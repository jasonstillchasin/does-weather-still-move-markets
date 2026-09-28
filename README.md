# Does the weather still move markets?

A pre-registered, two-hemisphere, post-publication test of weather and seasonal-mood effects in
US and Australian equities. The design is in `prereg/preregistration.md` (frozen in commit
80436d2, before any post-2003 regression); every later change is logged in
`prereg/deviations.md`.

## Reproduce

```bash
uv sync
make all
```

`make data` fetches ERA5 point series for 104 cities from the Copernicus Climate Data Store and
needs your own `~/.cdsapirc` plus the licence for `reanalysis-era5-single-levels-timeseries`
accepted. Everything else (Ken French, Yahoo, NOAA GHCNh/ISD-Lite, IEM METAR) downloads without
keys and is cached under `data/cache/` (git-ignored).

| Step | Script | Output |
|---|---|---|
| Replication gate (≤ 2000) | `s01_replicate` | `results/replication.*` |
| Primary tests H1–H6 + placebo | `s02_primary` | `results/primary.*`, `results/placebo.csv` |
| Romano–Wolf stepdown | `s05_romano_wolf` | `results/romano_wolf.json` |
| Exploratory robustness | `s03_robustness` | `results/robust_*`, `results/strategy.csv` |
| Figures | `s04_figures` | `paper/figs/` |
| Paper tables | `s06_tables` | `paper/tables/paper_*.tex` |
| Paper | `make paper` | `paper/main.pdf` |

## License

Code is released under the MIT License (see `LICENSE`). The raw data are not redistributed:
each source is downloaded by the scripts under its own terms (Ken French Data Library, Yahoo
Finance, NOAA GHCNh/ISD, Iowa Environmental Mesonet, and Copernicus ERA5, which requires
attribution).
