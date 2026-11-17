# The NehiyoMTB paper

`nehiyomtb-paper.pdf` is a descriptive academic paper about this project, built
entirely from the repository: every figure, table and number in it is produced
by the scripts in `scripts/` from `docs/catalogue.json`, the Translation
Workbench, the sign-factory manifest, the Supabase migrations, the photographs
and the Git history. When the project changes, rebuild the paper and it changes
with it.

## Build

```bash
cd paper
pip install -r requirements.txt
make            # figures + screenshots + PDF  ->  paper/nehiyomtb-paper.pdf
```

`make figures`, `make shots` and `make pdf` run the three stages on their own.
You need Python 3, a TeX Live with `latexmk` (pdfLaTeX), and the Noto Sans
Canadian Aboriginal font (`fonts-noto-core` on Debian/Ubuntu; on a Mac,
`brew install --cask font-noto-sans-canadian-aboriginal`). Screenshots need
Node with Playwright; without it, the committed copies in `figures/static/`
are used.

## How it fits together

| Script | Makes |
|---|---|
| `make_tables.py` | Table 1 (finished signs, with colour swatches), Table 3 (backend tables), catalogue counts |
| `orthography.py` | Figure 8 and Table 2: the SRO-vs-syllabics spelling audit, plus `build/generated/orthography_audit.csv` |
| `fig_map.py` | Figure 5 (trail map from the catalogue's GPS tracks) and Figure 10 (a Python port of the app's route builder) |
| `fig_timeline.py` | Figure 2 (project history from `git log`) |
| `fig_pipeline.py` | Figure 3 (how a trail name becomes a sign, page and app entry) |
| `fig_gallery.py` | Figure 1 (wall photo), Figures 6 and 7 (sign factory stages and drafts), generator counts |
| `fig_screenshots.py` + `screenshots.cjs` | Figures 4 and 9 (sign page and app, served from `docs/` with third-party requests blocked) |
| `build_tex.py` | Copies `tex/` to `build/tex/`, renders every run of Cree syllabics to a vector PDF and swaps in `\syl{...}` |

Numbers in the prose are LaTeX macros (for example `\catBuilt`,
`\orthWorkbenchMismatch`) written by the scripts to `build/generated/*.tex`, so
they never go stale. pdfLaTeX has no syllabics font, which is why
`build_tex.py` pre-renders syllabics: the journal recompiles with pdfLaTeX, and
this keeps the source in plain Unicode.

Edit the paper in `tex/main.tex` and `tex/references.bib`; never edit `build/`.

## Before submitting

- Orange **[k to supply: ...]** notes mark facts only the author can give
  (consultations with Elders and speakers, positionality, trail stakeholders,
  licence, ethics, how riders have responded). Set `\showtodosfalse` in
  `tex/main.tex` to hide them.
- `tex/Definitions/` is an older copy of MDPI's LaTeX class (2020, Apache-2.0
  via github.com/metaphori/Template-LaTeX-MDPI). Swap in the current template
  from https://www.mdpi.com/authors/latex before submitting; `main.tex`
  already uses the current back-matter commands.
- Every reference was checked against the publisher, ACL Anthology, a
  university repository or the issuing body in November 2026.

## Target journal: *Languages* (MDPI)

Recommended because the fit, speed and format all line up:

- **Fit.** *Languages* is an interdisciplinary, open-access linguistics journal
  that publishes work on language revitalization, writing systems and
  linguistic landscapes, so a descriptive project paper about Plains Cree
  signage, orthography and tools is in scope without having to be recast as an
  experiment.
- **Speed.** Median time to first decision about 57 days and about 11 days from
  acceptance to publication (journal page, first half of 2026).
- **Standing.** Indexed in Scopus, ESCI and ERIH Plus; 2025 impact factor 1.3
  (JCR Q2 Linguistics).
- **Cost.** APC of CHF 1,600 on acceptance. MDPI does not publish an
  acceptance rate for this journal, so "easy acceptance" cannot be confirmed;
  MDPI journals are generally faster and less selective than society journals.
- **Format.** Author–date (APA-like) references and a LaTeX template, which
  this pipeline uses.

If a free (no-APC) venue matters more than speed, *Language Documentation &
Conservation* (University of Hawai‘i, diamond open access) is the strongest
fit but is slower, more selective and Word-template based. The journal
*Linguistic Landscape* (John Benjamins) is the closest topical match but is
selective and slow.
