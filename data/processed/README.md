# Local prepared inputs

Place authorized prepared analysis files here for the documented defaults. These files remain uncommitted; the public repository contains code, an input manifest, and disclosure-safe aggregate outputs only.

Core replication defaults:

- `HH_ENT_Multiplier_Dataset_ECMA.dta`
- `multiplier_estimates.dta`

Extension defaults:

- `GE_experimental_timing_long_FINAL.dta`
- `GE_HHLevel_ECMA.dta`
- `GE_VillageLevel_ECMA.dta`

Use the corresponding explicit path options in `code/run_all.py` when the files live elsewhere. Do not place restricted GPS inputs here; the public workflow requires `runGPS = 0`.
