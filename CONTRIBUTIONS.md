# Contributions and Provenance

## Student project

Zhenyu Yang (university number 3036056641) is responsible for the course project built around this repository. The proposed scope is deliberately narrower than the full article:

- core replication: the transfer-multiplier results in Table V, with the paper's Figure 1 used only for dynamic context;
- extension: robustness to treatment rollout timing and local exposure definitions; and
- completed course work: portable execution, 2,000-draw numerical comparison, extension diagnostics, economic interpretation, and the report; and
- human gates still open: instructor approval, the student's final review, and the final submission decision.

The paper is an alternative project choice. Written instructor approval is pending; the repository does not imply that approval has been granted.

## Upstream research contribution

The empirical design, original analysis, and most Stata/R research programs derive from the supporting materials for:

> Egger, Dennis, Johannes Haushofer, Edward Miguel, Paul Niehaus, and Michael Walker. 2022. “General Equilibrium Effects of Cash Transfers: Experimental Evidence From Kenya.” *Econometrica* 90 (6): 2603–2643. <https://doi.org/10.3982/ECTA17945>.

The article's authors—not the student—created the underlying study, data, estimands, and original replication code. The repository is an independent course-oriented organization of those materials and is not endorsed by the authors or publisher. See `NOTICE.md`, `CITATION.cff`, and `THIRD_PARTY_NOTICES.md` for rights and dependency details.

## Course-specific work

The course layer prepared by Zhenyu Yang with disclosed AI assistance consists of repository organization, portable execution and validation tooling, a focused Table V comparison, the rollout/exposure robustness design, course documentation, and disclosure-safe output packaging. The course comparison figure is not the paper's Figure 1. Files should not be described as independently authored by the student when they retain upstream code.

The extension module is `code/extension_timing_exposure.py`. Its outputs must be interpreted as a student extension, not as results reported by Egger et al. (2022).

## AI contribution

OpenAI Codex assisted with repository inspection, documentation, Python workflow and extension implementation, validation, figure generation, report assembly, and aggregate-artifact checks on 18 October 2026. It did not supply the research data, instructor approval, or empirical evidence. The precise scope and limitations are recorded in `AI_USE_DISCLOSURE.md`.
