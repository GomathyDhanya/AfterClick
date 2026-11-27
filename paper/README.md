# Canonical paper

`main.tex` is the authoritative LaTeX manuscript **AfterClick: Beyond Action-Level Safety in Asynchronous AI Agents**, including its appendix. `AfterClick.pdf` is the current compiled manuscript. The supplied 17-page source/PDF and preceding versions are preserved through the archive index, not maintained as competing active papers.

From the repository root, install the locked research environment and run `bash scripts/build_paper.sh`. Tectonic is required; set `TECTONIC` to its executable path if necessary. `figures.py` reads hash-verified JSON/CSV evidence and generates eight figures, including the architecture schematic. `tables.py` generates all ten numerical tables, the claim registry and the claim/evidence matrix from the same source reports. Definition, hypothesis and readiness tables remain explanatory manuscript text. Figure coordinates, display ordering and labels are presentation constants, not empirical measurements.

`BUILD.json` records source and generated-table hashes. `claim_registry.json` binds claims to raw-report pointers and source hashes; `../evidence/index.json` is the single reader-facing evidence index. Full raw-data reproduction and exact frozen-source restoration are distinct procedures described in `../docs/REPRODUCIBILITY.md` and `../archive/README.md`.

The paper is a bounded analysis of an incomplete larger study. Original invalid and unexecuted outcomes, negative results and methodological limitations are preserved. Generating the paper makes no model calls and creates no cloud workloads. This is a conference-style working paper, not a venue-approved or peer-reviewed publication.
