"""Primary hypotheses H1-H6 (pre-registration sections 4-6).

Refuses to run unless prereg/preregistration.md is committed in git, so no post-2003 result
can be seen before the freeze.
"""

from __future__ import annotations

import subprocess
import sys

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from weather.data import returns
from weather.data.net import ROOT
from weather.data.placebo_cities import CITIES, PLACEBO_CITIES
from weather.data.weather_openmeteo import era5_daily
from weather.features.deseason import trailing_anomaly
from weather.models.regress import ols_coef
from weather.panel import CONTROLS, market_panel
from weather.studies.common import OUT, fmt_row, write_table


def prereg_is_frozen() -> bool:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--format=%H %cI", "--", "prereg/preregistration.md"],
        capture_output=True, text=True,
    )
    top = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True).stdout.strip()
    return out.returncode == 0 and bool(out.stdout.strip()) and top == str(ROOT)


# ---------------------------------------------------------------- specifications
# Each spec: (id, market, y, weather var, extra regressors, coefficient tested, direction)
# "W" in extra/tested is replaced by the weather column in use (station or placebo).

def _controls(market: str, y: str) -> list[str]:
    c = list(CONTROLS)
    if y != "r":
        c = [x for x in c if x not in ("lag1", "lag2")] + [f"{y}_lag1", f"{y}_lag2"]
    return c + (["r_us_prev"] if market == "AU" else [])


def _prepare(df: pd.DataFrame, w: str) -> pd.DataFrame:
    df = df.copy()
    df["W"] = df[w]
    df["W_pre"] = df["W"] * (1 - df["post"])
    df["W_post"] = df["W"] * df["post"]
    df["W_hybrid"] = df["W"] * df["hybrid"]
    return df


SPECS = [
    ("H1-US", "US", "r", "cloud_z", [], "W", -1),
    ("H1-AU", "AU", "r", "cloud_z", [], "W", -1),
    ("H2-US", "US", "r", "cloud_z", ["post", "W_pre"], "W_post", -1),
    ("H2-AU", "AU", "r", "cloud_z", ["post", "W_pre"], "W_post", -1),
    ("H3-AU", "AU", "r", None, ["sad", "fall", "sad_nyc", "fall_nyc"], "sad", 1),
    ("H4-US", "US", "r", "temp_z", [], "W", -1),
    ("H4-AU", "AU", "r", "temp_z", [], "W", -1),
    ("H5-US", "US", "r", "cloud_z", ["hybrid", "W"], "W_hybrid", 1),
    ("H6-US", "US", "smb10", "cloud_z", [], "W", -1),
]


def panels() -> dict[str, pd.DataFrame]:
    us = market_panel("US")
    smb = returns.us_small_minus_big()
    us["smb10"] = smb
    us["smb10_lag1"], us["smb10_lag2"] = smb.shift(1), smb.shift(2)
    return {"US": us, "AU": market_panel("AU")}


def estimate(df: pd.DataFrame, spec, wcol: str | None):
    sid, market, y, _, extra, tested, direction = spec
    d = _prepare(df, wcol) if wcol else df
    xs = [*extra, *(["W"] if wcol and "W" not in extra and tested == "W" else [])]
    if tested not in xs:
        xs.append(tested)
    xs += _controls(market, y)
    return ols_coef(d, y, xs, tested, direction)


# ---------------------------------------------------------------- placebo
def era5_anomalies(name: str, lat: float, lon: float, tz: str) -> pd.DataFrame:
    d = era5_daily(name, lat, lon, tz)
    return pd.DataFrame({"cloud_z": trailing_anomaly(d["cloud"].rename("c")),
                         "temp_z": trailing_anomaly(d["temp"].rename("t"))})


def placebo_percentiles(p: dict[str, pd.DataFrame]) -> list[dict]:
    home = {"US": "NYC", "AU": "SYD"}
    placebo_w = {c[0]: era5_anomalies(*c) for c in PLACEBO_CITIES}
    rows = []
    for spec in SPECS:
        sid, market, y, wvar, _, _, direction = spec
        if wvar is None:
            continue
        base = p[market].drop(columns=["cloud_z", "temp_z"])
        real = era5_anomalies(home[market], *CITIES[home[market]])
        b_real = estimate(base.join(real[[wvar]]), spec, wvar).coef
        b_station = estimate(p[market], spec, wvar).coef
        bs = np.array([estimate(base.join(w[[wvar]]), spec, wvar).coef
                       for w in placebo_w.values()])
        # Share of placebos at or beyond the real ERA5 beta in the predicted direction.
        pct_city = float(np.mean(direction * bs >= direction * b_real))
        # Year-shifted station weather, k = 1..30.
        station = p[market][[wvar]]
        shifted = []
        for k in range(1, 31):
            s = station.copy()
            s.index = s.index + pd.DateOffset(years=k)
            s = s[~s.index.duplicated()]
            shifted.append(estimate(base.join(s), spec, wvar).coef)
        shifted = np.array(shifted)
        pct_shift = float(np.mean(direction * shifted >= direction * b_station))
        rows.append(dict(test=sid, beta_era5=b_real, beta_station=b_station,
                         placebo_mean=float(bs.mean()), placebo_sd=float(bs.std(ddof=1)),
                         pct_city=pct_city, yearshift_mean=float(shifted.mean()),
                         pct_yearshift=pct_shift))
    return rows


def main() -> None:
    if not prereg_is_frozen():
        sys.exit("Pre-registration is not committed in this project's own git repo. "
                 "Commit prereg/preregistration.md first (see README).")
    p = panels()
    rows = []
    for spec in SPECS:
        e = estimate(p[spec[1]], spec, spec[3])
        pred = "<0" if spec[6] < 0 else ">0"
        rows.append(dict(test=spec[0], pred=pred, **vars(e)))
    holm = multipletests([r["p_one"] for r in rows], alpha=0.05, method="holm")
    for r, rej, padj in zip(rows, holm[0], holm[1], strict=True):
        r["p_holm"], r["holm_reject"] = float(padj), bool(rej)
    plac = {r["test"]: r for r in placebo_percentiles(p)}
    for r in rows:
        pl = plac.get(r["test"])
        r["pct_city"] = pl["pct_city"] if pl else None
        tail = pl is not None and pl["pct_city"] <= 0.05
        if pl is None:  # H3: no placebo defined for astronomical variables (deviation D4)
            r["verdict"] = "SUPPORTED" if r["holm_reject"] else "NOT SUPPORTED"
        elif r["holm_reject"] and tail:
            r["verdict"] = "SUPPORTED"
        elif r["holm_reject"] or tail:
            r["verdict"] = "INCONCLUSIVE"
        else:
            r["verdict"] = "NOT SUPPORTED"
        r["passed"] = r["verdict"] == "SUPPORTED"
    write_table(rows, "primary", "Primary pre-registered tests (H1-H6)")
    pd.DataFrame(plac.values()).to_csv(OUT / "placebo.csv", index=False)
    for r in rows:
        print(fmt_row(r), f"holm={r['p_holm']:.3f} pct_city={r['pct_city']} -> {r['verdict']}")
    print(pd.DataFrame(plac.values()).round(4).to_string())


if __name__ == "__main__":
    main()
