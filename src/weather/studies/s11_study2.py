"""Study 2 primary tests S1-S9 (prereg/study2_preregistration.md).

Pooled OLS over the 26 new exchanges with exchange fixed effects and Driscoll-Kraay errors, Holm
across the 9 tests, and placebo-assignment inference. Refuses to run until the Study 2
pre-registration is committed.
"""

from __future__ import annotations

import functools
import json
import math
import subprocess
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from weather.data import era5_full, returns
from weather.data.exchanges import EXCHANGES
from weather.data.net import ROOT
from weather.data.placebo_cities import PLACEBO_CITIES, km
from weather.features.daylight import sad_fall
from weather.features.deseason import trailing_anomaly
from weather.panel import END, calendar_controls
from weather.studies.common import OUT

warnings.filterwarnings("ignore")
STUDY1 = {"New York", "Sydney"}
Z_VARS = ["cloud", "sun", "temp", "wind", "humid", "press"]
CONTROLS = ["mon", "tue", "wed", "thu", "preholiday", "postholiday", "turn_of_year",
            "lag1", "lag2", "us_prev"]
SEED, DRAWS, DK_LAGS = 20260928, 200, 5
HS_END = pd.Timestamp("1998-01-01")

# (id, weather column, sample filter, tested sign: -1, +1 or 0 = two-sided)
SPECS = [
    ("S1", "cloud_z", None, -1), ("S2", "cloud_z", "post1997", -1),
    ("S3", "sun_z", None, 1), ("S4", "temp_z", None, -1), ("S5", "wind_z", None, -1),
    ("S6", "rain_a", None, -1), ("S7", "humid_z", None, 0), ("S8", "press_z", None, 0),
]


def frozen() -> bool:
    def committed(path: str) -> bool:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H", "--", path],
                             capture_output=True, text=True)
        return out.returncode == 0 and bool(out.stdout.strip())

    return committed("prereg/study2_preregistration.md") and committed(
        "src/weather/data/exchanges.py")


# ------------------------------------------------------------------ data
@functools.cache
def weather_anomalies(name: str, lat: float, lon: float, tz: str) -> pd.DataFrame:
    d = era5_full.fetch(name, lat, lon, tz)
    out = {f"{v}_z": trailing_anomaly(d[v].rename(v)) for v in Z_VARS}
    rain = (d["rain"] >= 1.0).astype(float).where(d["rain"].notna())
    out["rain_a"] = trailing_anomaly(rain.rename("rain"), standardise=False)
    return _ns(pd.DataFrame(out))


def _ns(x):
    x = x.copy()
    x.index = pd.DatetimeIndex(x.index).astype("datetime64[ns]")
    return x


def index_returns(source: str) -> pd.Series:
    if source == "FRENCH_MKT":
        return _ns(returns.us_market())
    if source == "AORD_DIV":
        return _ns(returns.au_market())
    return _ns(returns.logret(returns.yahoo_close(source)))


def scaled(r: pd.Series) -> pd.Series:
    r = r[(r.abs() <= 20) & (r != 0)]
    sigma = r.rolling(60, min_periods=40).std().shift(1)
    return (r / sigma).rename("y"), sigma


def exchange_frame(city: str, lat: float, tz: str, source: str, us_y: pd.Series,
                   weather: pd.DataFrame) -> pd.DataFrame:
    r = index_returns(source)
    r = r[r.index <= END]
    y, sigma = scaled(r)
    df = pd.DataFrame({"y": y, "sigma": sigma.reindex(y.index)}).dropna()
    df["lag1"], df["lag2"] = df["y"].shift(1), df["y"].shift(2)
    cal = calendar_controls(pd.DatetimeIndex(df.index), 12).drop(columns="tax_year_end")
    df = df.join(cal)
    if source == "FRENCH_MKT":
        df["us_prev"] = 0.0
    else:
        left = pd.DataFrame({"date": df.index})
        right = us_y.rename("us_prev").reset_index().rename(columns={"index": "date"})
        right.columns = ["date", "us_prev"]
        m = pd.merge_asof(left, right.sort_values("date"), on="date",
                          allow_exact_matches=False)
        df["us_prev"] = m["us_prev"].to_numpy()
    sf = sad_fall(pd.DatetimeIndex(df.index), lat)
    cal_sf = sad_fall(pd.DatetimeIndex(df.index), abs(lat))
    df["sad"], df["fall"] = sf["sad"], sf["fall"]
    df["sad_cal"], df["fall_cal"] = cal_sf["sad"], cal_sf["fall"]
    df = df.join(weather)
    df["exchange"] = city
    df["south"] = float(lat < 0)
    return df.dropna(subset=["y", "lag1", "lag2", "us_prev"])


def build_panel() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    us_y, _ = scaled(_ns(returns.us_market()))
    weather = {}
    frames = []
    for city, lat, lon, tz, source in EXCHANGES:
        weather[city] = weather_anomalies(city, lat, lon, tz)
        frames.append(exchange_frame(city, lat, tz, source, us_y, weather[city]))
    return pd.concat(frames).sort_index(), weather


