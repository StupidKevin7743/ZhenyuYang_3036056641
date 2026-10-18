---
name: reproduce-cash-transfer-ge
description: Reproduce or audit the ECON6067 cash-transfer general-equilibrium project when asked to run, validate, or explain its Table V core replication, rollout-timing extension, exposure-support extension, inputs, or aggregate outputs.
---

# Cash-transfer GE reproduction

Run commands from the repository root. Read `config/project.json` and `config/input_manifest.json` before execution.

## Invariants

- Keep `do/global_runGPS.do` at `global runGPS = 0`. Stop if any active assignment sets it to 1.
- Never commit or print record-level inputs, identifiers, coordinates, credentials, or machine-local paths.
- Treat every data file as non-redistributable unless the provider explicitly says otherwise. A filename containing `PUBLIC` is not evidence of permission.
- Write only the canonical aggregate CSV and PNG outputs under `outputs/`.
- Describe the core as an accelerated Python reimplementation validated against Stata point estimates. Do not call it a completed direct Stata 2,000-draw run.
- Describe the extension as design and identification robustness, not an economic treatment-outcome estimate.

## Preflight

Run the data-free release check first:

```sh
python3 code/run_all.py --check-only
```

This validates privacy configuration, manifests, scripts, and committed aggregate artifacts without requiring private inputs or writing outputs. If all selected local inputs are present, it also validates the core Stata schemas before reporting success.

## Execute

With the seven inputs at their manifest defaults:

```sh
python3 code/run_all.py --target all
```

For inputs elsewhere, pass any or all of `--data`, `--estimates`, `--timing`, `--household`, `--village`, `--treatment-status`, and `--village-buffer`. Use `--target core` or `--target extension` to run only one component. `--output-dir` is the parent of the `tables/` and `figures/` directories.

## Verify

After execution, run `python3 code/run_all.py --check-only` again. Confirm that:

- Table V has 12 summary rows and point validation has 11 rows;
- the maximum absolute Python-versus-Stata point difference is no more than `1e-6`;
- probabilities lie in `[0, 1]`;
- extension tables are nonempty and contain aggregate fields only;
- both canonical PNG files have valid PNG signatures;
- no input or draw-level data were added to version control.

An all-target run produces one core target and one independent extension. Approval of the alternative paper, legal access to inputs, and final submission remain human gates.
