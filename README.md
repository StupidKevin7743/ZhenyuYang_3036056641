# Cash Transfers, Local Multipliers, and Exposure Robustness

**ECON6067 Quantitative Tools for Economics final-project draft for Zhenyu Yang (3036056641)**

**Submission repository:** <https://github.com/StupidKevin7743/ZhenyuYang_3036056641>

> **Approval gate:** Egger et al. (2022) is an alternative paper choice. Written instructor approval is pending. This repository documents preparation and results, but does not imply that approval has been granted.

## Project question and scope

This project asks whether a large randomized cash-transfer program generated local general-equilibrium expenditure and income multipliers in rural Kenya. It focuses on two linked exhibits from:

> Egger, Dennis, Johannes Haushofer, Edward Miguel, Paul Niehaus, and Michael Walker. 2022. “General Equilibrium Effects of Cash Transfers: Experimental Evidence From Kenya.” *Econometrica* 90 (6): 2603–2643. <https://doi.org/10.3982/ECTA17945>.

- **Core replication:** Table V multiplier components and their cumulative-multiplier interpretation in Figure 1. The course comparison figure does not recreate the published Figure 1 graphic.
- **Student extension:** diagnostics for rollout timing and for the support of local treatment-exposure cells at 2, 3, and 4 km, implemented in `code/extension_timing_exposure.py`.

The extension is descriptive. It tests whether rollout timing is predictably related to observed village characteristics and shows how radius choices change exposure-cell support. It is not a new causal treatment-effect estimate.

## Main reproducibility result

The course package reconciles a custom 2,000-draw Python reimplementation with the article and with Stata point estimates:

| Multiplier | Reimplementation | Bootstrap SE | Published | Published SE |
|---|---:|---:|---:|---:|
| Expenditure | 2.5767 | 1.4575 | 2.58 | 1.44 |
| Income | 2.4691 | 1.7874 | 2.47 | 1.71 |
| Average | 2.5229 | 1.4278 | 2.52 | 1.39 |

Across the 11 Table V quantities, the largest absolute difference between Python and the saved Stata point estimates is `1.7844e-7`. The 2,000-draw joint p-values are 0.0130 against zero and 0.0785 against one. These results closely reproduce the printed benchmark after rounding.

This must be described accurately: the paper-scale inference is a validated matrix-based Python reimplementation, not a completed 2,000-replication Stata run. The available direct Stata run stopped at roughly 50 draws; the older completed Stata output used only three draws and is not paper-grade inference.

The extension finds no detectable conditional gradient in rollout timing with log weighted households, eligible share, or high-saturation assignment. At 2 km, exposure support is thin: 1 direct-only, 327 direct-plus-indirect, 4 pure-control, and 321 spillover-only villages. At 3 and 4 km, the direct-only and pure-control cells disappear. These are design diagnostics, not outcome effects.

## Repository layout

| Path | Role |
|---|---|
| `report.pdf` | Course report; every quantitative claim should trace to a committed aggregate output. |
| `code/run_all.py` | One-command course runner and data-free preflight. |
| `code/extension_timing_exposure.py` | Rollout-timing regression and exposure-support extension. |
| `code/` | Course-specific computation, figure, and report utilities. |
| `data/raw/` | Local authorized source inputs; never commit research observations. |
| `data/processed/` | Local prepared inputs; never commit research observations. |
| `outputs/tables/` | Disclosure-safe aggregate CSV outputs used by the report. |
| `outputs/figures/` | Figures generated from the aggregate tables. |
| `skills/SKILL.md` | Machine-readable execution contract for an AI reproducibility check. |
| `do/`, `ado/`, `scripts/` | Upstream Stata/R analysis code and portable legacy wrappers. |
| `AI_USE_DISCLOSURE.md` | Required account of AI assistance and limitations. |
| `CONTRIBUTIONS.md` | Separation of upstream, student, and AI contributions. |

## Data access and privacy

No research microdata, identifiers, restricted coordinates, raw archives, or record-level logs are distributed here. Obtain inputs only from an authorized source under the provider's current terms; the article page links its supporting information: <https://onlinelibrary.wiley.com/doi/10.3982/ECTA17945>.