# ------------------------------------------------------------------ estimation
def fe_ols_dk(df: pd.DataFrame, xs: list[str], tested: str, lags: int = DK_LAGS) -> dict:
    """OLS of y on xs + exchange FE with Driscoll-Kraay standard errors."""
    d = df[["y", "exchange", *xs]].dropna()
    fe = pd.get_dummies(d["exchange"], drop_first=False, dtype=float)
    X = np.column_stack([d[xs].to_numpy(dtype=float), fe.to_numpy()])
    y = d["y"].to_numpy(dtype=float)
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    scores = X * e[:, None]
    h = pd.DataFrame(scores).groupby(d.index.to_numpy()).sum().sort_index().to_numpy()
    T = len(h)
    S = h.T @ h
    for lag in range(1, lags + 1):
        w = 1 - lag / (lags + 1)
        G = h[lag:].T @ h[:-lag]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    j = xs.index(tested)
    b, se = float(beta[j]), float(math.sqrt(V[j, j]))
    return dict(coef=b, se=se, t=b / se, n=len(d), T=T, n_exch=d["exchange"].nunique())


def p_value(t: float, sign: int) -> float:
    return float(2 * stats.norm.sf(abs(t))) if sign == 0 else float(stats.norm.sf(sign * t))


def sample(df: pd.DataFrame, filt: str | None, exchanges: set[str]) -> pd.DataFrame:
    d = df[df["exchange"].isin(exchanges)]
    return d[d.index >= HS_END] if filt == "post1997" else d


def placebo(df: pd.DataFrame, wcol: str, filt, exchanges: set[str], real: float, sign: int,
            rng: np.random.Generator) -> float:
    coords = {c: (lat, lon) for c, lat, lon, _, _ in EXCHANGES}
    pool = [c for c in PLACEBO_CITIES if c[0] not in coords]
    pw = {c[0]: weather_anomalies(*c)[[wcol]] for c in pool}
    base = sample(df, filt, exchanges).drop(columns=[wcol])
    groups = dict(tuple(base.groupby("exchange")))
    eligible = {city: [c[0] for c in pool if km(*coords[city], c[1], c[2]) > 1000]
                for city in groups}
    draws = []
    for _ in range(DRAWS):
        parts = []
        for city, g in groups.items():
            ok = eligible[city]
            pick = ok[rng.integers(len(ok))]
            parts.append(g.join(pw[pick]))
        d = pd.concat(parts)
        draws.append(fe_ols_dk(d, [wcol, *CONTROLS], wcol)["coef"])
    draws = np.array(draws)
    if sign == 0:
        return float(np.mean(np.abs(draws) >= abs(real)))
    return float(np.mean(sign * draws >= sign * real))


def run_specs(panel: pd.DataFrame, exchanges: set[str], with_placebo: bool) -> list[dict]:
    rng = np.random.default_rng(SEED)
    med_sigma = float(panel[panel["exchange"].isin(exchanges)]["sigma"].median())
    rows = []
    for sid, wcol, filt, sign in SPECS:
        d = sample(panel, filt, exchanges)
        e = fe_ols_dk(d, [wcol, *CONTROLS], wcol)
        e.update(test=sid, var=wcol, sign=sign, p=p_value(e["t"], sign),
                 bp_at_median_sigma=e["coef"] * med_sigma * 100)
        if with_placebo:
            e["pct_placebo"] = placebo(panel, wcol, filt, exchanges, e["coef"], sign, rng)
        rows.append(e)
    d = sample(panel, None, exchanges)
    xs = ["sad", "fall", "sad_cal", "fall_cal", *CONTROLS]
    e = fe_ols_dk(d, xs, "sad")
    e.update(test="S9", var="sad", sign=1, p=p_value(e["t"], 1),
             bp_at_median_sigma=e["coef"] * med_sigma * 100, pct_placebo=None)
    rows.append(e)
    holm = multipletests([r["p"] for r in rows], alpha=0.05, method="holm")
    for r, rej, padj in zip(rows, holm[0], holm[1], strict=True):
        r["p_holm"], r["holm_reject"] = float(padj), bool(rej)
        if r["test"] == "S9" or not with_placebo:
            tail = None
        else:
            tail = r["pct_placebo"] <= (0.025 if r["sign"] == 0 else 0.05)
        if tail is None:
            r["verdict"] = ("SUPPORTED" if rej else "NOT SUPPORTED") if r["test"] == "S9" \
                else ("pending placebo" if rej else "NOT SUPPORTED")
        elif rej and tail:
            r["verdict"] = "SUPPORTED"
        elif rej or tail:
            r["verdict"] = "INCONCLUSIVE"
        else:
            r["verdict"] = "NOT SUPPORTED"
    return rows


def main() -> None:
    if not frozen():
        sys.exit("Commit prereg/study2_preregistration.md and src/weather/data/exchanges.py "
                 "before running Study 2.")
    panel, _ = build_panel()
    new = {c for c, *_ in EXCHANGES} - STUDY1
    rows = run_specs(panel, new, with_placebo="--no-placebo" not in sys.argv)
    OUT.mkdir(exist_ok=True)
    (OUT / "study2_primary.json").write_text(json.dumps(rows, indent=2, default=str))
    cols = ["test", "var", "coef", "se", "t", "p", "p_holm", "pct_placebo",
            "bp_at_median_sigma", "n", "n_exch", "verdict"]
    print(pd.DataFrame(rows)[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
