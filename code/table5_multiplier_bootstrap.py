#!/usr/bin/env python3
"""Portable accelerated reproduction of Egger et al. (2022), Table V.

The estimator mirrors the public Stata multiplier construction with weighted
2SLS matrices and sublocation-cluster Rademacher wild-bootstrap signs.  It is
an accelerated Python reimplementation, not evidence that the original Stata
2,000-repetition loop completed.  On the audited inputs, the eleven Python
point estimates matched the supplied Stata intermediate to within 1.8e-7.

No record-level data are written.  The public privacy boundary is enforced:
``do/global_runGPS.do`` must set ``global runGPS = 0`` and must not enable the
restricted GPS path.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data" / "processed" / "HH_ENT_Multiplier_Dataset_ECMA.dta"
DEFAULT_ESTIMATES = REPO_ROOT / "data" / "processed" / "multiplier_estimates.dta"
DEFAULT_BENCHMARKS = REPO_ROOT / "config" / "published_benchmarks.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "tables"
DEFAULT_FIGURE_DIR = REPO_ROOT / "outputs" / "figures"
DEFAULT_RUN_GPS_CONFIG = REPO_ROOT / "do" / "global_runGPS.do"

FIRST_Q = 1
RANGE_NAME = "0to2"
QTRS = [225, 226, 227, 228, 229]
ENT_TYPES = [1, 2, 3]
DEFAULT_REPS = 2_000
DEFAULT_SEED = 12_345
DEFAULT_POINT_TOLERANCE = 1e-6

SUMMARY_NAME = "table5_2000_bootstrap_summary.csv"
VALIDATION_NAME = "table5_point_validation.csv"
COMPARISON_NAME = "table5_paper_comparison.csv"
DRAW_NAME = "table5_2000_bootstrap_draws.csv"
FIGURE_NAME = "table5_multiplier_comparison.png"

POINT_ORDER = [
    ("Panel A", "Expenditure multiplier", "multiplier_exp", True),
    ("Panel A", "Household non-durable expenditure", "nondurables_exp_wins", False),
    ("Panel A", "Household durable expenditure", "totval_hhassets_h_wins", False),
    ("Panel A", "Enterprise investment", "ent_inv_wins", False),
    ("Panel A", "Enterprise inventory", "ent_inventory_wins", False),
    ("Panel B", "Income multiplier", "multiplier_inc", True),
    ("Panel B", "Enterprise profits", "ent_profit2_wins", False),
    ("Panel B", "Household wage bill", "p3_3_wageearnings_wins", False),
    ("Panel B", "Enterprise capital income", "ent_rentcost_wins", False),
    ("Panel B", "Enterprise taxes paid", "ent_totaltaxes_wins", False),
    ("Panel C", "Average of both multipliers", "mean_mult", True),
]
POINT_KEYS = [variable for _, _, variable, _ in POINT_ORDER]


def qvars(prefix: str) -> list[str]:
    return [f"{prefix}_q{q}" for q in range(1, 11)]


def required_data_columns() -> set[str]:
    columns = {
        "eligible",
        "treat",
        "hi_sat",
        "hhweight_EL",
        "entweight_EL",
        "ent_type",
        "quarter",
        "sublocation_code",
        "pac_ownvill_r",
        f"pac_ov_{RANGE_NAME}km_r",
        f"pac_{RANGE_NAME}km_r",
        f"pac_{RANGE_NAME}km_r_eligible",
        f"pac_{RANGE_NAME}km_r_ineligible",
        f"share_ge_elig_treat_ov_{RANGE_NAME}km",
        f"share_ge_elig_treat_{RANGE_NAME}km_el",
        f"share_ge_elig_treat_{RANGE_NAME}km_in",
        "nondurables_exp_wins_r",
        "totval_hhassets_h_wins_r",
        "ent_inv_wins_r",
        "ent_inventory_wins_r",
        "p3_3_wageearnings_wins_r",
        "ent_profit2_wins_r",
        "ent_rentcost_wins_r",
        "ent_totaltaxes_wins_r",
    }
    for prefix in (
        "pac_ownvill_r",
        f"pac_ov_{RANGE_NAME}km_r",
        "t_share_actamt_ownvill_r",
        f"t_share_actamt_ov_{RANGE_NAME}km_r",
        f"pac_{RANGE_NAME}km_r_el",
        f"pac_{RANGE_NAME}km_r_in",
        f"t_shr_actamt_{RANGE_NAME}km_r_el",
        f"t_shr_actamt_{RANGE_NAME}km_r_in",
    ):
        columns.update(qvars(prefix))
    return columns


def required_estimate_columns() -> set[str]:
    return {
        "deflated",
        "withRarieda",
        "type",
        "quarter",
        "multiplier_exp",
        "nondurables_exp_wins",
        "totval_hhassets_h_wins",
        "ent_inv_wins",
        "ent_inventory_wins",
        "multiplier_inc",
        "ent_profit2_wins",
        "p3_3_wageearnings_wins",
        "ent_rentcost_wins",
        "ent_totaltaxes_wins",
    }


def stata_columns(path: Path) -> set[str]:
    with pd.read_stata(path, iterator=True, convert_categoricals=False) as reader:
        return set(reader.variable_labels())


def validate_run_gps(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing runGPS configuration: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    zero = re.compile(r"(?im)^\s*global\s+runGPS\s*(?:=\s*)?0(?:\s|$)")
    one = re.compile(r"(?im)^\s*global\s+runGPS\s*(?:=\s*)?1(?:\s|$)")
    if not zero.search(text) or one.search(text):
        raise ValueError("Privacy check failed: the public workflow must set runGPS = 0 only")


def validate_inputs(data_path: Path, estimates_path: Path, run_gps_config: Path) -> None:
    validate_run_gps(run_gps_config)
    for label, path in (("multiplier data", data_path), ("Stata point estimates", estimates_path)):
        if not path.is_file():
            raise FileNotFoundError(f"Missing {label}: {path}")
        if path.suffix.lower() != ".dta":
            raise ValueError(f"Expected a Stata .dta file for {label}: {path}")

    missing_data = sorted(required_data_columns() - stata_columns(data_path))
    if missing_data:
        preview = ", ".join(missing_data[:12])
        suffix = " ..." if len(missing_data) > 12 else ""
        raise ValueError(f"Multiplier data are missing {len(missing_data)} required variables: {preview}{suffix}")

    missing_estimates = sorted(required_estimate_columns() - stata_columns(estimates_path))
    if missing_estimates:
        raise ValueError(
            "Stata point-estimate file is missing required variables: " + ", ".join(missing_estimates)
        )


def wmean(df: pd.DataFrame, value: str, weight: str, mask: pd.Series) -> float:
    part = df.loc[mask & df[value].notna() & df[weight].notna(), [value, weight]]
    if part.empty or not np.isfinite(part[weight].to_numpy(float)).all() or (part[weight] <= 0).all():
        raise ValueError(f"Cannot calculate weighted mean for {value}")
    return float(np.average(part[value].to_numpy(float), weights=part[weight].to_numpy(float)))


def wsum(df: pd.DataFrame, weight: str, mask: pd.Series) -> float:
    return float(df.loc[mask & df[weight].notna(), weight].sum())


def quarter_dummies(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    cols = [(df["quarter"].to_numpy(float) == q).astype(float) for q in QTRS]
    return np.column_stack(cols), [f"quarter_{q}" for q in QTRS]


def quarter_by_binary(df: pd.DataFrame, var: str) -> tuple[np.ndarray, list[str]]:
    arrays: list[np.ndarray] = []
    names: list[str] = []
    base = df[var].to_numpy(float)
    quarter = df["quarter"].to_numpy(float)
    for qtr in QTRS:
        for level in (0, 1):
            arrays.append(((quarter == qtr) & (base == level)).astype(float))
            names.append(f"quarter_{qtr}#{var}_{level}")
    return np.column_stack(arrays), names


def quarter_by_ent_type(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    arrays: list[np.ndarray] = []
    names: list[str] = []
    quarter = df["quarter"].to_numpy(float)
    ent_type = df["ent_type"].to_numpy(float)
    for qtr in QTRS:
        for level in ENT_TYPES:
            arrays.append(((quarter == qtr) & (ent_type == level)).astype(float))
            names.append(f"quarter_{qtr}#ent_type_{level}")
    return np.column_stack(arrays), names


def ent_type_dummies(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    ent_type = df["ent_type"].to_numpy(float)
    return np.column_stack([(ent_type == 2).astype(float), (ent_type == 3).astype(float)]), [
        "ent_type_2",
        "ent_type_3",
    ]


def continuous(df: pd.DataFrame, names: list[str]) -> tuple[np.ndarray, list[str]]:
    return df[names].to_numpy(float), names


def interact_ent(df: pd.DataFrame, names: list[str]) -> tuple[np.ndarray, list[str]]:
    arrays: list[np.ndarray] = []
    output_names: list[str] = []
    ent_type = df["ent_type"].to_numpy(float)
    for name in names:
        values = df[name].to_numpy(float)
        for level in ENT_TYPES:
            arrays.append(values * (ent_type == level))
            output_names.append(f"ent_type_{level}#{name}")
    return np.column_stack(arrays), output_names


def add_constant(n: int) -> tuple[np.ndarray, list[str]]:
    return np.ones((n, 1)), ["_cons"]


def hstack(parts: Iterable[tuple[np.ndarray, list[str]]]) -> tuple[np.ndarray, list[str]]:
    parts = list(parts)
    arrays = [array for array, _ in parts if array.size]
    names = [name for _, part_names in parts for name in part_names]
    return (np.column_stack(arrays), names) if arrays else (np.empty((0, 0)), [])


@dataclass
class IVModel:
    y_name: str
    x_names: list[str]
    x: np.ndarray
    weights: np.ndarray
    sample: np.ndarray
    beta_map: np.ndarray
    beta: np.ndarray
    fitted: np.ndarray
    resid: np.ndarray

    @classmethod
    def fit(
        cls,
        df: pd.DataFrame,
        y_name: str,
        endog: tuple[np.ndarray, list[str]],
        instr: tuple[np.ndarray, list[str]],
        exog: tuple[np.ndarray, list[str]],
        weight_name: str,
        base_mask: pd.Series,
    ) -> "IVModel":
        y_all = df[y_name].to_numpy(float)
        w_all = df[weight_name].to_numpy(float)
        x_all, x_names = hstack([endog, exog])
        z_all, _ = hstack([instr, exog])
        valid = (
            base_mask.to_numpy(bool)
            & np.isfinite(y_all)
            & np.isfinite(w_all)
            & (w_all > 0)
            & np.isfinite(x_all).all(axis=1)
            & np.isfinite(z_all).all(axis=1)
        )
        if not valid.any():
            raise ValueError(f"No valid observations for {y_name}")
        y = y_all[valid]
        x = x_all[valid]
        z = z_all[valid]
        weights = w_all[valid]
        sqrtw = np.sqrt(weights)
        zw = z * sqrtw[:, None]
        xw = x * sqrtw[:, None]
        gamma = np.linalg.pinv(zw, rcond=1e-12) @ xw
        xhat = z @ gamma
        xhatw = xhat * sqrtw[:, None]
        beta_map = np.linalg.pinv(xhatw, rcond=1e-12) * sqrtw[None, :]
        beta = beta_map @ y
        fitted = x @ beta
        return cls(y_name, x_names, x, weights, valid, beta_map, beta, fitted, y - fitted)

    def bootstrap_beta(self, row_signs: np.ndarray) -> np.ndarray:
        y_star = self.fitted + self.resid * row_signs[self.sample]
        return self.beta_map @ y_star

    def lincom(self, lincom_weights: dict[str, float], beta: np.ndarray | None = None) -> float:
        selected_beta = self.beta if beta is None else beta
        index = {name: i for i, name in enumerate(self.x_names)}
        return float(
            sum(weight * selected_beta[index[name]] for name, weight in lincom_weights.items() if name in index)
        )


def hh_flow_weights_treated(amount_own: float, amount_other: float) -> dict[str, float]:
    weights: dict[str, float] = {}
    for q in range(FIRST_Q, 11):
        terms = [(q, 47 / 87)] if q < 3 else [(q, 47 / 87), (q - 2, 40 / 87)]
        for q_term, factor in terms:
            own = f"pac_ownvill_r_q{q_term}"
            other = f"pac_ov_{RANGE_NAME}km_r_q{q_term}"
            weights[own] = weights.get(own, 0.0) + amount_own * factor
            weights[other] = weights.get(other, 0.0) + amount_other * factor
    return weights


def hh_flow_weights_untreated(
    eligible_amount: float,
    ineligible_amount: float,
    eligible_weight: float,
    ineligible_weight: float,
) -> dict[str, float]:
    weights: dict[str, float] = {}
    for q in range(FIRST_Q, 11):
        terms = [(q, 47 / 87)] if q < 3 else [(q, 47 / 87), (q - 2, 40 / 87)]
        for q_term, factor in terms:
            eligible = f"pac_{RANGE_NAME}km_r_el_q{q_term}"
            ineligible = f"pac_{RANGE_NAME}km_r_in_q{q_term}"
            weights[eligible] = weights.get(eligible, 0.0) + eligible_amount * eligible_weight * factor
            weights[ineligible] = weights.get(ineligible, 0.0) + ineligible_amount * ineligible_weight * factor
    return weights


def hh_stock_weights_treated(amount_own: float, amount_other: float) -> dict[str, float]:
    return {"pac_ownvill_r": amount_own, f"pac_ov_{RANGE_NAME}km_r": amount_other}


def hh_stock_weights_untreated(
    eligible_amount: float,
    ineligible_amount: float,
    eligible_weight: float,
    ineligible_weight: float,
) -> dict[str, float]:
    return {
        f"pac_{RANGE_NAME}km_r_eligible": eligible_amount * eligible_weight,
        f"pac_{RANGE_NAME}km_r_ineligible": ineligible_amount * ineligible_weight,
    }


def ent_flow_weights(side: str, amounts: dict[int, float], scale: dict[int, float]) -> dict[str, float]:
    weights: dict[str, float] = {}
    base = "pac_ownvill_r" if side == "own" else f"pac_ov_{RANGE_NAME}km_r"
    for q in range(FIRST_Q, 11):
        terms = [(q, 47 / 87)] if q < 3 else [(q, 47 / 87), (q - 2, 40 / 87)]
        for q_term, factor in terms:
            for ent_type, amount in amounts.items():
                name = f"ent_type_{ent_type}#{base}_q{q_term}"
                weights[name] = weights.get(name, 0.0) + amount * scale[ent_type] * factor
    return weights


def ent_stock_weights(side: str, amounts: dict[int, float], scale: dict[int, float]) -> dict[str, float]:
    base = "pac_ownvill_r" if side == "own" else f"pac_ov_{RANGE_NAME}km_r"
    return {f"ent_type_{ent_type}#{base}": amount * scale[ent_type] for ent_type, amount in amounts.items()}


def merge_weights(*dicts: dict[str, float], scale: float = 1.0) -> dict[str, float]:
    output: dict[str, float] = {}
    for weights in dicts:
        for key, value in weights.items():
            output[key] = output.get(key, 0.0) + value * scale
    return output


def constants(df: pd.DataFrame) -> dict[str, object]:
    treated_eligible = (df["eligible"] == 1) & (df["treat"] == 1)
    control_eligible = (df["eligible"] == 1) & (df["treat"] == 0)
    ineligible = df["eligible"] == 0
    untreated = ineligible | (df["treat"] == 0)
    treated = df["treat"] == 1
    control = df["treat"] == 0
    low_saturation_control = (df["hi_sat"] == 0) & control

    eligible_sum = wsum(df, "hhweight_EL", control_eligible)
    ineligible_sum = wsum(df, "hhweight_EL", ineligible)
    output: dict[str, object] = {
        "eligcontrolweight": eligible_sum / (eligible_sum + ineligible_sum),
        "ineligweight": ineligible_sum / (eligible_sum + ineligible_sum),
        "n_hh_treatall": wsum(df, "hhweight_EL", treated),
        "n_hh_controlall": wsum(df, "hhweight_EL", control),
        "n_hh_lowsatcontrol": wsum(df, "hhweight_EL", low_saturation_control),
        "n_hh_treat": wsum(df, "hhweight_EL", treated_eligible),
        "n_hh_untreat": wsum(df, "hhweight_EL", untreated),
        "eligtreat_amt_ownvill": wmean(df, "pac_ownvill_r", "hhweight_EL", treated_eligible),
        "eligtreat_amt_ov": wmean(df, f"pac_ov_{RANGE_NAME}km_r", "hhweight_EL", treated_eligible),
        "eligcontrol_amt": wmean(df, f"pac_{RANGE_NAME}km_r", "hhweight_EL", control_eligible),
        "inelig_amt": wmean(df, f"pac_{RANGE_NAME}km_r", "hhweight_EL", ineligible),
    }
    output["untreatweight"] = float(output["n_hh_untreat"]) / float(output["n_hh_treat"])

    for ent_type, label in ((2, "from_hh"), (1, "outside_hh"), (3, "ownfarm")):
        ent = df["ent_type"] == ent_type
        output[f"n_ent_{label}_treatall"] = wsum(df, "entweight_EL", ent & treated)
        output[f"n_ent_{label}_control"] = wsum(df, "entweight_EL", ent & control)
        output[f"n_ent_{label}_lowsatcontrol"] = wsum(df, "entweight_EL", ent & low_saturation_control)
        output[f"n_ent_{label}_tot"] = wsum(df, "entweight_EL", ent)

    treated_own: dict[int, float] = {}
    treated_other: dict[int, float] = {}
    control_other: dict[int, float] = {}
    for ent_type in ENT_TYPES:
        ent = df["ent_type"] == ent_type
        treated_own[ent_type] = wmean(df, "pac_ownvill_r", "entweight_EL", ent & treated)
        treated_other[ent_type] = wmean(df, f"pac_ov_{RANGE_NAME}km_r", "entweight_EL", ent & treated)
        control_other[ent_type] = wmean(df, f"pac_ov_{RANGE_NAME}km_r", "entweight_EL", ent & control)
    output["treat_amounts_own"] = treated_own
    output["treat_amounts_ov"] = treated_other
    output["control_amounts_ov"] = control_other
    return output


def build_models(df: pd.DataFrame) -> tuple[dict[str, IVModel], dict[str, dict[str, float]]]:
    c = constants(df)
    models: dict[str, IVModel] = {}
    lincom_weights: dict[str, dict[str, float]] = {}
    eligible = df["eligible"] == 1
    untreated = (df["eligible"] == 0) | (df["treat"] == 0)
    all_rows = pd.Series(True, index=df.index)

    for outcome in ("nondurables_exp_wins_r", "p3_3_wageearnings_wins_r"):
        models[f"{outcome}:treated"] = IVModel.fit(
            df,
            outcome,
            continuous(df, qvars("pac_ownvill_r") + qvars(f"pac_ov_{RANGE_NAME}km_r")),
            continuous(df, qvars("t_share_actamt_ownvill_r") + qvars(f"t_share_actamt_ov_{RANGE_NAME}km_r")),
            quarter_dummies(df),
            "hhweight_EL",
            eligible,
        )
        models[f"{outcome}:untreated"] = IVModel.fit(
            df,
            outcome,
            continuous(df, qvars(f"pac_{RANGE_NAME}km_r_el") + qvars(f"pac_{RANGE_NAME}km_r_in")),
            continuous(
                df,
                qvars(f"t_shr_actamt_{RANGE_NAME}km_r_el") + qvars(f"t_shr_actamt_{RANGE_NAME}km_r_in"),
            ),
            quarter_by_binary(df, "eligible"),
            "hhweight_EL",
            untreated,
        )
        lincom_weights[f"{outcome}:treated"] = hh_flow_weights_treated(
            float(c["eligtreat_amt_ownvill"]), float(c["eligtreat_amt_ov"])
        )
        lincom_weights[f"{outcome}:untreated"] = merge_weights(
            hh_flow_weights_untreated(
                float(c["eligcontrol_amt"]),
                float(c["inelig_amt"]),
                float(c["eligcontrolweight"]),
                float(c["ineligweight"]),
            ),
            scale=float(c["untreatweight"]),
        )

    household_stock = "totval_hhassets_h_wins_r"
    models[f"{household_stock}:treated"] = IVModel.fit(
        df,
        household_stock,
        continuous(df, ["pac_ownvill_r", f"pac_ov_{RANGE_NAME}km_r"]),
        continuous(df, ["treat", f"share_ge_elig_treat_ov_{RANGE_NAME}km"]),
        add_constant(len(df)),
        "hhweight_EL",
        eligible,
    )
    models[f"{household_stock}:untreated"] = IVModel.fit(
        df,
        household_stock,
        continuous(df, [f"pac_{RANGE_NAME}km_r_eligible", f"pac_{RANGE_NAME}km_r_ineligible"]),
        continuous(df, [f"share_ge_elig_treat_{RANGE_NAME}km_el", f"share_ge_elig_treat_{RANGE_NAME}km_in"]),
        hstack([add_constant(len(df)), continuous(df, ["eligible"])]),
        "hhweight_EL",
        untreated,
    )
    lincom_weights[f"{household_stock}:treated"] = hh_stock_weights_treated(
        float(c["eligtreat_amt_ownvill"]), float(c["eligtreat_amt_ov"])
    )
    lincom_weights[f"{household_stock}:untreated"] = merge_weights(
        hh_stock_weights_untreated(
            float(c["eligcontrol_amt"]),
            float(c["inelig_amt"]),
            float(c["eligcontrolweight"]),
            float(c["ineligweight"]),
        ),
        scale=float(c["untreatweight"]),
    )

    enterprise_flows = ("ent_inv_wins_r", "ent_profit2_wins_r", "ent_rentcost_wins_r", "ent_totaltaxes_wins_r")
    total_scale = {
        1: float(c["n_ent_outside_hh_treatall"]) / float(c["n_hh_treatall"]),
        2: float(c["n_ent_from_hh_treatall"]) / float(c["n_hh_treatall"]),
        3: float(c["n_ent_ownfarm_treatall"]) / float(c["n_hh_treatall"]),
    }
    spill_scale = {
        1: float(c["n_ent_outside_hh_control"]) / float(c["n_hh_controlall"]),
        2: float(c["n_ent_from_hh_control"]) / float(c["n_hh_controlall"]),
        3: float(c["n_ent_ownfarm_control"]) / float(c["n_hh_controlall"]),
    }
    total_final = float(c["n_hh_treatall"]) / float(c["n_hh_treat"])
    spill_final = float(c["n_hh_controlall"]) / float(c["n_hh_treat"])

    for outcome in enterprise_flows:
        models[f"{outcome}:enterprise"] = IVModel.fit(
            df,
            outcome,
            interact_ent(df, qvars("pac_ownvill_r") + qvars(f"pac_ov_{RANGE_NAME}km_r")),
            interact_ent(
                df, qvars("t_share_actamt_ownvill_r") + qvars(f"t_share_actamt_ov_{RANGE_NAME}km_r")
            ),
            hstack([add_constant(len(df)), quarter_by_ent_type(df)]),
            "entweight_EL",
            all_rows,
        )
        lincom_weights[f"{outcome}:enterprise"] = merge_weights(
            merge_weights(
                ent_flow_weights("own", c["treat_amounts_own"], total_scale),
                ent_flow_weights("other", c["treat_amounts_ov"], total_scale),
                scale=total_final,
            ),
            merge_weights(ent_flow_weights("other", c["control_amounts_ov"], spill_scale), scale=spill_final),
        )

    enterprise_stock = "ent_inventory_wins_r"
    models[f"{enterprise_stock}:enterprise"] = IVModel.fit(
        df,
        enterprise_stock,
        interact_ent(df, ["pac_ownvill_r", f"pac_ov_{RANGE_NAME}km_r"]),
        interact_ent(df, ["treat", f"share_ge_elig_treat_ov_{RANGE_NAME}km"]),
        hstack([add_constant(len(df)), ent_type_dummies(df)]),
        "entweight_EL",
        all_rows,
    )
    lincom_weights[f"{enterprise_stock}:enterprise"] = merge_weights(
        merge_weights(
            ent_stock_weights("own", c["treat_amounts_own"], total_scale),
            ent_stock_weights("other", c["treat_amounts_ov"], total_scale),
            scale=total_final,
        ),
        merge_weights(ent_stock_weights("other", c["control_amounts_ov"], spill_scale), scale=spill_final),
    )
    return models, lincom_weights


def component_values(
    models: dict[str, IVModel],
    lincom_weights: dict[str, dict[str, float]],
    betas: dict[str, np.ndarray] | None = None,
) -> dict[str, float]:
    def value(key: str) -> float:
        return models[key].lincom(lincom_weights[key], None if betas is None else betas[key])

    nondurables = value("nondurables_exp_wins_r:treated") + value("nondurables_exp_wins_r:untreated")
    durables = value("totval_hhassets_h_wins_r:treated") + value("totval_hhassets_h_wins_r:untreated")
    enterprise_investment = value("ent_inv_wins_r:enterprise")
    inventory = value("ent_inventory_wins_r:enterprise")
    wage = value("p3_3_wageearnings_wins_r:treated") + value("p3_3_wageearnings_wins_r:untreated")
    profits = value("ent_profit2_wins_r:enterprise")
    rent = value("ent_rentcost_wins_r:enterprise")
    taxes = value("ent_totaltaxes_wins_r:enterprise")
    expenditure = nondurables + durables + enterprise_investment + inventory
    income = wage + profits + rent + taxes
    return {
        "multiplier_exp": expenditure,
        "nondurables_exp_wins": nondurables,
        "totval_hhassets_h_wins": durables,
        "ent_inv_wins": enterprise_investment,
        "ent_inventory_wins": inventory,
        "multiplier_inc": income,
        "ent_profit2_wins": profits,
        "p3_3_wageearnings_wins": wage,
        "ent_rentcost_wins": rent,
        "ent_totaltaxes_wins": taxes,
        "mean_mult": (expenditure + income) / 2,
    }


def stata_targets(estimates_path: Path) -> dict[str, float]:
    estimates = pd.read_stata(estimates_path)
    mask = (
        (estimates["deflated"] == 1)
        & (estimates["withRarieda"] == 0)
        & (estimates["type"].astype(str) == "joint")
        & (estimates["quarter"] == 99)
    )
    selected = estimates.loc[mask]
    if len(selected) != 1:
        raise ValueError(f"Expected exactly one main Table V point-estimate row; found {len(selected)}")
    row = selected.iloc[0]
    targets = {key: float(row[key]) for key in POINT_KEYS if key != "mean_mult"}
    targets["mean_mult"] = float((row["multiplier_exp"] + row["multiplier_inc"]) / 2)
    return targets


def point_validation(point: dict[str, float], targets: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "row": key,
                "python_point": point[key],
                "stata_point": targets[key],
                "difference": point[key] - targets[key],
            }
            for key in POINT_KEYS
        ]
    )


def bootstrap(
    models: dict[str, IVModel],
    lincom_weights: dict[str, dict[str, float]],
    df: pd.DataFrame,
    reps: int,
    seed: int,
) -> pd.DataFrame:
    if reps < 2:
        raise ValueError("At least two bootstrap replications are required")
    rng = np.random.default_rng(seed)
    clusters = df["sublocation_code"].to_numpy(float)
    unique_clusters = np.array(sorted(pd.unique(df["sublocation_code"].dropna())))
    cluster_to_pos = {cluster: position for position, cluster in enumerate(unique_clusters)}
    cluster_index = np.array([cluster_to_pos.get(cluster, -1) for cluster in clusters])
    if (cluster_index < 0).any():
        raise ValueError("Missing sublocation_code in bootstrap data")

    # Literal public-Stata-code compatibility: this untreated household-stock
    # coefficient is left fixed because the bootstrap outcome is generated but
    # the original outcome is passed to ivreg2 in that leg.
    fixed_keys = {"totval_hhassets_h_wins_r:untreated"}
    rows: list[dict[str, float]] = []
    for _ in range(reps):
        cluster_signs = rng.choice(np.array([-1.0, 1.0]), size=len(unique_clusters))
        row_signs = cluster_signs[cluster_index]
        betas = {
            key: models[key].beta if key in fixed_keys else models[key].bootstrap_beta(row_signs)
            for key in models
        }
        rows.append(component_values(models, lincom_weights, betas))
    return pd.DataFrame(rows)


def summarize(draws: pd.DataFrame, targets: dict[str, float], reps: int, seed: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for panel, label, variable, test_one in POINT_ORDER:
        rows.append(
            {
                "panel": panel,
                "row": label,
                "estimate": targets[variable],
                "se": float(draws[variable].std(ddof=1)),
                "p_m_lt_0": float((draws[variable] < 0).mean()),
                "p_m_lt_1": float((draws[variable] < 1).mean()) if test_one else math.nan,
            }
        )
    rows.append(
        {
            "panel": "Panel C",
            "row": "Joint test of both multipliers",
            "estimate": math.nan,
            "se": math.nan,
            "p_m_lt_0": float(
                ((draws["multiplier_exp"] < 0) & (draws["multiplier_inc"] < 0)).mean()
            ),
            "p_m_lt_1": float(
                ((draws["multiplier_exp"] < 1) & (draws["multiplier_inc"] < 1)).mean()
            ),
        }
    )
    return pd.DataFrame(rows)


def load_benchmarks(path: Path) -> pd.DataFrame:
    required = {
        "panel",
        "row",
        "published_estimate",
        "published_se",
        "published_p_m_lt_0",
        "published_p_m_lt_1",
        "source",
    }
    if not path.is_file():
        raise FileNotFoundError(f"Missing published benchmark table: {path}")
    benchmarks = pd.read_csv(path)
    missing = sorted(required - set(benchmarks.columns))
    if missing:
        raise ValueError("Published benchmark table is missing columns: " + ", ".join(missing))
    if benchmarks.duplicated(["panel", "row"]).any():
        raise ValueError("Published benchmark table has duplicate panel/row keys")
    return benchmarks


def compare_with_paper(summary: pd.DataFrame, benchmarks: pd.DataFrame) -> pd.DataFrame:
    ordered_benchmarks = benchmarks.copy()
    ordered_benchmarks["_benchmark_order"] = np.arange(len(ordered_benchmarks))
    comparison = ordered_benchmarks.merge(
        summary,
        on=["panel", "row"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if not (comparison["_merge"] == "both").all():
        unmatched = comparison.loc[comparison["_merge"] != "both", ["panel", "row", "_merge"]]
        raise ValueError("Benchmark and reproduced rows do not align:\n" + unmatched.to_string(index=False))
    comparison["replicated_estimate"] = comparison["estimate"]
    comparison["absolute_difference"] = (
        comparison["published_estimate"] - comparison["replicated_estimate"]
    ).abs()
    comparison["replicated_se"] = comparison["se"]
    comparison["se_difference"] = comparison["replicated_se"] - comparison["published_se"]
    comparison["replicated_p_m_lt_0"] = comparison["p_m_lt_0"]
    comparison["replicated_p_m_lt_1"] = comparison["p_m_lt_1"]
    comparison = comparison.sort_values("_benchmark_order", kind="stable")
    return comparison[
        [
            "row",
            "published_estimate",
            "replicated_estimate",
            "absolute_difference",
            "published_se",
            "replicated_se",
            "se_difference",
            "published_p_m_lt_0",
            "replicated_p_m_lt_0",
            "published_p_m_lt_1",
            "replicated_p_m_lt_1",
        ]
    ]


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", dir=path.parent, delete=False, encoding="utf-8") as handle:
        temporary = Path(handle.name)
        frame.to_csv(handle, index=False, quoting=csv.QUOTE_MINIMAL)
    temporary.replace(path)


def render_comparison_figure(comparison: pd.DataFrame, path: Path, reps: int, seed: int) -> None:
    """Use the same print-ready renderer as the aggregate-only figure command."""
    from render_figures import render_table5_comparison

    render_table5_comparison(comparison, path, f"{reps:,}-draw reimplementation")


@dataclass(frozen=True)
class RunResult:
    summary_path: Path
    validation_path: Path
    comparison_path: Path
    figure_path: Path
    draws_path: Path | None
    max_point_difference: float


def run_table5(
    *,
    data_path: Path,
    estimates_path: Path,
    benchmarks_path: Path,
    output_dir: Path,
    figure_dir: Path,
    run_gps_config: Path,
    reps: int = DEFAULT_REPS,
    seed: int = DEFAULT_SEED,
    point_tolerance: float = DEFAULT_POINT_TOLERANCE,
    write_draws: bool = False,
) -> RunResult:
    validate_inputs(data_path, estimates_path, run_gps_config)
    benchmarks = load_benchmarks(benchmarks_path)
    data = pd.read_stata(data_path)
    models, lincom_weights = build_models(data)
    python_point = component_values(models, lincom_weights)
    targets = stata_targets(estimates_path)
    validation = point_validation(python_point, targets)
    max_difference = float(validation["difference"].abs().max())
    if max_difference > point_tolerance:
        raise ValueError(
            f"Python/Stata point-estimate validation failed: {max_difference:.9g} exceeds {point_tolerance:.9g}"
        )

    draws = bootstrap(models, lincom_weights, data, reps, seed)
    summary = summarize(draws, targets, reps, seed)
    comparison = compare_with_paper(summary, benchmarks)

    summary_path = output_dir / SUMMARY_NAME
    validation_path = output_dir / VALIDATION_NAME
    comparison_path = output_dir / COMPARISON_NAME
    figure_path = figure_dir / FIGURE_NAME
    atomic_csv(summary, summary_path)
    atomic_csv(validation, validation_path)
    atomic_csv(comparison, comparison_path)
    render_comparison_figure(comparison, figure_path, reps, seed)
    draws_path: Path | None = None
    if write_draws:
        draws_path = output_dir / DRAW_NAME
        atomic_csv(draws, draws_path)

    return RunResult(
        summary_path,
        validation_path,
        comparison_path,
        figure_path,
        draws_path,
        max_difference,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Prepared multiplier analysis .dta")
    parser.add_argument("--estimates", type=Path, default=DEFAULT_ESTIMATES, help="Stata multiplier_estimates.dta")
    parser.add_argument("--benchmarks", type=Path, default=DEFAULT_BENCHMARKS, help="Published Table V benchmarks CSV")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for aggregate CSV tables")
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR, help="Directory for the comparison figure")
    parser.add_argument("--run-gps-config", type=Path, default=DEFAULT_RUN_GPS_CONFIG)
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--point-tolerance", type=float, default=DEFAULT_POINT_TOLERANCE)
    parser.add_argument("--check-only", action="store_true", help="Validate paths, schemas, benchmarks, and runGPS=0; write nothing")
    parser.add_argument("--validate-only", action="store_true", help="Also calculate and validate point estimates; skip bootstrap and writes")
    parser.add_argument("--write-draws", action="store_true", help="Also write aggregate bootstrap draws")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    validate_inputs(args.data, args.estimates, args.run_gps_config)
    load_benchmarks(args.benchmarks)
    if args.check_only:
        print("Table V preflight passed: inputs and schemas present; runGPS=0; no outputs written.")
        return 0

    if args.validate_only:
        data = pd.read_stata(args.data)
        models, weights = build_models(data)
        validation = point_validation(component_values(models, weights), stata_targets(args.estimates))
        max_difference = float(validation["difference"].abs().max())
        print(validation.to_string(index=False))
        print(f"Max absolute Python/Stata point-estimate difference: {max_difference:.9g}")
        if max_difference > args.point_tolerance:
            raise ValueError(f"Point validation exceeds tolerance {args.point_tolerance:.9g}")
        return 0

    result = run_table5(
        data_path=args.data,
        estimates_path=args.estimates,
        benchmarks_path=args.benchmarks,
        output_dir=args.output_dir,
        figure_dir=args.figure_dir,
        run_gps_config=args.run_gps_config,
        reps=args.reps,
        seed=args.seed,
        point_tolerance=args.point_tolerance,
        write_draws=args.write_draws,
    )
    print(f"Table V accelerated bootstrap completed ({args.reps:,} draws; seed {args.seed}; runGPS=0).")
    print(f"Max absolute Python/Stata point-estimate difference: {result.max_point_difference:.9g}")
    for path in (result.summary_path, result.validation_path, result.comparison_path, result.figure_path):
        print(path)
    if result.draws_path is not None:
        print(result.draws_path)
    print("Claim boundary: accelerated Python reimplementation; not a completed direct Stata 2,000-draw run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