Place authorized inputs under `data/raw/` or `data/processed/` and pass their paths explicitly to the runner. Do not commit them. Filenames such as `PUBLIC` are not proof that redistribution is permitted. See `DATA_AVAILABILITY.md` before handling any input.

Restricted GPS inputs are absent, and `do/global_runGPS.do` must remain at `runGPS = 0`. Applicable legacy analyses therefore use the documented clustered-inference path rather than the article's restricted-coordinate spatial-HAC path.

## Environment

The course runner requires Python 3 with the pinned NumPy, pandas, and Matplotlib versions in `requirements.txt`. The legacy workflow records Stata 15.1 and R 4.1.3; its Stata packages are installed from upstream and are not fully version-pinned. Run all commands from the repository root.

Install the course-runner dependencies:

```sh
python3 -m pip install -r requirements.txt
```

First perform the data-free contract check:

```sh
python3 code/run_all.py --check-only
```

## One-command reproduction

After placing the seven authorized inputs at the manifest defaults in `config/input_manifest.json`, run:

```sh
python3 code/run_all.py --target all
```

The equivalent fully explicit command is:

```sh
python3 code/run_all.py --target all --data data/processed/HH_ENT_Multiplier_Dataset_ECMA.dta --estimates data/processed/multiplier_estimates.dta --timing data/processed/GE_experimental_timing_long_FINAL.dta --household data/processed/GE_HHLevel_ECMA.dta --village data/processed/GE_VillageLevel_ECMA.dta --treatment-status data/raw/GE_Treat_Status_Master.dta --village-buffer data/raw/VillageBuffers_GE_HHs_1km_Increments_PUBLIC.dta --output-dir outputs
```

The runner must fail rather than fabricate an output when an input, expected schema, dependency, or privacy setting is missing. Exact input checks and expected outputs are also documented in `skills/SKILL.md`.

## Output manifest

All committed outputs are aggregate. They contain no record identifiers.

| Output | Meaning |
|---|---|
| `outputs/tables/table5_2000_bootstrap_summary.csv` | Table V point estimates, 2,000-draw standard errors, and tail probabilities. |
| `outputs/tables/table5_paper_comparison.csv` | Reimplementation-versus-published comparison. |
| `outputs/tables/table5_point_validation.csv` | Python-versus-Stata point-estimate validation. |
| `outputs/figures/table5_multiplier_comparison.png` | Course-facing comparison of Table V estimates and uncertainty; complements the Figure 1 discussion. |
| `outputs/tables/extension_timing_regression.csv` | Rollout-timing diagnostic with sublocation-clustered inference. |
| `outputs/tables/extension_exposure_cells.csv` | Village exposure-cell counts by radius. |
| `outputs/tables/extension_exposure_households.csv` | Weighted household support by eligibility, cell, and radius. |
| `outputs/tables/extension_neighbor_summary.csv` | Neighbor-count and treated-neighbor support diagnostics. |
| `outputs/figures/extension_exposure_cells.png` | Exposure-cell support at 2, 3, and 4 km. |

## Limits on the claim

- This is a focused Table V replication, Figure 1 interpretation, and extension—not a recreation of the published Figure 1 graphic or a certified reproduction of every article exhibit.
- The public package omits raw-data construction code containing record-level material, restricted GPS inputs, and manual GIS exhibits.
- The direct paper-scale Stata bootstrap remains incomplete; Python paper-scale inference is labelled as a reimplementation.
- The rollout data are monthly, and the exposure cells simplify the article's continuous-transfer IV design.
- A successful privacy or structure check is not proof of numerical replication. The report, CSVs, code, and exact submitted commit must agree.

For the full legacy execution notes, see `REPLICATION.md`; for the source-to-exhibit map, see `docs/EXHIBIT_MAP.md`; for unresolved risks, see `docs/CODE_AUDIT.md`.

## Attribution and rights

This is an independent course-oriented organization of code distributed with the publisher's supporting information. It is not an official repository of the article's authors or publisher. The original authors retain credit for the study and upstream research code; the student extension and packaging are described in `CONTRIBUTIONS.md`.

No new blanket open-source license is asserted over the upstream research code. Read `NOTICE.md`, `THIRD_PARTY_NOTICES.md`, and `CITATION.cff` before reuse or redistribution.
