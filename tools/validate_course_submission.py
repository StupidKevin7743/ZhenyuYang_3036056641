#!/usr/bin/env python3
"""Validate the data-free ECON6067 submission contract using the standard library."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REPOSITORY_NAME = "ZhenyuYang_3036056641"
REQUIRED_FILES = {
    "README.md",
    "report.pdf",
    "AI_USE_DISCLOSURE.md",
    "CONTRIBUTIONS.md",
    "code/run_all.py",
    "code/table5_multiplier_bootstrap.py",
    "code/extension_timing_exposure.py",
    "code/render_figures.py",
    "code/build_report.py",
    "config/project.json",
    "config/input_manifest.json",
    "config/published_benchmarks.csv",
    "data/raw/README.md",
    "data/processed/README.md",
    "outputs/tables/table5_2000_bootstrap_summary.csv",
    "outputs/tables/table5_paper_comparison.csv",
    "outputs/tables/table5_point_validation.csv",
    "outputs/tables/extension_timing_regression.csv",
    "outputs/tables/extension_exposure_cells.csv",
    "outputs/tables/extension_exposure_households.csv",
    "outputs/tables/extension_neighbor_summary.csv",
    "outputs/figures/table5_multiplier_comparison.png",
    "outputs/figures/extension_exposure_cells.png",
    "skills/SKILL.md",
}
EXPECTED_ROWS = {
    "outputs/tables/table5_2000_bootstrap_summary.csv": 12,
    "outputs/tables/table5_paper_comparison.csv": 12,
    "outputs/tables/table5_point_validation.csv": 11,
    "outputs/tables/extension_timing_regression.csv": 10,
    "outputs/tables/extension_exposure_cells.csv": 8,
    "outputs/tables/extension_exposure_households.csv": 16,
    "outputs/tables/extension_neighbor_summary.csv": 3,
}


def fail(message: str) -> None:
    raise ValueError(message)


def require_files() -> None:
    for relative in sorted(REQUIRED_FILES):
        path = REPO_ROOT / relative
        if not path.is_file():
            fail(f"Required course file is missing: {relative}")
        if path.stat().st_size == 0:
            fail(f"Required course file is empty: {relative}")


def validate_identity_and_scope() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    disclosure = (REPO_ROOT / "AI_USE_DISCLOSURE.md").read_text(encoding="utf-8")
    contributions = (REPO_ROOT / "CONTRIBUTIONS.md").read_text(encoding="utf-8")
    for label, text in (
        ("README.md", readme),
        ("AI_USE_DISCLOSURE.md", disclosure),
        ("CONTRIBUTIONS.md", contributions),
    ):
        if "Zhenyu Yang" not in text or "3036056641" not in text:
            fail(f"{label} must identify the student and university number")
    if EXPECTED_REPOSITORY_NAME not in readme:
        fail("README.md must identify the required Name_StudentID repository")
    required_scope_phrases = (
        "Table V",
        "approval",
        "pending",
        "rollout",
        "exposure",
        "2,000",
        "runGPS = 0",
    )
    for phrase in required_scope_phrases:
        if phrase not in readme:
            fail(f"README.md is missing required scope or limitation text: {phrase}")


def validate_config() -> None:
    project = json.loads((REPO_ROOT / "config/project.json").read_text(encoding="utf-8"))
    manifest = json.loads((REPO_ROOT / "config/input_manifest.json").read_text(encoding="utf-8"))
    if project.get("privacy", {}).get("runGPS") != 0:
        fail("config/project.json must keep runGPS at 0")
    if project.get("paper", {}).get("alternative_paper_approval") != "pending":
        fail("Alternative-paper approval must remain pending until documented")
    inputs = manifest.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != 7:
        fail("config/input_manifest.json must describe exactly seven course inputs")
    for entry in inputs:
        if entry.get("committed") is not False:
            fail(f"Input must remain uncommitted: {entry.get('key')}")
        path = Path(str(entry.get("default_path", "")))
        if path.is_absolute() or ".." in path.parts:
            fail(f"Input default must be repository-relative: {entry.get('key')}")


def validate_aggregate_tables() -> None:
    for relative, expected_rows in EXPECTED_ROWS.items():
        path = REPO_ROOT / relative
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != expected_rows:
            fail(f"{relative} has {len(rows)} rows; expected {expected_rows}")
        headers = {name.lower() for name in (rows[0].keys() if rows else [])}
        forbidden = {
            "village_code",
            "household_id",
            "hhid",
            "latitude",
            "longitude",
            "gps",
        }
        overlap = sorted(headers & forbidden)
        if overlap:
            fail(f"{relative} exposes forbidden record fields: {', '.join(overlap)}")


def validate_binary_artifacts() -> None:
    signatures = {
        "report.pdf": b"%PDF-",
        "outputs/figures/table5_multiplier_comparison.png": b"\x89PNG\r\n\x1a\n",
        "outputs/figures/extension_exposure_cells.png": b"\x89PNG\r\n\x1a\n",
    }
    for relative, signature in signatures.items():
        with (REPO_ROOT / relative).open("rb") as handle:
            if not handle.read(len(signature)).startswith(signature):
                fail(f"Unexpected file signature: {relative}")


def main() -> int:
    try:
        require_files()
        validate_identity_and_scope()
        validate_config()
        validate_aggregate_tables()
        validate_binary_artifacts()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"COURSE SUBMISSION VALIDATION FAILED: {error}", file=sys.stderr)
        return 1
    print(
        "COURSE SUBMISSION VALIDATION PASSED: required files, student identity, "
        "scope limits, input contract, aggregate row counts, and artifact signatures verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
