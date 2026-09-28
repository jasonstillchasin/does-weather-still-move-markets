.PHONY: all test data replicate primary robust figures tables paper study2

all: test replicate primary robust figures tables study2 paper

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

# Study 2: 26 further exchanges, seven ERA5 weather variables (needs ~/.cdsapirc).
study2:
	uv run python -m weather.studies.s10_fetch_era5_full
	uv run python -W ignore -m weather.studies.s11_study2
	uv run python -W ignore -m weather.studies.s12_study2_secondary
	uv run python -m weather.studies.s13_study2_report
