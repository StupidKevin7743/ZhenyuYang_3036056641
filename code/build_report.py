#!/usr/bin/env python3
"""Build the ECON6067 final-project report from committed aggregate outputs."""

from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = REPO_ROOT / "outputs" / "tables"
FIGURE_DIR = REPO_ROOT / "outputs" / "figures"
OUTPUT_PATH = REPO_ROOT / "report.pdf"

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#3D7199")
SKY = colors.HexColor("#EAF2F8")
INK = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#5E6D7A")
LIGHT = colors.HexColor("#F6F8FA")
BORDER = colors.HexColor("#D9E2EC")
GOLD = colors.HexColor("#B98228")
GREEN = colors.HexColor("#4E7D5A")
RED = colors.HexColor("#A44A3F")


def read_csv(name: str) -> list[dict[str, str]]:
    with (TABLE_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=31,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=18,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=14,
            leading=20,
            textColor=BLUE,
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=10,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            textColor=BLUE,
            spaceBefore=9,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=INK,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            spaceAfter=5,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=NAVY,
            borderColor=BLUE,
            borderWidth=1,
            borderPadding=9,
            backColor=SKY,
            spaceBefore=13,
            spaceAfter=10,
        ),
        "warning": ParagraphStyle(
            "Warning",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13.5,
            textColor=RED,
            borderColor=GOLD,
            borderWidth=1,
            borderPadding=9,
            backColor=colors.HexColor("#FFF8E8"),
            spaceAfter=10,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.8,
            leading=10.5,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "covermeta": ParagraphStyle(
            "CoverMeta",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=17,
            textColor=INK,
            spaceAfter=2,
        ),
    }


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullet(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(f"<bullet>&bull;</bullet>{text}", style)


def course_table(
    rows: list[list[object]],
    widths: list[float],
    *,
    font_size: float = 7.4,
    header_rows: int = 1,
) -> Table:
    body_cell_style = ParagraphStyle(
        "Cell",
        fontName="Helvetica",
        fontSize=font_size,
        leading=font_size + 2,
        textColor=INK,
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell",
        fontName="Helvetica-Bold",
        fontSize=font_size,
        leading=font_size + 2,
        textColor=colors.white,
    )
    converted = []
    for row_index, row in enumerate(rows):
        cell_style = header_cell_style if row_index < header_rows else body_cell_style
        converted.append(
            [
                cell if isinstance(cell, Paragraph) else Paragraph(str(cell), cell_style)
                for cell in row
            ]
        )
    table = Table(converted, colWidths=widths, repeatRows=header_rows, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.white),
        ("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for row_index in range(header_rows, len(rows)):
        if (row_index - header_rows) % 2:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), LIGHT))
    table.setStyle(TableStyle(commands))
    return table


def add_header_footer(canvas, document) -> None:
    canvas.saveState()
    page = canvas.getPageNumber()
    if page > 1:
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(0.65 * inch, 0.58 * inch, 7.85 * inch, 0.58 * inch)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.68 * inch, 0.38 * inch, "ECON6067 Final Project | Zhenyu Yang | 3036056641")
        canvas.drawRightString(7.82 * inch, 0.38 * inch, f"Page {page}")
    canvas.restoreState()


