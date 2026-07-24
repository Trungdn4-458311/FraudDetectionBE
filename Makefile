# Build the graded artifacts.
#   make notebook   # Restart & Run All (pixi)         -> executes fraud_eda.ipynb, refreshes figures
#   make monitor    # Module 7 monitoring report (pixi) -> monitoring/monitoring_report.html
#   make report     # report/main.pdf   (docker TeX Live)
#   make slides     # slides/main.pdf    (docker TeX Live)
#   make pptx       # slides/main.pptx   (pixi; needs slides.pdf)
#   make all        # notebook -> monitor -> report -> slides -> pptx
#
# LaTeX runs in a full TeX Live docker image pulled from ghcr.io (registry-independent:
# docker.io is unreachable from this host). Python steps run in the pixi env.

TEX_IMG := ghcr.io/xu-cheng/texlive-full:latest
TEXRUN  := docker run --rm -u $(shell id -u):$(shell id -g) -e HOME=/tmp \
           -v "$(CURDIR)":/w
PIXI    := pixi run

.PHONY: all notebook monitor report slides pptx clean

all: notebook monitor report slides pptx

notebook:
	$(PIXI) notebook

monitor:
	$(PIXI) monitor

report:
	$(TEXRUN) -w /w/report $(TEX_IMG) latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

slides:
	$(TEXRUN) -w /w/slides $(TEX_IMG) latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

pptx: slides
	$(PIXI) slides-to-pptx

clean:
	$(TEXRUN) -w /w/report $(TEX_IMG) latexmk -C || true
	$(TEXRUN) -w /w/slides $(TEX_IMG) latexmk -C || true
