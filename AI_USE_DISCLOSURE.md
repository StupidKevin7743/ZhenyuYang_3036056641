# AI Use Disclosure

## Project and student

- Student: Zhenyu Yang
- University number: 3036056641
- Project: replication and extension of Egger et al. (2022), *General Equilibrium Effects of Cash Transfers: Experimental Evidence From Kenya*

## How AI was used

OpenAI Codex was used on 18 October 2026 as a repository and writing assistant. Its material contributions were:

1. inspecting the course instructions, reference-repository structure, and the existing public code package;
2. auditing file organization, documented dependencies, privacy controls, reproducibility claims, and gaps against the course format;
3. drafting the course-facing README, contribution statement, submission checklist, and continuous-integration checks;
4. helping design, implement, and test Python code for the Table V reimplementation, the rollout/exposure extension, the one-command runner, validation, figures, and report assembly; and
5. checking documentation, configuration, and aggregate output consistency.

AI-generated text and code are not treated as evidence. Zhenyu Yang remains responsible for reviewing every change, running the final workflow with authorized inputs, checking every reported number against machine-generated outputs, interpreting the economics, and deciding what to submit.

## Boundaries, limitations, and rejected claims

- Codex ran the documented workflow against the user's local analysis files. It did not upload, commit, publish, or expose those inputs, identifiers, restricted coordinates, or credentials.
- Codex did not infer that an input labelled `PUBLIC` was safe to redistribute; public release still requires a human disclosure review.
- Codex did not verify instructor approval for this alternative paper. Approval is pending and must be documented separately.
- Codex did not certify an exact replication. At the time of this disclosure, no clean-machine end-to-end Stata run with the authorized inputs had been demonstrated in the public repository.
- Codex did not claim that clustered inference with `runGPS = 0` reproduces the article's restricted-coordinate spatial-HAC standard errors.
- Codex did not invent missing inputs, coefficients, standard errors, figures, or robustness findings. Missing prerequisites must make the workflow fail visibly.
- Codex did not determine that upstream code may be relicensed. The original authors and publisher retain their applicable rights.
- Codex did not submit the project or send the instructor email. Those actions remain under the student's control.

## Verification before submission

Before submission, the student will compare `report.pdf` against the committed tables and figures, review the Git diff, run the repository checks, confirm the cited commit, and update this disclosure if AI use expands materially.
