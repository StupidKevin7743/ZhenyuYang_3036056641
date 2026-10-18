#!/usr/bin/env python3
"""Run the course project's rollout-timing and exposure-network extension.

The extension is deliberately limited to aggregate design diagnostics.  It does
not estimate a new treatment effect and never writes village or household
identifiers.  Inputs are supplied explicitly so the public repository contains
neither data nor machine-local paths.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


RADII_KM = (2, 3, 4)
CELL_ORDER = ("direct only", "direct+indirect", "pure control", "spillover only")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing", type=Path, required=True)
    parser.add_argument("--household", type=Path, required=True)
    parser.add_argument("--village", type=Path, required=True)
    parser.add_argument("--treatment-status", type=Path, required=True)
    parser.add_argument("--village-buffer", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--figure-dir", type=Path, required=True)
    return parser.parse_args()


def _require_files(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required input file(s) missing: " + ", ".join(missing))


def _month_index(series: pd.Series) -> pd.Series:
    origin_year, origin_month = 2014, 9
    dates = pd.to_datetime(series, errors="coerce")
    return (dates.dt.year - origin_year) * 12 + (dates.dt.month - origin_month)


def _cluster_ols(
    frame: pd.DataFrame,
    dependent: str,
    regressors: list[str],
    cluster: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, int]:
    """OLS with the standard finite-sample corrected cluster sandwich."""
    columns = [dependent, cluster, *regressors]
    data = frame[columns].replace([np.inf, -np.inf], np.nan).dropna().copy()
    y = data[dependent].to_numpy(dtype=float)
    x = np.column_stack(
        [np.ones(len(data), dtype=float)]
        + [data[name].to_numpy(dtype=float) for name in regressors]
    )
    n, k = x.shape
    clusters = data[cluster].astype(str).to_numpy()
    unique_clusters = np.unique(clusters)
    g = len(unique_clusters)
    if n <= k or g <= 1:
        raise ValueError("Not enough observations or clusters for clustered OLS")

    xtx_inv = np.linalg.pinv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    residual = y - x @ beta
    meat = np.zeros((k, k), dtype=float)
    for label in unique_clusters:
        mask = clusters == label
        score = x[mask].T @ residual[mask]
        meat += np.outer(score, score)
    correction = (g / (g - 1)) * ((n - 1) / (n - k))
    covariance = correction * (xtx_inv @ meat @ xtx_inv)
    standard_errors = np.sqrt(np.clip(np.diag(covariance), 0, None))
    z_scores = np.divide(
        beta,
        standard_errors,
        out=np.full_like(beta, np.nan),
        where=standard_errors > 0,
    )
    p_values = np.array(
        [math.erfc(abs(float(z)) / math.sqrt(2)) if np.isfinite(z) else np.nan for z in z_scores]
    )
    return beta, standard_errors, p_values, n, g


def compute_timing_regression(
    timing_path: Path,
    household_path: Path,
    treatment_status_path: Path,
) -> pd.DataFrame:
    household = pd.read_stata(
        household_path,
        convert_categoricals=False,
        columns=["village_code", "hhweight_EL", "eligible"],
    )
    household["eligible_weight"] = household["hhweight_EL"] * (household["eligible"] == 1)
    village_covariates = (
        household.groupby("village_code", as_index=False)
        .agg(
            weighted_households=("hhweight_EL", "sum"),
            weighted_eligible_households=("eligible_weight", "sum"),
        )
    )
    village_covariates["eligible_share"] = (
        village_covariates["weighted_eligible_households"]
        / village_covariates["weighted_households"]
    )
    village_covariates["log_weighted_households"] = np.log(
        village_covariates["weighted_households"]
    )

    status = pd.read_stata(
        treatment_status_path,
        convert_categoricals=False,
        columns=["village_code", "sublocation_code", "subcounty", "hi_sat", "treat"],
    ).drop_duplicates("village_code")
    timing = pd.read_stata(
        timing_path,
        convert_categoricals=False,
        columns=["village_code", "act_start", "act_start_c"],
    ).drop_duplicates("village_code")
    frame = timing.merge(village_covariates, on="village_code").merge(status, on="village_code")
    frame = frame[frame["treat"] == 1].copy()
    frame["actual_start_month"] = _month_index(frame["act_start"])
    frame["actual_start_month_10pct"] = _month_index(frame["act_start_c"])

    subcounty = frame["subcounty"].astype(str).str.strip().str.upper()
    frame["subcounty_ugunja"] = (subcounty == "UGUNJA").astype(float)
    frame["subcounty_ukwala"] = (subcounty == "UKWALA").astype(float)
    regressors = [
        "log_weighted_households",
        "eligible_share",
        "hi_sat",
        "subcounty_ugunja",
        "subcounty_ukwala",
    ]
    labels = [
        "log weighted village households",
        "eligible share",
        "high saturation",
        "Ugunja FE",
        "Ukwala FE",
    ]

    rows: list[dict[str, object]] = []
    for dependent, model_name in (
        ("actual_start_month", "Actual start month"),
        ("actual_start_month_10pct", "Actual start month (10 pct cutoff)"),
    ):
        beta, standard_errors, p_values, n, clusters = _cluster_ols(
            frame, dependent, regressors, "sublocation_code"
        )
        for index, label in enumerate(labels, start=1):
            rows.append(
                {
                    "model": model_name,
                    "variable": label,
                    "coefficient": float(beta[index]),
                    "standard_error": float(standard_errors[index]),
                    "p_value": float(p_values[index]),
                    "n": n,
                    "clusters": clusters,
                    "covariance": "sublocation-clustered",
                }
            )
    return pd.DataFrame(rows)


def compute_exposure_tables(
    household_path: Path,
    village_path: Path,
    buffer_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    buffers = pd.read_stata(buffer_path, convert_categoricals=False)
    buffers = buffers[buffers["treatvill_code"] != buffers["village_code"]].copy()
    village_status = pd.read_stata(
        village_path,
        convert_categoricals=False,
        columns=["village_code", "treat"],
    ).drop_duplicates("village_code")
    household_weights = (
        pd.read_stata(
            household_path,
            convert_categoricals=False,
            columns=["village_code", "hhweight_EL", "eligible"],
        )
        .groupby(["village_code", "eligible"], as_index=False)["hhweight_EL"]
        .sum()
    )

    summary_rows: list[dict[str, object]] = []
    cell_rows: list[dict[str, object]] = []
    household_rows: list[dict[str, object]] = []
    for radius in RADII_KM:
        nearby = buffers[buffers["distance"] <= radius].copy()
        grouped = (
            nearby.groupby("treatvill_code")
            .agg(
                nearby_villages=("village_code", "nunique"),
                nearby_treated_villages=(
                    "village_code",
                    lambda values: nearby.loc[values.index]
                    .loc[nearby.loc[values.index, "treat"] == 1, "village_code"]
                    .nunique(),
                ),
            )
            .rename_axis("village_code")
            .reset_index()
        )
        grouped = village_status.merge(grouped, on="village_code", how="left").fillna(
            {"nearby_villages": 0, "nearby_treated_villages": 0}
        )
        grouped["nearby_villages"] = grouped["nearby_villages"].astype(int)
        grouped["nearby_treated_villages"] = grouped["nearby_treated_villages"].astype(int)
        has_treated_neighbor = grouped["nearby_treated_villages"] > 0
        grouped["cell"] = np.select(
            [
                (grouped["treat"] == 1) & has_treated_neighbor,
                (grouped["treat"] == 1) & ~has_treated_neighbor,
                (grouped["treat"] == 0) & has_treated_neighbor,
                (grouped["treat"] == 0) & ~has_treated_neighbor,
            ],
            ["direct+indirect", "direct only", "spillover only", "pure control"],
            default="other",
        )

        summary_rows.append(
            {
                "radius_km": radius,
                "villages_with_0_neighbors": int((grouped["nearby_villages"] == 0).sum()),
                "mean_nearby_villages": float(grouped["nearby_villages"].mean()),
                "median_nearby_villages": float(grouped["nearby_villages"].median()),
                "max_nearby_villages": int(grouped["nearby_villages"].max()),
                "villages_with_0_treated_neighbors": int(
                    (grouped["nearby_treated_villages"] == 0).sum()
                ),
                "villages_with_1_treated_neighbor": int(
                    (grouped["nearby_treated_villages"] == 1).sum()
                ),
                "villages_with_2_treated_neighbors": int(
                    (grouped["nearby_treated_villages"] == 2).sum()
                ),
                "villages_with_3plus_treated_neighbors": int(
                    (grouped["nearby_treated_villages"] >= 3).sum()
                ),
            }
        )
        counts = grouped.groupby("cell", as_index=False).size()
        for row in counts.itertuples(index=False):
            cell_rows.append(
                {"radius_km": radius, "cell": row.cell, "village_count": int(row.size)}
            )

        merged = household_weights.merge(
            grouped[["village_code", "cell"]], on="village_code", how="left"
        )
        aggregate = (
            merged.groupby(["cell", "eligible"], as_index=False)["hhweight_EL"]
            .sum()
            .rename(columns={"hhweight_EL": "weighted_households"})
        )
        for row in aggregate.itertuples(index=False):
            household_rows.append(
                {
                    "radius_km": radius,
                    "cell": row.cell,
                    "eligible": int(row.eligible),
                    "weighted_households": float(row.weighted_households),
                }
            )

    cells = pd.DataFrame(cell_rows).sort_values(["radius_km", "cell"]).reset_index(drop=True)
    households = (
        pd.DataFrame(household_rows)
        .sort_values(["radius_km", "cell", "eligible"])
        .reset_index(drop=True)
    )
    summary = pd.DataFrame(summary_rows)
    return cells, households, summary


def write_exposure_figure(cells: pd.DataFrame, output_path: Path) -> None:
    """Create a compact stacked-bar PNG without exposing any identifiers."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:  # pragma: no cover - environment-specific message
        raise RuntimeError("matplotlib is required to render the extension figure") from error

    palette = {
        "direct only": "#d39b3d",
        "direct+indirect": "#17324d",
        "pure control": "#75a478",
        "spillover only": "#4c82ad",
    }
    radii = list(RADII_KM)
    figure, axis = plt.subplots(figsize=(7.4, 4.5))
    bottoms = np.zeros(len(radii), dtype=float)
    for cell in CELL_ORDER:
        values = []
        for radius in radii:
            match = cells[(cells["radius_km"] == radius) & (cells["cell"] == cell)]
            values.append(int(match["village_count"].iloc[0]) if not match.empty else 0)
        axis.bar([str(value) for value in radii], values, bottom=bottoms, label=cell, color=palette[cell])
        bottoms += np.asarray(values, dtype=float)
    axis.set_title("Nearby-treatment exposure cells become thin quickly", loc="left", weight="bold")
    axis.set_xlabel("Radius (km)")
    axis.set_ylabel("Villages")
    axis.grid(axis="y", color="#d9e2ec", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.legend(frameon=False, fontsize=8, loc="upper left")
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, facecolor="white")
    plt.close(figure)


def main() -> int:
    args = parse_args()
    inputs = [
        args.timing,
        args.household,
        args.village,
        args.treatment_status,
        args.village_buffer,
    ]
    _require_files(inputs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.figure_dir.mkdir(parents=True, exist_ok=True)

    timing = compute_timing_regression(args.timing, args.household, args.treatment_status)
    cells, households, summary = compute_exposure_tables(
        args.household, args.village, args.village_buffer
    )
    timing.to_csv(args.output_dir / "extension_timing_regression.csv", index=False)
    cells.to_csv(args.output_dir / "extension_exposure_cells.csv", index=False)
    households.to_csv(args.output_dir / "extension_exposure_households.csv", index=False)
    summary.to_csv(args.output_dir / "extension_neighbor_summary.csv", index=False)
    write_exposure_figure(cells, args.figure_dir / "extension_exposure_cells.png")
    print(
        "Extension complete: aggregate timing diagnostics, exposure-cell tables, "
        "and one disclosure-safe figure were written."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
