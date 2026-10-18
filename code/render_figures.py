#!/usr/bin/env python3
"""Render disclosure-safe course figures from committed aggregate CSV files."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table-dir", type=Path, required=True)
    parser.add_argument("--figure-dir", type=Path, required=True)
    return parser.parse_args()


def render_table5(table_dir: Path, figure_dir: Path) -> None:
    import matplotlib.pyplot as plt

    data = pd.read_csv(table_dir / "table5_paper_comparison.csv")
    data = data[data["published_estimate"].notna()].copy()
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

    figure, axis = plt.subplots(figsize=(9.2, 6.0))
    axis.errorbar(
        data["published_estimate"],
        y + 0.12,
        xerr=data["published_se"],
        fmt="o",
        color="#7b8794",
        ecolor="#b8c2cc",
        capsize=2,
        label="Published Table V",
    )
    axis.errorbar(
        data["replicated_estimate"],
        y - 0.12,
        xerr=data["replicated_se"],
        fmt="o",
        color="#17324d",
        ecolor="#4c82ad",
        capsize=2,
        label="2,000-draw reimplementation",
    )
    axis.axvline(0, color="#8795a1", linewidth=0.8)
    axis.set_yticks(y, data["label"])
    axis.set_xlabel("Multiplier component estimate (± one standard error)")
    axis.set_title("Table V point estimates and uncertainty closely track the paper", loc="left", weight="bold")
    axis.grid(axis="x", color="#d9e2ec", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
    )
    figure.tight_layout()
    figure.savefig(figure_dir / "table5_multiplier_comparison.png", dpi=220, facecolor="white")
    plt.close(figure)


def main() -> int:
    args = parse_args()
    args.figure_dir.mkdir(parents=True, exist_ok=True)
    render_table5(args.table_dir, args.figure_dir)
    print("Rendered table5_multiplier_comparison.png from aggregate CSV input.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
