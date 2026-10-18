#!/usr/bin/env python3
"""Render disclosure-safe course figures from committed aggregate CSV files."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table-dir", type=Path, required=True)
    parser.add_argument("--figure-dir", type=Path, required=True)
    return parser.parse_args()


def render_table5_comparison(
    comparison: pd.DataFrame,
    output_path: Path,
    replication_label: str = "2,000-draw reimplementation",
) -> None:
    """Render the shared monochrome comparison and atomically replace its PNG."""
    import matplotlib

    # The CLI and core pipeline must use the same export backend.
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = comparison[comparison["published_estimate"].notna()].copy()
    labels = {
        "Expenditure multiplier": "Expenditure multiplier",
        "Household non-durable expenditure": "Nondurable expenditure",
        "Household durable expenditure": "Durable expenditure",
        "Enterprise investment": "Enterprise investment",
        "Enterprise inventory": "Enterprise inventory",
        "Income multiplier": "Income multiplier",
        "Enterprise profits": "Enterprise profits",
        "Household wage bill": "Household wage bill",
        "Enterprise capital income": "Enterprise capital income",
        "Enterprise taxes paid": "Enterprise taxes",
        "Average of both multipliers": "Average multiplier",
    }
    data["label"] = data["row"].map(labels)
    data = data.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(data), dtype=float)

    figure, axis = plt.subplots(figsize=(9.19, 6.2))
    axis.errorbar(
        data["published_estimate"],
        y + 0.12,
        xerr=data["published_se"],
        fmt="o",
        color="0.35",
        ecolor="0.55",
        markerfacecolor="white",
        markeredgecolor="0.25",
        markersize=5.5,
        elinewidth=1.0,
        capsize=3,
        label="Published Table V",
    )
    axis.errorbar(
        data["replicated_estimate"],
        y - 0.12,
        xerr=data["replicated_se"],
        fmt="D",
        color="black",
        ecolor="black",
        markerfacecolor="black",
        markersize=4.5,
        elinewidth=1.0,
        capsize=3,
        label=replication_label,
    )
    axis.axvline(0, color="0.45", linewidth=0.8)
    axis.set_yticks(y, data["label"])
    axis.set_xlabel("Estimate (bars show ± one standard error)", labelpad=9)
    axis.set_title("Published and replicated multiplier estimates", loc="left", weight="bold", pad=13)
    axis.grid(axis="x", color="0.88", linewidth=0.7)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    figure.legend(
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.62, 0.015),
        ncol=2,
        fontsize=9,
    )
    figure.tight_layout(rect=(0, 0.09, 1, 1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".png", dir=output_path.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        figure.savefig(temporary, dpi=220, facecolor="white")
        temporary.replace(output_path)
    finally:
        plt.close(figure)
        temporary.unlink(missing_ok=True)


def render_table5(table_dir: Path, figure_dir: Path) -> None:
    comparison = pd.read_csv(table_dir / "table5_paper_comparison.csv")
    render_table5_comparison(comparison, figure_dir / "table5_multiplier_comparison.png")


def main() -> int:
    args = parse_args()
    args.figure_dir.mkdir(parents=True, exist_ok=True)
    render_table5(args.table_dir, args.figure_dir)
    print("Rendered table5_multiplier_comparison.png from aggregate CSV input.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
