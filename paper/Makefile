# Build the NehiyoMTB paper end to end:  make
#
#   make figures   regenerate figures, tables and number macros from the repo
#   make shots     re-take the website/app screenshots (needs Node + Playwright)
#   make pdf       assemble build/tex and compile nehiyomtb-paper.pdf
#   make clean     remove build/
#
# Requirements: python3 with paper/requirements.txt, a TeX Live with latexmk,
# and the Noto Sans Canadian Aboriginal font (fonts-noto-core on Debian/Ubuntu).

PY      ?= python3
SCRIPTS := scripts
BUILD   := build

.PHONY: all figures shots pdf clean

all: figures shots pdf

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
