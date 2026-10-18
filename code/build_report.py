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

# Neutral tones throughout so the report remains clear when printed in black and white.
NAVY = colors.black
BLUE = colors.black
SKY = colors.HexColor("#F3F3F3")
INK = colors.black
MUTED = colors.HexColor("#444444")
LIGHT = colors.HexColor("#F5F5F5")
BORDER = colors.HexColor("#BBBBBB")
GOLD = colors.HexColor("#777777")
RED = colors.black


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
            spaceAfter=20,
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
            backColor=colors.white,
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


def report_figure(name: str, width: float = 6.85 * inch) -> Image:
    """Preserve the chart's aspect ratio, including its external legend."""
    chart = Image(str(FIGURE_DIR / name))
    # Force lazy image-size loading before setting drawing dimensions.
    aspect_ratio = chart.imageHeight / chart.imageWidth
    chart.drawWidth = width
    chart.drawHeight = width * aspect_ratio
    return chart


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
        textColor=colors.black,
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
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#E5E5E5")),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.black),
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
                "with an extension on payment timing and nearby treated villages",
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
                "Paper approval pending. Egger et al. is outside the four illustrative "
                "options in the project brief. Instructor approval is still required for "
                "this paper and the proposed replication scope.",
                s["warning"],
            ),
            Spacer(1, 0.18 * inch),
            p(
                "The repository includes the code, summary results, data-access instructions, "
                "and an AI-use disclosure. The research datasets and restricted coordinates "
                "must be obtained separately from an authorized source.",
                s["callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("1. Main findings", s["h1"]),
            p(
                "Does giving cash to poor households also raise incomes elsewhere in the local "
                "economy? Egger et al. (2022) study a one-time program that gave about USD 1,000 "
                "to each of more than 10,500 households in rural Kenya. Treatment was randomized "
                "across a study area of 653 villages. The paper reports that each dollar transferred "
                "generated about USD 2.50 of additional local economic activity, with little "
                "price inflation. This project checks the multiplier estimates in Table V; it "
                "does not independently re-estimate the paper's price effects.",
                s["body"],
            ),
            p(
                "The replication gives an expenditure multiplier of <b>2.58</b> and an income "
                "multiplier of <b>2.47</b>, matching the paper after rounding. Their average is "
                "<b>2.52</b>. Across all 11 table quantities, the largest difference between the "
                "Python and saved Stata estimates is less than 0.0000002. A completed 2,000-draw "
                "Python bootstrap gives similar, though slightly larger, standard errors. The "
                "estimates support a positive local response, but the evidence that the multiplier "
                "exceeds one is weaker.",
                s["body"],
            ),
            p(
                "The extension checks two practical questions: did some types of village start "
                "receiving payments earlier, and are there enough villages without nearby treatment "
                "to make simple comparisons? Within subcounties, the timing regression detects no "
                "clear association with the three measured village characteristics. At 2 km, "
                "however, only <b>five of 653 villages</b> have no treated neighbor; at 3 km and "
                "4 km, none do. Simple comparisons of four treatment/exposure groups would therefore "
                "rely on very small or empty groups.",
                s["body"],
            ),
            p("Scope and evidence", s["h2"]),
            bullet("Core: Table V estimates, their components, and a comparison of bootstrap uncertainty.", s["body"]),
            bullet("Extension: descriptive checks of payment timing and village exposure groups.", s["body"]),
            bullet("Implementation: completed Python computation checked against Stata point estimates; the direct 2,000-draw Stata run remained incomplete.", s["body"]),
            p(
                "These findings concern the selected table and extension. They do not certify "
                "every result in the article or establish a new causal effect from the extension.",
                s["callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("2. Research question and economic mechanism", s["h1"]),
            p(
                "When a household receives cash, it may buy food from a local shop, pay a builder, "
                "or purchase farm inputs. Those sellers earn income and may spend some of it locally. "
                "People who never received a transfer can therefore benefit too. The research "
                "question is how much additional spending and income this process creates across "
                "the study area. These wider effects are what the paper calls local "
                "general-equilibrium effects.",
                s["body"],
            ),
            p(
                "The <b>transfer multiplier</b> is the extra local economic activity divided by the "
                "cash transferred. A value of 2.5 means that USD 100 transferred is associated with "
                "an estimated USD 250 increase in activity over the measured period. It does not mean "
                "that each recipient receives another USD 250 in cash. The estimate covers recipients, "
                "other households, and firms, using the paper's expenditure or income accounting.",
                s["body"],
            ),
            p("Why Table V", s["h2"]),
            p(
                "Table V brings the results together in two ways: it adds extra household spending "
                "and business investment, and it separately adds extra wages, profits, capital income, "
                "and taxes. These are two measures of the same broad response, so they should not be "
                "added together. Their average is a third summary. The paper's Figure 1 shows the "
                "quarterly paths; this project reproduces Table V and uses Figure 1 only as context.",
                s["body"],
            ),
            p("Why the size of the effect is uncertain", s["h2"]),
            course_table(
                [
                    ["Economic channel", "What it means for the multiplier"],
                    ["Spending circulates locally", "A shopkeeper or worker can spend new income again, spreading gains beyond recipients."],
                    ["Firms can produce more", "Unused capacity can allow higher sales and output without equally large price increases."],
                    ["Purchases leave the area", "Imports and spending elsewhere can reduce the local response."],
                    ["The response takes time", "Adding effects across 29 months captures more than a single survey-date comparison."],
                ],
                [2.15 * inch, 4.65 * inch],
                font_size=8.2,
            ),
            Spacer(1, 0.12 * inch),
            p(
                "The extension asks whether the data provide useful comparisons for studying these "
                "effects. A village receiving no cash may still have treated neighbors, so it is "
                "not automatically an unaffected comparison village.",
                s["callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("3. Data, sample, and experimental design", s["h1"]),
            p(
                "The study includes 653 villages in 84 sublocations, with 328 villages assigned "
                "to treatment and 325 to control. Randomization occurred in two stages. First, "
                "sublocations or groups of sublocations were assigned to 33 high-saturation and "
                "35 low-saturation groups. Then two-thirds of villages in the high groups and "
                "one-third in the low groups were assigned to treatment. This created random "
                "variation in both a village's own treatment and treatment nearby.",
                s["body"],
            ),
            p(
                "Households living under thatched roofs were eligible. In treated villages, eligible "
                "households received KES 87,000: KES 7,000 initially, KES 40,000 two months later, "
                "and KES 40,000 eight months after the first payment. The census covers 65,383 "
                "households. Baseline and endline surveys cover 7,845 and 8,239 households; these "
                "are study-wide survey counts, not the sample size of every Table V regression. "
                "The median endline interview was 19 months after experimental start. Enterprise "
                "and market surveys supply business and price measures.",
                s["body"],
            ),
            p("Inputs used by this package", s["h2"]),
            course_table(
                [
                    ["Logical input", "Role", "Public-repository treatment"],
                    ["Household/enterprise multiplier file", "Spending and income components for Table V", "Access instructions only; never committed"],
                    ["Stata multiplier estimate file", "Point-estimate cross-check", "Generated/authorized local input; never committed"],
                    ["Experimental timing panel", "Actual rollout month", "Access instructions only; never committed"],
                    ["Household/village analysis files", "Endline-weighted size proxy, eligibility, treatment", "Access instructions only; never committed"],
                    ["Provider-supplied village-buffer file", "Counts of nearby treated villages", "No coordinates committed; input remains untracked"],
                ],
                [1.7 * inch, 2.4 * inch, 2.7 * inch],
                font_size=7.4,
            ),
            p("Data access and scope", s["h2"]),
            p(
                "The repository distributes summary tables, figures, and this report; it does not "
                "distribute research observations or coordinates. The input manifest lists the seven "
                "required files. The project starts from prepared analysis files, because the "
                "earlier raw-data construction code contains record-specific material and is excluded. "
                "Restricted-GPS analyses elsewhere in the paper remain outside this project's scope.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("4. Identification and replication method", s["h1"]),
            p(
                "A simple comparison of recipients and nonrecipients would miss gains reaching "
                "nearby households and firms. Equation (7) in the paper therefore relates each "
                "outcome to transfers paid in the village and within 2 km of it, in the current "
                "quarter and each of the previous nine quarters. The explanatory variables are "
                "quarter-specific transfer amounts, not cumulative transfers to date.",
                s["body"],
            ),
            p(
                "The instrumental-variables (IV) design uses randomized assignment and rollout "
                "to isolate transfer variation that is not chosen in response to local outcomes. "
                "The paper then adds the estimated spending and income responses over 29 months. "
                "Durable assets and inventories are measured as stocks at endline. Prices and "
                "transfers are converted to January 2015 values, so the calculation is in real terms.",
                s["body"],
            ),
            p("Core workflow", s["h2"]),
            course_table(
                [
                    ["Stage", "Implementation", "Validation"],
                    ["1. Estimate", "Compute each spending and income component in Python", "Compare 11 quantities with saved Stata estimates"],
                    ["2. Measure uncertainty", "Run 2,000 wild-cluster bootstrap draws", "Use seed 12345 and common signs within sublocations"],
                    ["3. Compare", "Calculate totals, averages, and bootstrap tail frequencies", "Show differences from published Table V"],
                    ["4. Present", "Generate summary tables and figures directly from code", "Check numbers and inspect rendered pages"],
                ],
                [1.3 * inch, 3.0 * inch, 2.5 * inch],
                font_size=7.7,
            ),
            p("Inference", s["h2"]),
            p(
                "The wild-cluster bootstrap repeats the calculation after multiplying regression "
                "residuals by random +1 or -1 signs, using the same sign for observations in a "
                "sublocation. Each artificial outcome combines the fitted value with the signed "
                "residual. The spread across 2,000 draws gives the bootstrap standard error. "
                "Following the supplied code, the reported one-sided quantities are the shares of "
                "draws below zero or one. They are not probabilities that a hypothesis is true.",
                s["body"],
            ),
            p("Numerical comparison rule", s["h2"]),
            p(
                "The point-estimate tolerance is 0.000001. Matching those estimates checks the "
                "coefficient calculations; it does not prove that the whole bootstrap is identical "
                "to Stata. Standard errors and tail frequencies are therefore compared separately "
                "with the paper, and the differences remain visible in the results.",
                s["callout"],
            ),
            p("Why not use the earlier three-draw result?", s["h2"]),
            p(
                "Three draws can produce only very coarse tail frequencies and unstable standard "
                "errors. The earlier run shows that the code executed, but it is unsuitable for "
                "final inference. This report uses the completed 2,000-draw Python results.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    key_rows = {row["row"]: row for row in comparison}
    full_table_rows: list[list[object]] = [["Component", "Paper", "Python", "Paper SE", "Python SE", "Below 0", "Below 1"]]
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
                f"{float(row['replicated_p_m_lt_0']):.4f}",
                f"{float(row['replicated_p_m_lt_1']):.4f}" if row["replicated_p_m_lt_1"] else "-",
            ]
        )
    story.extend(
        [
            p("5. Core replication results", s["h1"]),
            p(
                "All 11 point estimates match the paper to two decimal places. The expenditure "
                "multiplier is 2.5767, income is 2.4691, and their average is 2.5229. Their "
                "bootstrap standard errors are 1.4575, 1.7874, and 1.4278, respectively: slightly "
                "larger than the paper's 1.44, 1.71, and 1.39. Thus, the central estimates are very "
                "close, while the uncertainty estimates are similar rather than identical.",
                s["body"],
            ),
            course_table(
                full_table_rows,
                [2.12 * inch, 0.65 * inch, 0.65 * inch, 0.75 * inch, 0.75 * inch, 0.94 * inch, 0.94 * inch],
                font_size=7.8,
            ),
            p(
                "Table 1. Published Table V and Python results. SE = bootstrap standard error. "
                "The last two columns are the fractions of bootstrap draws below 0 and 1, using "
                "the supplied code's convention. A dash indicates an unreported component-level "
                "test. A displayed 0.0000 means no draw fell below the threshold, not zero true probability.",
                s["caption"],
            ),
            p("Interpretation", s["h2"]),
            p(
                "The point estimates are economically large, but they are imprecise. For expenditure, "
                "3.05% of bootstrap draws fall below zero and 14.55% below one; for income, the "
                "corresponding shares are 8.60% and 21.05%. The shares in which <b>both</b> "
                "multipliers fall below the threshold are 1.30% for zero and 7.85% for one. These "
                "are the code's joint-tail measures. Under the paper's reporting convention, the "
                "evidence for a positive response is stronger than the evidence for a multiplier above one.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("6. How closely do the results match?", s["h1"]),
            report_figure("table5_multiplier_comparison.png"),
            p(
                "Report Figure 1. Published and Python Table V estimates. Each horizontal line extends "
                "one standard error either side of its point estimate; these are not 95% confidence "
                "intervals. Marker shapes distinguish the series in black-and-white print.",
                s["caption"],
            ),
            p("Point-estimate cross-check", s["h2"]),
            p(
                f"Across {len(validation)} quantities, the largest absolute difference between "
                "Python and saved Stata point estimates is 0.00000017844. This is below the "
                "0.000001 tolerance. The two implementations therefore give effectively the same "
                "central estimates at the precision reported in the paper.",
                s["body"],
            ),
            p("Why some uncertainty estimates differ", s["h2"]),
            p(
                "The Python and published standard errors differ slightly. Different random-number "
                "streams and numerical routines may contribute, but this project has not isolated "
                "the exact source of each difference. One supplied-code behavior is retained: the "
                "untreated-household asset coefficient is held fixed during resampling. This is "
                "documented for reproducibility, not endorsed as the only valid choice. A completed "
                "original-code Stata bootstrap would provide a stronger comparison.",
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
                    {"log weighted village households": "Log of weighted village size",
                     "eligible share": "Eligible-household share",
                     "high saturation": "High-saturation assignment"}[variable],
                    f"{float(row['coefficient']):.3f}",
                    f"{float(row['standard_error']):.3f}",
                    f"{float(row['p_value']):.3f}",
                ]
            )
    cell_lookup = {(int(row["radius_km"]), row["cell"]): int(row["village_count"]) for row in cells}
    story.extend(
        [
            p("7. Extension: timing and comparison groups", s["h1"]),
            p(
                "<b>Did some types of village receive payments earlier?</b> The first check relates "
                "the start month to village size, the share of eligible households, and high-saturation "
                "assignment. It controls for average timing differences between subcounties, so the "
                "comparison is within each subcounty. Standard errors allow errors to be correlated "
                "within sublocations. Village size and eligibility shares use endline household "
                "weights: this is a descriptive timing check, not a baseline balance test.",
                s["body"],
            ),
            p(
                "Start is measured in two ways: the first month with an initial KES 7,000 payment, "
                "and the first month when cumulative initial payments reach 10% of the village's "
                "total initial payments. Coefficients are in months; positive values indicate later starts.",
                s["body"],
            ),
            course_table(timing_rows, [1.0 * inch, 2.55 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch], font_size=7.4),
            p(
                "Table 2. Timing diagnostics: 328 treated villages and 80 sublocation clusters. "
                "Subcounty indicators are included. SEs are cluster-adjusted; p-values use a "
                "two-sided normal approximation. The eligible share is measured from 0 to 1.",
                s["caption"],
            ),
            p("Timing result", s["h2"]),
            p(
                "None of the three characteristics has a statistically detectable association with "
                "start month in either specification. For example, high-saturation assignment is "
                "associated with a 0.168-month later first payment (SE 0.286; p = 0.557). This is "
                "consistent with little association in these data, but a nonsignificant result "
                "does not establish that actual payment timing is random.",
                s["body"],
            ),
            p("Which comparison groups exist?", s["h2"]),
            p(
                "The second check separates own-village treatment from the presence of at least "
                "one other treated village nearby. The labels describe assignment and proximity; "
                "they do not prove that an economic spillover occurred.",
                s["body"],
            ),
            course_table(
                [["Own village", "Treated neighbor?", "2 km", "3 km", "4 km"]] + [
                    [own, nearby] + [cell_lookup.get((radius, cell), 0) for radius in (2, 3, 4)]
                    for own, nearby, cell in (
                        ("Treated", "No", "direct only"),
                        ("Treated", "Yes", "direct+indirect"),
                        ("Control", "No", "pure control"),
                        ("Control", "Yes", "spillover only"),
                    )
                ],
                [1.5 * inch, 2.3 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch],
                font_size=8,
            ),
            p("Table 3. Village counts. Each radius includes the same 653 villages; the focal village is excluded from its own neighbor count.", s["caption"]),
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
            p("8. Why nearby treatment matters", s["h1"]),
            report_figure("extension_exposure_cells.png"),
            p(
                "Figure 2. Treatment and nearby-treatment groups. Each bar contains all 653 villages. "
                "The very small groups retain their true scale; exact counts are in Table 3 and below the chart.",
                s["caption"],
            ),
            p("Almost every village has a treated neighbor", s["h2"]),
            p(
                f"At 2 km, villages have an average of {float(neighbor_2km['mean_nearby_villages']):.2f} "
                "neighbors. Only one treated village and four control villages have no treated "
                "neighbor. These two groups account for just "
                f"{100 * hh_2km.get('direct only', 0) / total_hh:.1f}% and "
                f"{100 * hh_2km.get('pure control', 0) / total_hh:.1f}% of weighted households. "
                "At 3 km and 4 km, every village has a treated neighbor.",
                s["body"],
            ),
            p(
                "An average based on one or four villages would be sensitive to those particular "
                "villages. Empty groups cannot be compared at all. This explains the difficulty of "
                "a simple four-group analysis and the value of examining <b>how much</b> cash was "
                "transferred nearby. The counts do not, by themselves, validate the paper's instruments "
                "or show that spillovers caused an outcome change.",
                s["body"],
            ),
            p("Limits of the extension", s["h2"]),
            p("Payment timing is monthly, the regressions cover only three characteristics, and the exposure groups reduce nearby transfers to yes/no categories. These checks describe the data and comparison groups; they do not estimate a new causal effect.", s["body"]),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("9. Reproducibility package", s["h1"]),
            p(
                "The repository keeps the original Stata/R analysis code and adds a Python workflow "
                "for this project's results. Install the dependencies in requirements.txt and place "
                "the seven authorized input files at the paths listed in config/input_manifest.json. "
                "Then run <b>python3 code/run_all.py --target all</b> from the repository root to "
                "regenerate the tables and figures. Input paths can also be supplied explicitly.",
                s["body"],
            ),
            p("Package map", s["h2"]),
            course_table(
                [
                    ["Path", "Purpose"],
                    ["code/run_all.py", "Run the core and extension; check expected inputs and outputs"],
                    ["code/table5_multiplier_bootstrap.py", "Table V point estimates and 2,000-draw Python bootstrap"],
                    ["code/extension_timing_exposure.py", "Timing regression, village-group counts, and exposure chart"],
                    ["code/render_figures.py", "Table V comparison chart from summary CSVs"],
                    ["code/build_report.py", "Build report.pdf from the summary tables and figures; requires ReportLab"],
                    ["config/", "Project status, input contract, and published benchmarks"],
                    ["data/raw/ and data/processed/", "README access instructions only; inputs remain untracked"],
                    ["outputs/tables/ and outputs/figures/", "Summary results used by this report"],
                    ["skills/SKILL.md", "Reusable instructions for running and checking the project"],
                    ["AI_USE_DISCLOSURE.md", "Stage-by-stage AI assistance and human verification"],
                ],
                [2.3 * inch, 4.5 * inch],
                font_size=7.6,
            ),
            p("How to check the package", s["h2"]),
            p(
                "Run <b>python3 code/run_all.py --check-only</b> to check the public files without "
                "estimating the models. The full computation fixes the bootstrap at 2,000 draws "
                "and seed 12345. The release validator checks that only the approved summary "
                "outputs are included. It does not replace numerical or visual review. The PDF "
                "is built separately using <b>python3 code/build_report.py</b>.",
                s["body"],
            ),
            p(
                "The full project workflow completed using the existing local analysis files. "
                "Reproducing the numbers on another machine still requires authorized access to "
                "those inputs. A fresh-machine run of the full original article has not been completed.",
                s["callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("10. Validation, limitations, and AI use", s["h1"]),
            p("Validation completed", s["h2"]),
            bullet("The source paper and appendix were checked against their contents, including Table V and the experimental design.", s["body"]),
            bullet("The core computation used 2,000 draws and seed 12345. Its summary has 11 estimate rows and one joint-tail row.", s["body"]),
            bullet("All 11 Python point estimates agree with the saved Stata estimates within 0.000001.", s["body"]),
            bullet("The timing and village-group results agree with the earlier local analysis. The final editorial revision leaves the numerical CSVs unchanged.", s["body"]),
            bullet("Tables, charts, and the rendered PDF were checked for numerical consistency, readable labels, and page layout.", s["body"]),
            p("Substantive limitations", s["h2"]),
            bullet("The direct 2,000-draw Stata loop remained incomplete. Point-estimate agreement does not establish exact equivalence of every bootstrap step.", s["body"]),
            bullet("The supplied code holds one untreated-household asset coefficient fixed during resampling. This behavior is retained and should be tested in further work.", s["body"]),
            bullet("Household surveys begin about nine months after rollout and enterprise surveys about 18 months after rollout. Early quarterly responses are therefore less precisely estimated.", s["body"]),
            bullet("The multiplier depends on the paper's accounting and horizon. Imports, asset depreciation, and activity outside the study area limit its interpretation as a full welfare or national-GDP effect.", s["body"]),
            bullet("The village-size and eligibility covariates use endline weights, and the exposure groups simplify continuous transfer amounts. Neither extension check establishes a new causal effect.", s["body"]),
            bullet("Restricted-GPS analyses and other article exhibits are outside the project scope. Alternative-paper approval remains pending.", s["body"]),
            p("AI use and human responsibility", s["h2"]),
            p(
                "OpenAI Codex assisted with reading the instructions, organizing the repository, "
                "implementing and checking Python code, drafting the report, and revising its text "
                "and figures. Source material and machine-generated results provide the evidence. "
                "The student remains responsible for reviewing the methods, explaining the results, "
                "and deciding what to submit. AI_USE_DISCLOSURE.md gives the full account.",
                s["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("11. Conclusion", s["h1"]),
            p(
                "The replication gives an expenditure multiplier of 2.58 and an income multiplier "
                "of 2.47, matching the published figures after rounding. They suggest that one dollar "
                "transferred generated about USD 2.50 of additional local economic activity over the "
                "measured period. The estimates remain uncertain: the results support a positive "
                "response more clearly than they establish a multiplier above one.",
                s["body"],
            ),
            p(
                "The extension shows why a simple treated-versus-control comparison can be misleading "
                "in this setting. Almost every village has a treated neighbor. At 2 km, only one "
                "treated village and four control villages have no treated neighbor; at 3 km and "
                "4 km, none do. Comparisons built around these tiny groups would be unreliable. "
                "The counts help explain the paper's use of nearby transfer amounts, while leaving "
                "the causal effect of those transfers to the original IV design.",
                s["body"],
            ),
            p(
                "The contribution is a transparent check of Table V and a practical diagnosis of "
                "the comparison groups. The remaining substantive work is to compare a completed "
                "Stata bootstrap and test the retained resampling choice. Instructor approval is "
                "also required before using this alternative paper for the final submission.",
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
                "Egger et al. Complete Appendices A-J (7 June 2022): Appendix A for the design "
                "and Appendix D for multiplier sensitivity. Main-paper references: Section 2 "
                "for randomization, Section 3.8 and Equation (7) for dynamics, and Table V "
                "and Section 5 for the multiplier and its limitations.",
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
