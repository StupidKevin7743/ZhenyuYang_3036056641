# Notice

## Provenance

This repository began as an independent, privacy-screened, code-only organization of research code distributed with the publisher’s supporting information for:

> Egger, Dennis, Johannes Haushofer, Edward Miguel, Paul Niehaus, and Michael Walker. 2022. “General Equilibrium Effects of Cash Transfers: Experimental Evidence From Kenya.” *Econometrica* 90 (6): 2603–2643. <https://doi.org/10.3982/ECTA17945>.

The current ECON6067 course layer adds a focused Table V reimplementation, a
student-designed diagnostic extension, a report, and an exact allowlist of
aggregate tables and figures. It is not an official repository maintained by
the article’s authors or publisher. Organizational documentation, portable
wrappers, course code, and release checks should not be interpreted as author
or publisher endorsement.

## Rights

No blanket open-source license is asserted for the upstream research code or the publisher’s supporting materials. Their copyright and other rights remain with their respective rights holders. Third-party Stata dependencies are not vendored and retain their own upstream licenses. The included `renv` bootstrap is distributed under the MIT license reproduced in [LICENSES/renv-MIT.txt](LICENSES/renv-MIT.txt). Inclusion here does not expand the permissions granted by an upstream source, and this notice does not grant permission to redistribute data or restricted materials.

Users must determine whether their intended use, modification, or redistribution is permitted by the applicable upstream terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for dependency provenance notes.

## Data exclusion

No research microdata, source archives, raw-data construction programs
containing embedded record-level material, restricted GPS information,
draw-level results, or execution logs are intended to be part of this
repository. The only generated results included are the disclosure-reviewed,
aggregate course artifacts enumerated by exact path in `README.md` and
`tools/validate_release.py`. Data access and use remain subject to the
provider’s terms, research-ethics requirements, and any applicable
confidentiality restrictions. See [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md).

## Reproducibility status

The focused course workflow has been run locally from the documented prepared
inputs, and the public repository performs data-free structure, artifact, and
privacy checks. A complete clean-machine execution through every exhibit in the
article has not been verified. The absence of restricted GPS inputs means some
inferential results can differ from the published spatial-HAC specification.

No warranty is made that the code is error-free, complete for every exhibit, or suitable for a particular purpose. Scholarly users should document independent validation and cite the published article.
