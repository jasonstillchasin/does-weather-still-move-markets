.PHONY: all test data replicate primary robust figures tables paper

all: test replicate primary robust figures tables paper

test:
	uv run pytest -q

# ERA5 for 104 cities from Copernicus CDS; needs ~/.cdsapirc and the dataset licence accepted.
data:
	uv run python -m weather.studies.s00_fetch_era5

replicate:
	uv run python -m weather.studies.s01_replicate

primary: data
	uv run python -W ignore -m weather.studies.s02_primary
	uv run python -W ignore -m weather.studies.s05_romano_wolf

robust: data
	uv run python -W ignore -m weather.studies.s03_robustness

figures: data
	uv run python -W ignore -m weather.studies.s04_figures

tables:
	uv run python -m weather.studies.s06_tables

paper:
	cd paper && pdflatex -interaction=nonstopmode main.tex >/dev/null && bibtex main >/dev/null && pdflatex -interaction=nonstopmode main.tex >/dev/null && pdflatex -interaction=nonstopmode main.tex >/dev/null