def build_story() -> list[object]:
    s = styles()
    summary = read_csv("table5_2000_bootstrap_summary.csv")
    comparison = read_csv("table5_paper_comparison.csv")
    validation = read_csv("table5_point_validation.csv")
    timing = read_csv("extension_timing_regression.csv")
    cells = read_csv("extension_exposure_cells.csv")
    households = read_csv("extension_exposure_households.csv")
    neighbors = read_csv("extension_neighbor_summary.csv")

    story: list[object] = []
    story.extend(
        [
            Spacer(1, 0.55 * inch),
            p("ECON6067 Individual Final Project", s["subtitle"]),
            p("Cash Transfers and Local General Equilibrium", s["title"]),
            p(
                "Replication of Egger et al. (2022) Table V, "
                "with a rollout-timing and exposure-network robustness extension",
                s["subtitle"],
            ),
            Spacer(1, 0.35 * inch),
            Table(
                [
                    [p("Student", s["small"]), p("Zhenyu Yang", s["covermeta"])],
                    [p("Student ID", s["small"]), p("3036056641", s["covermeta"])],
                    [p("Course", s["small"]), p("ECON6067 Quantitative Tools for Economics", s["covermeta"])],
                    [p("Submission date", s["small"]), p("18 October 2026", s["covermeta"])],
                    [p("Repository", s["small"]), p("github.com/StupidKevin7743/ZhenyuYang_3036056641", s["covermeta"])],
                ],
                colWidths=[1.3 * inch, 5.6 * inch],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LINEBELOW", (0, 0), (-1, -1), 0.35, BORDER),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                ),
            ),
            Spacer(1, 0.45 * inch),
            p(
                "APPROVAL STATUS: Egger et al. is an alternative paper outside the four "
                "illustrative options in the project brief. Instructor approval and target "
                "confirmation are requested in the accompanying unsent email draft; approval "
                "has not been assumed in this report.",
                s["warning"],
            ),
            Spacer(1, 0.18 * inch),
            p(
                "Reproducibility statement: the repository contains code, disclosure-reviewed "
                "aggregate outputs, access instructions, an AI-use record, and one public entry "
                "point. It contains no microdata, household identifiers, coordinates, or restricted GPS inputs.",
                s["callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("1. Executive summary", s["h1"]),
            p(
                "Egger et al. (2022) study a one-time cash-transfer program that paid about "
                "USD 1,000 nominal to more than 10,500 poor households in 653 randomized Kenyan "
                "villages. Because the transfer shock exceeded 15% of local GDP, the experiment "
                "can measure both direct recipient spending and indirect local spillovers. The "
                "paper's central result is a local transfer multiplier of roughly 2.5 with little "
                "aggregate price inflation.",
                s["body"],
            ),
            p(
                "This project targets Table V. It reproduces the published dynamic-IV "
                "point estimates and validates a matrix-based Python implementation against Stata "
                "to within 1.8e-7. It then performs 2,000 Rademacher wild-cluster draws at the "
                "sublocation level. The reimplemented expenditure multiplier is 2.5767 "
                "(SE 1.4575), the income multiplier is 2.4691 (SE 1.7874), and their average is "
                "2.5229 (SE 1.4278). These closely track the printed estimates 2.58, 2.47, and 2.52.",
                s["body"],
            ),
            p(
                "The independent extension asks whether rollout timing and the nearby-treatment "
                "network create systematic selection or very thin comparison cells. Conditional "
                "on subcounty fixed effects, timing is not detectably related to village size, "
                "eligibility share, or saturation assignment. Yet at a 2 km radius there is only "
                "one direct-only village and four pure-control villages; those categories disappear "
                "at 3 km and 4 km. This is an identification diagnostic, not a new treatment-effect estimate.",
                s["body"],
            ),
            p("What the project establishes", s["h2"]),
            bullet("Core Table V point estimates and presentation are reproduced.", s["body"]),
            bullet("The completed 2,000-draw accelerator closely reconciles published uncertainty and p-values.", s["body"]),
            bullet("The extension makes rollout phases and exposure-cell support auditable.", s["body"]),
            p("What the project does not establish", s["h2"]),
            bullet("It is not a full-paper, paper-identical end-to-end replication.", s["body"]),
            bullet("It does not reproduce the restricted-coordinate spatial-HAC implementation.", s["body"]),
            bullet("The direct Stata 2,000-repetition loop did not finish; the final inference is the validated Python accelerator.", s["body"]),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("2. Research question and economic mechanism", s["h1"]),
            p(
                "The paper asks whether a large, externally financed cash transfer raises only the "
                "recipient household's expenditure or also expands local production and income. A "
                "purely partial-equilibrium view predicts direct consumption gains. A local "
                "general-equilibrium view adds demand spillovers: recipients buy local goods and "
                "services, firms respond through sales, inventories, investment, profits, wages, "
                "and taxes, and nonrecipients receive part of the resulting income flow.",
                s["body"],
            ),
            p(
                "The multiplier divides the integrated local expenditure or income response by the "
                "transfer amount. Values greater than one are possible when one household's spending "
                "becomes another household's or firm's income and is spent again. Whether this occurs "
                "without large inflation depends on local supply elasticities, unused capacity, trade, "
                "and leakage outside the study area.",
                s["body"],
            ),
            p("Why Table V", s["h2"]),
            p(
                "Table V aggregates the paper's dynamic expenditure and income responses into the "
                "headline multipliers and decomposes them into economically interpretable components. "
                "The paper's Figure 1 provides the quarterly-path context, but this course package does "
                "not claim to regenerate that exhibit. The selected table connects the research question, "
                "identification strategy, dynamics, and main conclusion more directly than a descriptive "
                "balance table would.",
                s["body"],
            ),
            p("Predictions assessed", s["h2"]),
            course_table(
                [
                    ["Prediction", "Observable implication"],
                    ["Local demand propagates", "Expenditure and income multipliers exceed zero and may exceed one."],
                    ["Supply responds", "Enterprise profits, investment, inventories, wages, and taxes rise."],
                    ["Effects unfold over time", "Impulse responses persist across quarterly lags rather than appearing in one period."],
                    ["Design support matters", "Rollout and exposure cells provide credible variation for own and nearby transfers."],
                ],
                [2.15 * inch, 4.65 * inch],
                font_size=8.2,
            ),
            Spacer(1, 0.12 * inch),
            p(
                "The extension focuses on the fourth prediction. It does not redefine the paper's "
                "estimand; it tests whether the timing and simplified exposure geometry reveal support "
                "problems that should qualify interpretation.",
                s["callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("3. Data, sample, and experimental design", s["h1"]),
            p(
                "The experiment covers 653 villages in 84 sublocations: 328 treated and 325 control. "
                "Randomization is hierarchical. Sublocations were assigned to high- or low-saturation "
                "groups, and villages within them were treated at different probabilities. Eligible "
                "households in treated villages received KES 87,000 in three payments: KES 7,000, "
                "then KES 40,000 about two months later, then KES 40,000 about six months later.",
                s["body"],
            ),
            p(
                "The household census contains 65,383 households (about 280,000 people). Baseline "
                "surveys cover 7,845 households and endline surveys 8,239, with tracking above 90%. "
                "Endline occurred a median 19 months after experimental start and about 11 months "
                "after the final transfer. Enterprise and market data supply the remaining multiplier components.",
                s["body"],
            ),
            p("Inputs used by this package", s["h2"]),
            course_table(
                [
                    ["Logical input", "Role", "Public-repository treatment"],
                    ["HH/enterprise multiplier analysis file", "Dynamic-IV components for Table V", "Access instructions only; never committed"],
                    ["Stata multiplier estimate file", "Point-estimate cross-check", "Generated/authorized local input; never committed"],
                    ["Experimental timing panel", "Actual rollout month", "Access instructions only; never committed"],
                    ["Household/village analysis files", "Village size, eligibility, treatment", "Access instructions only; never committed"],
                    ["Provider-supplied village-buffer file", "Counts of nearby treated villages", "No coordinates committed; input remains untracked"],
                ],
                [1.7 * inch, 2.4 * inch, 2.7 * inch],
                font_size=7.4,
            ),
            p("Disclosure boundary", s["h2"]),
            p(
                "Only aggregate CSV tables and two figures are versioned. The repository's release "
                "auditor uses an exact output allowlist and rejects Stata data, coordinates, archives, "
                "logs, identifiers, machine-local paths, unexpected result files, and credentials. "
                "Legacy public execution fixes <b>runGPS = 0</b>; no claim is made about restricted GPS analysis.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("4. Identification and replication method", s["h1"]),
            p(
                "The paper's dynamic IV specification relates quarterly outcomes to own-village and "
                "nearby-village cumulative transfer amounts within 0-2 km across ten quarterly lags. "
                "Random assignment of village treatment, saturation, and rollout timing instruments "
                "for realized transfer exposure. Flow responses are integrated over 29 months; stock "
                "outcomes are measured at endline. Values are expressed in January 2015 terms.",
                s["body"],
            ),
            p("Core workflow", s["h2"]),
            course_table(
                [
                    ["Stage", "Implementation", "Validation"],
                    ["1. Point estimates", "Reconstruct the Table V dynamic-IV component vector", "Compare 11 quantities with Stata"],
                    ["2. Resampling", "2,000 Rademacher wild-cluster draws by sublocation", "Check exact draw count and fixed seed"],
                    ["3. Aggregation", "Form expenditure, income, average, and joint tests", "Compare printed precision with Table V"],
                    ["4. Presentation", "Write aggregate CSVs and render figures", "Schema/privacy audit plus visual review"],
                ],
                [1.3 * inch, 3.0 * inch, 2.5 * inch],
                font_size=7.7,
            ),
            p("Inference", s["h2"]),
            p(
                "For each wild-bootstrap draw, sublocation-level Rademacher weights perturb the null "
                "residual structure. The empirical distribution yields bootstrap standard errors and "
                "one-sided probabilities Pr(M &lt; 0) and Pr(M &lt; 1). This matches the paper's stated "
                "2,000 within-sublocation replication logic. The Python code is a matrix accelerator, "
                "not a claim that the original Stata loop completed.",
                s["body"],
            ),
            p("Pre-specified comparison rule", s["h2"]),
            p(
                "A point estimate passes if the Python-Stata absolute difference is below 1e-6. A "
                "printed benchmark is treated as reconciled when the reimplemented value agrees at "
                "the paper's reported precision or its small deviation is reported explicitly. No "
                "manual edits are made to canonical output numbers.",
                s["callout"],
            ),
            p("Why not use the earlier three-draw result?", s["h2"]),
            p(
                "The earlier Stata smoke run reproduces point estimates but produces p-values only in "
                "increments of one third and unstable standard errors. It is retained as pipeline "
                "evidence only and excluded from the canonical course outputs.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    key_rows = {row["row"]: row for row in comparison}
    full_table_rows: list[list[object]] = [["Component", "Paper", "Reimpl.", "Paper SE", "Reimpl. SE", "p<0", "p<1"]]
    for label in (
        "Expenditure multiplier",
        "Household non-durable expenditure",
        "Household durable expenditure",
        "Enterprise investment",
        "Enterprise inventory",
        "Income multiplier",
        "Enterprise profits",
        "Household wage bill",
        "Enterprise capital income",
        "Enterprise taxes paid",
        "Average of both multipliers",
    ):
        row = key_rows[label]
        full_table_rows.append(
            [
                label,
                f"{float(row['published_estimate']):.2f}",
                f"{float(row['replicated_estimate']):.2f}",
                f"{float(row['published_se']):.2f}",
                f"{float(row['replicated_se']):.2f}",
                f"{float(row['replicated_p_m_lt_0']):.3f}",
                f"{float(row['replicated_p_m_lt_1']):.3f}" if row["replicated_p_m_lt_1"] else "-",
            ]
        )
    story.extend(
        [
            p("5. Core replication results", s["h1"]),
            p(
                "The core point estimates match the paper at printed precision. The expenditure "
                "multiplier is 2.5767; the income multiplier is 2.4691; their average is 2.5229. "
                "The 2,000-draw standard errors are slightly larger than the published values by "
                "0.018, 0.077, and 0.038, respectively. The reimplemented one-sided p-values remain "
                "close to those printed in Table V.",
                s["body"],
            ),
            course_table(
                full_table_rows,
                [2.12 * inch, 0.56 * inch, 0.62 * inch, 0.64 * inch, 0.69 * inch, 0.55 * inch, 0.55 * inch],
                font_size=6.65,
            ),
            p(
                "Table 1. Published versus reimplemented Table V. p&lt;0 and p&lt;1 are the "
                "reimplemented one-sided wild-bootstrap probabilities. A dash means the paper did "
                "not report that component-level test.",
                s["caption"],
            ),
            p("Interpretation", s["h2"]),
            p(
                "The expenditure multiplier is significantly above zero at conventional one-sided "
                "levels but not significantly above one (Pr[M&lt;1] = 0.1455). Income has Pr(M&lt;0) = "
                "0.0860 and Pr(M&lt;1) = 0.2105. The joint probabilities for expenditure and income "
                "are 0.0130 against zero and 0.0785 against one. The evidence supports a positive "
                "local response; it is more cautious about claiming a multiplier definitively above one.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("6. Visual comparison and numerical validation", s["h1"]),
            Image(str(FIGURE_DIR / "table5_multiplier_comparison.png"), width=6.95 * inch, height=4.54 * inch),
            p(
                "Report Figure 1. Published and reimplemented Table V point estimates, with plus/minus one "
                "standard error. The two series nearly overlap. Error bars are descriptive rather than 95% intervals.",
                s["caption"],
            ),
            p("Point-estimate cross-check", s["h2"]),
            p(
                f"Across {len(validation)} Stata quantities, the largest absolute Python-Stata "
                "difference is 1.7844e-7, below the 1e-6 tolerance. This isolates uncertainty "
                "differences from coefficient-construction errors.",
                s["body"],
            ),
            p("Reconciliation, not overclaiming", s["h2"]),
            p(
                "The reimplementation does not reproduce every printed digit of every standard error. "
                "Potential sources include numerical details of the original Stata routines, null "
                "imposition, and random-number implementation. The magnitudes and inference closely "
                "track the published benchmark, but the result is labeled an accelerated "
                "reimplementation rather than a completed original-code bootstrap.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    timing_lookup = {(row["model"], row["variable"]): row for row in timing}
    timing_rows = [["Timing model", "Covariate", "Coef.", "SE", "p-value"]]
    for model in ("Actual start month", "Actual start month (10 pct cutoff)"):
        for variable in ("log weighted village households", "eligible share", "high saturation"):
            row = timing_lookup[(model, variable)]
            timing_rows.append(
                [
                    "First token" if model == "Actual start month" else "10% cutoff",
                    variable,
                    f"{float(row['coefficient']):.3f}",
                    f"{float(row['standard_error']):.3f}",
                    f"{float(row['p_value']):.3f}",
                ]
            )
    cell_lookup = {(int(row["radius_km"]), row["cell"]): int(row["village_count"]) for row in cells}
    story.extend(
        [
            p("7. Independent extension: rollout and exposure support", s["h1"]),
            p(
                "The extension asks: <b>Do rollout timing and nearby-treatment exposure create "
                "systematic selection or thin comparison cells that qualify the interpretation of "
                "general-equilibrium spillovers?</b> It has two parts. First, actual start month is "
                "regressed on pre-existing village scale, eligibility share, and high-saturation "
                "assignment, with subcounty fixed effects and sublocation-clustered standard errors. "
                "Second, villages are classified as direct only, direct plus indirect, pure control, "
                "or spillover only at 2, 3, and 4 km.",
                s["body"],
            ),
            course_table(timing_rows, [1.0 * inch, 2.55 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch], font_size=7.4),
            p(
                "Table 2. Timing diagnostics, N = 328 treated villages and 80 sublocation clusters. "
                "Subcounty fixed effects are included but omitted from the display.",
                s["caption"],
            ),
            p("Result 1: no detected within-subcounty timing gradient", s["h2"]),
            p(
                "The coefficients on log weighted households, eligible share, and high saturation "
                "are individually small relative to their standard errors in both timing definitions. "
                "The subcounty fixed effects are large, consistent with phased geographic rollout. "
                "These are descriptive correlations and do not convert rollout timing into an outcome estimate.",
                s["body"],
            ),
            p("Result 2: binary exposure comparisons become unsupported", s["h2"]),
            p(
                f"At 2 km there are {cell_lookup[(2, 'direct only')]} direct-only, "
                f"{cell_lookup[(2, 'direct+indirect')]} direct-plus-indirect, "
                f"{cell_lookup[(2, 'pure control')]} pure-control, and "
                f"{cell_lookup[(2, 'spillover only')]} spillover-only villages. At 3 km and 4 km, "
                "the direct-only and pure-control cells vanish. Hence a simple four-cell comparison "
                "would be unstable; the paper's continuous exposure design is more appropriate.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    hh_2km: dict[str, float] = {}
    for row in households:
        if int(row["radius_km"]) == 2:
            hh_2km[row["cell"]] = hh_2km.get(row["cell"], 0.0) + float(row["weighted_households"])
    total_hh = sum(hh_2km.values())
    neighbor_2km = next(row for row in neighbors if int(row["radius_km"]) == 2)
    story.extend(
        [
            p("8. Extension evidence and implications", s["h1"]),
            Image(str(FIGURE_DIR / "extension_exposure_cells.png"), width=6.9 * inch, height=4.19 * inch),
            p(
                "Figure 2. Simplified village exposure cells at 2, 3, and 4 km. Each village appears "
                "once within a treated or control bar component for each radius.",
                s["caption"],
            ),
            p("Economic and design interpretation", s["h2"]),
            p(
                f"Within 2 km, villages have on average {float(neighbor_2km['mean_nearby_villages']):.2f} "
                f"neighbors (median {float(neighbor_2km['median_nearby_villages']):.0f}; maximum "
                f"{int(neighbor_2km['max_nearby_villages'])}). Two villages have no neighbors and "
                f"five have no treated neighbor. Direct-only and pure-control villages represent only "
                f"{100 * hh_2km.get('direct only', 0) / total_hh:.1f}% and "
                f"{100 * hh_2km.get('pure control', 0) / total_hh:.1f}% of weighted households. "
                "That lack of support is not evidence against spillovers; it is evidence that binary "
                "cell means would be a poor substitute for continuous nearby-transfer exposure.",
                s["body"],
            ),
            p(
                "The extension therefore strengthens interpretation in a limited but useful way. "
                "Observed timing does not show an obvious within-subcounty association with the three "
                "tested village characteristics, while the geometry explains why instruments based on "
                "randomized saturation and continuous exposure are needed. It also warns against "
                "claiming clean direct-only versus pure-control contrasts at broader radii.",
                s["body"],
            ),
            p("Extension limitations", s["h2"]),
            bullet("Monthly timing cannot recover exact weekly payment order.", s["body"]),
            bullet("The exposure cells reduce a continuous dose to any-versus-none categories.", s["body"]),
            bullet("Timing regressions cover three observed characteristics, not every source of selection.", s["body"]),
            bullet("No new causal outcome coefficient is estimated in this extension.", s["body"]),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("9. Reproducibility package", s["h1"]),
            p(
                "The public repository preserves the upstream Stata/R workflow and adds a course-facing "
                "Python entry point. From an authorized local copy of the documented inputs, the intended "
                "command is <b>python3 code/run_all.py --target all</b>. Explicit path "
                "overrides support inputs stored outside the repository. A check-only mode validates the "
                "committed package without requiring restricted data.",
                s["body"],
            ),
            p("Package map", s["h2"]),
            course_table(
                [
                    ["Path", "Purpose"],
                    ["code/run_all.py", "Single course entry point; preflight, core, extension, output validation"],
                    ["code/table5_multiplier_bootstrap.py", "Portable Table V point estimates and 2,000-draw accelerator"],
                    ["code/extension_timing_exposure.py", "Timing regression and exposure-support diagnostics"],
                    ["code/render_figures.py", "Figures generated only from aggregate CSV outputs"],
                    ["config/", "Project status, input contract, and published benchmarks"],
                    ["data/raw/ and data/processed/", "README access instructions only; inputs remain untracked"],
                    ["outputs/tables/ and outputs/figures/", "Disclosure-reviewed canonical aggregate artifacts"],
                    ["skills/SKILL.md", "Reusable execution, checks, privacy invariants, and troubleshooting"],
                    ["AI_USE_DISCLOSURE.md", "Stage-by-stage AI assistance and human verification"],
                ],
                [2.3 * inch, 4.5 * inch],
                font_size=7.6,
            ),
            p("Fresh-run controls", s["h2"]),
            bullet("Resolve paths from the repository root; no machine-local path is committed.", s["body"]),
            bullet("Fail before analysis if inputs, required variables, or output schemas are missing.", s["body"]),
            bullet("Use a fixed seed and 2,000 draws in paper mode; smoke results cannot replace canonical outputs.", s["body"]),
            bullet("Reject GPS/coordinate files and keep legacy public analysis at runGPS = 0.", s["body"]),
            bullet("Run the exact-path privacy auditor before any push.", s["body"]),
            p(
                "The committed results were regenerated from the existing authorized local analysis "
                "files and compared with the paper. A third party still needs lawful access to the "
                "documented inputs to reproduce the numerical run from scratch.",
                s["callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("10. Validation, limitations, and AI use", s["h1"]),
            p("Validation completed", s["h2"]),
            bullet("Exact paper and appendix identities were verified from contents; key exhibits were rendered.", s["body"]),
            bullet("The core workflow generated exactly 2,000 bootstrap draws with seed 12345; the committed summary contains the 12 canonical Table V rows.", s["body"]),
            bullet("All 11 Python point estimates pass the 1e-6 Stata-difference tolerance.", s["body"]),
            bullet("Extension tables were freshly regenerated and match prior aggregate results.", s["body"]),
            bullet("Canonical CSV schemas, figure dimensions, PDF extraction, and rendered pages were checked.", s["body"]),
            p("Substantive limitations", s["h2"]),
            bullet("Alternative-paper approval remains pending; this is a submission candidate, not evidence of approval.", s["body"]),
            bullet("The package targets Table V plus one robustness extension, not all paper exhibits or the paper's Figure 1.", s["body"]),
            bullet("Restricted spatial-HAC/GPS inference is not reproduced in the public package.", s["body"]),
            bullet("A direct 2,000-draw Stata loop was incomplete; the final results use the validated Python matrix implementation.", s["body"]),
            bullet("Early quarterly responses are imprecise because survey timing begins well after rollout for some outcomes.", s["body"]),
            p("AI use and human responsibility", s["h2"]),
            p(
                "AI assisted with requirement extraction, repository auditing, portability edits, "
                "table/figure generation, report drafting, and validation planning. Every empirical "
                "claim in this report was checked against the named paper, appendix, code, logs, or "
                "aggregate output. Suggestions that would have mislabeled three-draw inference, "
                "claimed a complete Stata run, or treated a third-party reanalysis as the student's "
                "own extension were rejected. Full details appear in AI_USE_DISCLOSURE.md.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("11. Conclusion", s["h1"]),
            p(
                "The selected replication supports the paper's headline result in a carefully bounded "
                "sense. Table V point estimates are reproduced to numerical precision, and a validated "
                "2,000-draw wild-cluster accelerator closely reconciles the reported uncertainty. The "
                "expenditure multiplier is about 2.58, the income multiplier about 2.47, and their "
                "average about 2.52. The evidence is strong that the local response is positive; the "
                "one-sided evidence that the multiplier exceeds one is suggestive rather than decisive.",
                s["body"],
            ),
            p(
                "The rollout/exposure extension adds a design insight. Within subcounty, start timing is "
                "not detectably associated with the tested village characteristics, but simplified "
                "direct-only and pure-control exposure cells are extremely thin and disappear at broader "
                "radii. This supports the paper's use of randomized saturation and continuous nearby "
                "transfer exposure while warning against unsupported binary comparisons.",
                s["body"],
            ),
            p(
                "The main remaining decision is administrative rather than computational: instructor "
                "approval is required because Egger et al. is an alternative paper. Subject to that "
                "approval, the repository now matches the requested submission structure and states its "
                "replication boundary honestly.",
                s["callout"],
            ),
            p("References", s["h2"]),
            p(
                "Egger, D., Haushofer, J., Miguel, E., Niehaus, P., and Walker, M. (2022). "
                "General Equilibrium Effects of Cash Transfers: Experimental Evidence From Kenya. "
                "<i>Econometrica</i>, 90(6), 2603-2643. https://doi.org/10.3982/ECTA17945.",
                s["body"],
            ),
            p(
                "Egger et al. Complete Appendices A-J (version dated 7 June 2022), especially "
                "Appendix A (design), Appendix C (MPC), and Appendix D (multiplier robustness).",
                s["body"],
            ),
            p("Rubric map", s["h2"]),
            course_table(
                [
                    ["Project criterion", "Report location"],
                    ["Understanding and motivation", "Sections 1-2"],
                    ["Data sources, sample, variables", "Section 3"],
                    ["Core replication and validation", "Sections 4-6"],
                    ["Independent extension", "Sections 7-8"],
                    ["Reproducibility/workflow", "Section 9 and repository"],
                    ["Limitations, AI disclosure, conclusion", "Sections 10-11 and AI_USE_DISCLOSURE.md"],
                ],
                [2.55 * inch, 4.25 * inch],
                font_size=8,
            ),
        ]
    )
    return story


def main() -> int:
    document = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        rightMargin=0.68 * inch,
        leftMargin=0.68 * inch,
        topMargin=0.68 * inch,
        bottomMargin=0.72 * inch,
        title="Cash Transfers and Local General Equilibrium",
        author="Zhenyu Yang",
        subject="ECON6067 Individual Final Project",
    )
    document.build(build_story(), onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
