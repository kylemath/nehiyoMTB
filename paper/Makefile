# Build the paper end to end:  make
#
#   make names     (default) the Names submission: Word files for blind review
#                  and after acceptance, PDF previews, figure files at the
#                  required resolution, supplementary CSVs -> names/submission/
#   make mdpi      the earlier MDPI Languages version (LaTeX -> nehiyomtb-paper.pdf)
#   make figures   regenerate figures, tables and number macros from the repo
#   make shots     re-take the website/app screenshots (needs Node + Playwright)
#   make pdf       assemble build/tex and compile nehiyomtb-paper.pdf
#   make clean     remove build/
#
# Requirements: python3 with paper/requirements.txt, pandoc (3.x) and LibreOffice
# for the Names version, a TeX Live with latexmk for the MDPI version,
# and the Noto Sans Canadian Aboriginal font (fonts-noto-core on Debian/Ubuntu).

PY      ?= python3
SCRIPTS := scripts
BUILD   := build

.PHONY: names mdpi all figures shots pdf clean

names:
	$(PY) names/build_names.py
	rm -rf names/submission && mkdir -p names/submission
	cp $(BUILD)/names/manuscript_anonymized.docx $(BUILD)/names/manuscript_anonymized.pdf \
	   $(BUILD)/names/manuscript_final.docx $(BUILD)/names/manuscript_final.pdf \
	   $(BUILD)/names/wordcount.txt names/submission/
	cp -r $(BUILD)/names/figures $(BUILD)/names/supplementary names/submission/
	@echo "wrote paper/names/submission/"

mdpi: figures shots pdf

all: names mdpi

figures:
	cd $(SCRIPTS) && $(PY) make_tables.py
	cd $(SCRIPTS) && $(PY) orthography.py
	cd $(SCRIPTS) && $(PY) fig_map.py
	cd $(SCRIPTS) && $(PY) fig_timeline.py
	cd $(SCRIPTS) && $(PY) fig_pipeline.py
	cd $(SCRIPTS) && $(PY) fig_gallery.py

# Falls back to the committed copies in figures/static/ when a browser is unavailable.
shots:
	cd $(SCRIPTS) && $(PY) fig_screenshots.py

pdf:
	cd $(SCRIPTS) && $(PY) build_tex.py
	cd $(BUILD)/tex && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
	cp $(BUILD)/tex/main.pdf nehiyomtb-paper.pdf
	@echo "wrote paper/nehiyomtb-paper.pdf"

clean:
	rm -rf $(BUILD)
