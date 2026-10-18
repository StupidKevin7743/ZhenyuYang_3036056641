#!/usr/bin/env python3
"""Run or audit the ECON6067 core replication and independent extension.

The default execution runs one core target (Table V) and one extension target
(rollout timing and nearby-treatment exposure support).  ``--check-only`` is a
data-free release audit: it validates code, configuration, privacy settings,
and committed aggregate artifacts without rewriting them.  If every selected
private input is already present, preflight also validates the core schemas and
known input hashes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

# The data-free audit promises not to create repository artifacts.  Disable
# local ``__pycache__`` files before importing the core module so a plain
# ``python3 code/run_all.py --check-only`` keeps the worktree unchanged.
sys.dont_write_bytecode = True

from table5_multiplier_bootstrap import (
    DEFAULT_POINT_TOLERANCE,
    DEFAULT_REPS,
    DEFAULT_SEED,
    load_benchmarks,
    run_table5,
    validate_inputs,
    validate_run_gps,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs"
DEFAULT_DATA = REPO_ROOT / "data" / "processed" / "HH_ENT_Multiplier_Dataset_ECMA.dta"
DEFAULT_ESTIMATES = REPO_ROOT / "data" / "processed" / "multiplier_estimates.dta"
DEFAULT_TIMING = REPO_ROOT / "data" / "processed" / "GE_experimental_timing_long_FINAL.dta"
DEFAULT_HOUSEHOLD = REPO_ROOT / "data" / "processed" / "GE_HHLevel_ECMA.dta"
DEFAULT_VILLAGE = REPO_ROOT / "data" / "processed" / "GE_VillageLevel_ECMA.dta"
DEFAULT_TREATMENT_STATUS = REPO_ROOT / "data" / "raw" / "GE_Treat_Status_Master.dta"
DEFAULT_VILLAGE_BUFFER = (
    REPO_ROOT / "data" / "raw" / "VillageBuffers_GE_HHs_1km_Increments_PUBLIC.dta"
)
DEFAULT_BENCHMARKS = REPO_ROOT / "config" / "published_benchmarks.csv"
DEFAULT_MANIFEST = REPO_ROOT / "config" / "input_manifest.json"
DEFAULT_PROJECT_CONFIG = REPO_ROOT / "config" / "project.json"
DEFAULT_RUN_GPS_CONFIG = REPO_ROOT / "do" / "global_runGPS.do"
EXTENSION_SCRIPT = REPO_ROOT / "code" / "extension_timing_exposure.py"

CORE_TABLES = {
    "table5_2000_bootstrap_summary.csv": {
        "panel",
        "row",
        "estimate",
        "se",
        "p_m_lt_0",
        "p_m_lt_1",
    },
    "table5_paper_comparison.csv": {
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
    },
    "table5_point_validation.csv": {"row", "python_point", "stata_point", "difference"},
}
EXTENSION_TABLES = {
    "extension_timing_regression.csv": {
        "model",
        "variable",
        "coefficient",
        "standard_error",
        "p_value",
        "n",
        "clusters",
        "covariance",
    },
    "extension_exposure_cells.csv": {"radius_km", "cell", "village_count"},
    "extension_exposure_households.csv": {
        "radius_km",
        "cell",
        "eligible",
        "weighted_households",
    },
    "extension_neighbor_summary.csv": {
        "radius_km",
        "villages_with_0_neighbors",
        "mean_nearby_villages",
        "median_nearby_villages",
        "max_nearby_villages",
        "villages_with_0_treated_neighbors",
        "villages_with_1_treated_neighbor",
        "villages_with_2_treated_neighbors",
        "villages_with_3plus_treated_neighbors",
    },
}
CORE_FIGURE = "table5_multiplier_comparison.png"
EXTENSION_FIGURE = "extension_exposure_cells.png"
FORBIDDEN_OUTPUT_COLUMNS = {
    "village_code",
    "hhid",
    "hh_id",
    "household_id",
    "latitude",
    "longitude",
    "lat",
    "lon",
    "xcoord",
    "ycoord",
    "gps",
}


def _load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing configuration: {path}")
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Configuration must be a JSON object: {path}")
    return value


def validate_configuration(project_path: Path, manifest_path: Path) -> dict[str, dict[str, object]]:
    project = _load_json(project_path)
    manifest = _load_json(manifest_path)
    project_privacy = project.get("privacy")
    manifest_privacy = manifest.get("privacy")
    if not isinstance(project_privacy, dict) or project_privacy.get("runGPS") != 0:
        raise ValueError("config/project.json must declare privacy.runGPS = 0")
    if not isinstance(manifest_privacy, dict) or manifest_privacy.get("runGPS") != 0:
        raise ValueError("config/input_manifest.json must declare privacy.runGPS = 0")

    entries = manifest.get("inputs")
    if not isinstance(entries, list):
        raise ValueError("config/input_manifest.json must contain an inputs list")
    indexed: dict[str, dict[str, object]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("key"), str):
            raise ValueError("Every input-manifest entry must be an object with a string key")
        key = str(entry["key"])
        if key in indexed:
            raise ValueError(f"Duplicate input-manifest key: {key}")
        default_path = Path(str(entry.get("default_path", "")))
        if not str(default_path) or default_path.is_absolute() or ".." in default_path.parts:
            raise ValueError(f"Manifest path must be a safe repository-relative path: {key}")
        if entry.get("committed") is not False:
            raise ValueError(f"Private input must be declared uncommitted: {key}")
        indexed[key] = entry

    expected = {
        "multiplier_data",
        "multiplier_estimates",
        "timing",
        "household",
        "village",
        "treatment_status",
        "village_buffer",
    }
    missing = sorted(expected - set(indexed))
    if missing:
        raise ValueError("Input manifest is missing keys: " + ", ".join(missing))
    return indexed


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_known_hash(path: Path, entry: dict[str, object]) -> None:
    expected = entry.get("sha256")
    if expected is None:
        return
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError(f"Invalid SHA-256 value in manifest for {entry.get('key')}")
    actual = _sha256(path)
    if actual.lower() != expected.lower():
        raise ValueError(
            f"Input hash does not match the audited manifest for {entry.get('key')}: {path}"
        )


def _read_csv(path: Path, required_columns: set[str]) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing canonical aggregate table: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        rows = list(reader)
    missing = sorted(required_columns - set(headers))
    if missing:
        raise ValueError(f"{path.name} is missing columns: {', '.join(missing)}")
    forbidden = sorted(FORBIDDEN_OUTPUT_COLUMNS & {name.lower() for name in headers})
    if forbidden:
        raise ValueError(f"{path.name} exposes forbidden record fields: {', '.join(forbidden)}")
    if not rows:
        raise ValueError(f"Canonical aggregate table is empty: {path}")
    return headers, rows


def _float_in_unit_interval(value: str, label: str) -> None:
    if value.strip() == "":
        return
    number = float(value)
    if not 0 <= number <= 1:
        raise ValueError(f"Probability outside [0, 1] in {label}: {value}")


def _validate_png(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing canonical aggregate figure: {path}")
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Unexpected PNG signature: {path}")


def validate_core_artifacts(table_dir: Path, figure_dir: Path, tolerance: float) -> None:
    tables: dict[str, list[dict[str, str]]] = {}
    for name, required in CORE_TABLES.items():
        _, tables[name] = _read_csv(table_dir / name, required)

    summary = tables["table5_2000_bootstrap_summary.csv"]
    validation = tables["table5_point_validation.csv"]
    comparison = tables["table5_paper_comparison.csv"]
    if len(summary) != 12 or len(comparison) != 12:
        raise ValueError("Core summary and comparison must each contain exactly 12 Table V rows")
    if len(validation) != 11:
        raise ValueError("Core point validation must contain exactly 11 quantities")
    for row in summary:
        _float_in_unit_interval(row["p_m_lt_0"], "table5_2000_bootstrap_summary.csv")
        _float_in_unit_interval(row["p_m_lt_1"], "table5_2000_bootstrap_summary.csv")
    max_difference = max(abs(float(row["difference"])) for row in validation)
    if max_difference > tolerance:
        raise ValueError(
            f"Committed point validation exceeds tolerance: {max_difference:.9g} > {tolerance:.9g}"
        )
    _validate_png(figure_dir / CORE_FIGURE)


def validate_extension_artifacts(table_dir: Path, figure_dir: Path) -> None:
    for name, required in EXTENSION_TABLES.items():
        _, rows = _read_csv(table_dir / name, required)
        if name == "extension_timing_regression.csv":
            for row in rows:
                _float_in_unit_interval(row["p_value"], name)
    _validate_png(figure_dir / EXTENSION_FIGURE)


def _compile_script(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing analysis script: {path}")
    compile(path.read_text(encoding="utf-8"), str(path), "exec")


def _all_or_none_present(paths: Iterable[Path], label: str) -> bool:
    paths = list(paths)
    present = [path.is_file() for path in paths]
    if any(present) and not all(present):
        missing = [str(path) for path, exists in zip(paths, present) if not exists]
        raise FileNotFoundError(f"Partial {label} input set; missing: " + ", ".join(missing))
    return all(present)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("core", "extension", "all"), default="all")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate privacy, code, configs, and canonical aggregate artifacts; write nothing",
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Core multiplier analysis .dta")
    parser.add_argument(
        "--estimates", type=Path, default=DEFAULT_ESTIMATES, help="Core Stata multiplier_estimates.dta"
    )
    parser.add_argument("--timing", type=Path, default=DEFAULT_TIMING, help="Extension rollout-timing .dta")
    parser.add_argument("--household", type=Path, default=DEFAULT_HOUSEHOLD, help="Extension household .dta")
    parser.add_argument("--village", type=Path, default=DEFAULT_VILLAGE, help="Extension village .dta")
    parser.add_argument(
        "--treatment-status", type=Path, default=DEFAULT_TREATMENT_STATUS, help="Extension treatment-status .dta"
    )
    parser.add_argument(
        "--village-buffer", type=Path, default=DEFAULT_VILLAGE_BUFFER, help="Extension village-buffer .dta"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Parent directory for tables/ and figures/ (default: outputs)",
    )
    parser.add_argument("--benchmarks", type=Path, default=DEFAULT_BENCHMARKS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--project-config", type=Path, default=DEFAULT_PROJECT_CONFIG)
    parser.add_argument("--run-gps-config", type=Path, default=DEFAULT_RUN_GPS_CONFIG)
    parser.add_argument(
        "--write-draws",
        action="store_true",
        help="Also write aggregate bootstrap draws (not part of the committed release)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.check_only and args.write_draws:
        raise ValueError("--check-only and --write-draws cannot be combined")

    manifest = validate_configuration(args.project_config, args.manifest)
    validate_run_gps(args.run_gps_config)
    load_benchmarks(args.benchmarks)
    _compile_script(REPO_ROOT / "code" / "table5_multiplier_bootstrap.py")
    _compile_script(EXTENSION_SCRIPT)

    table_dir = args.output_dir / "tables"
    figure_dir = args.output_dir / "figures"
    run_core = args.target in {"core", "all"}
    run_extension = args.target in {"extension", "all"}
    core_inputs = [args.data, args.estimates]
    extension_inputs = [
        args.timing,
        args.household,
        args.village,
        args.treatment_status,
        args.village_buffer,
    ]

    if args.check_only:
        if run_core:
            validate_core_artifacts(table_dir, figure_dir, DEFAULT_POINT_TOLERANCE)
            if _all_or_none_present(core_inputs, "core"):
                validate_inputs(args.data, args.estimates, args.run_gps_config)
                validate_known_hash(args.data, manifest["multiplier_data"])
                validate_known_hash(args.estimates, manifest["multiplier_estimates"])
        if run_extension:
            validate_extension_artifacts(table_dir, figure_dir)
            _all_or_none_present(extension_inputs, "extension")
        print(
            f"Preflight passed for target={args.target}: runGPS=0, configuration and code valid, "
            "canonical aggregate artifacts passed; no outputs written."
        )
        return 0

    if run_core:
        if not _all_or_none_present(core_inputs, "core"):
            raise FileNotFoundError("Core inputs are absent; see config/input_manifest.json")
        validate_known_hash(args.data, manifest["multiplier_data"])
        validate_known_hash(args.estimates, manifest["multiplier_estimates"])
        result = run_table5(
            data_path=args.data,
            estimates_path=args.estimates,
            benchmarks_path=args.benchmarks,
            output_dir=table_dir,
            figure_dir=figure_dir,
            run_gps_config=args.run_gps_config,
            reps=DEFAULT_REPS,
            seed=DEFAULT_SEED,
            point_tolerance=DEFAULT_POINT_TOLERANCE,
            write_draws=args.write_draws,
        )
        print(
            "Core complete: accelerated Python reimplementation, 2,000 draws, seed 12345; "
            f"max point difference={result.max_point_difference:.9g}."
        )

    if run_extension:
        if not _all_or_none_present(extension_inputs, "extension"):
            raise FileNotFoundError("Extension inputs are absent; see config/input_manifest.json")
        command = [
            sys.executable,
            str(EXTENSION_SCRIPT),
            "--timing",
            str(args.timing),
            "--household",
            str(args.household),
            "--village",
            str(args.village),
            "--treatment-status",
            str(args.treatment_status),
            "--village-buffer",
            str(args.village_buffer),
            "--output-dir",
            str(table_dir),
            "--figure-dir",
            str(figure_dir),
        ]
        subprocess.run(command, cwd=REPO_ROOT, check=True)

    if run_core:
        validate_core_artifacts(table_dir, figure_dir, DEFAULT_POINT_TOLERANCE)
    if run_extension:
        validate_extension_artifacts(table_dir, figure_dir)
    print(
        "Reproduction complete. Outputs are aggregate only; runGPS=0. "
        "The extension is a design/identification diagnostic, not a treatment-outcome estimate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
