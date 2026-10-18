# Local raw inputs

This directory is a local landing area for authorized source files. Research observations, identifiers, coordinates, archives, and credentials must not be committed. Obtain data only through the provider's current access process and comply with its terms.

The course extension expects these uncommitted files by default:

- `GE_Treat_Status_Master.dta`
- `VillageBuffers_GE_HHs_1km_Increments_PUBLIC.dta`

The word `PUBLIC` in a filename is not, by itself, permission to redistribute the file. The runner publishes only aggregate diagnostics and keeps `do/global_runGPS.do` at `runGPS = 0`.

For a nondefault location, pass `--treatment-status` or `--village-buffer` to `code/run_all.py`.
