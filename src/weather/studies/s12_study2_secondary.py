"""Study 2 secondary / exploratory analyses (prereg/study2_preregistration.md section 7)."""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from weather.data import era5_full
from weather.data.exchanges import EXCHANGES
from weather.models.regress import ols_coef
from weather.studies import s11_study2 as S2
from weather.studies.common import OUT

warnings.filterwarnings("ignore")
VARS = [("cloud_z", -1), ("sun_z", 1), ("temp_z", -1), ("wind_z", -1), ("rain_a", -1),
        ("humid_z", 0), ("press_z", 0)]
# MSCI market classification (developed) as of 2026; everything else is emerging/frontier.
DEVELOPED = {"New York", "Sydney", "London", "Frankfurt", "Paris", "Zurich", "Amsterdam",
             "Brussels", "Madrid", "Milan", "Vienna", "Dublin", "Tokyo", "Hong Kong",
             "Singapore", "Toronto", "Wellington"}


def pooled(d: pd.DataFrame, w: str, sign: int, y: str = "y") -> dict:
    dd = d.copy()
    dd["y"] = dd[y]
    e = S2.fe_ols_dk(dd, [w, *S2.CONTROLS], w)
    e["p"] = S2.p_value(e["t"], sign)
    return e


def extreme_events(panel: pd.DataFrame) -> pd.DataFrame:
    """Storm day: 06-16h max gust above the trailing 30-year 99th percentile for the ISO week."""
    out = []
    for city, lat, lon, tz, _ in EXCHANGES:
        g = era5_full.fetch(city, lat, lon, tz)["gust"].dropna()
        wk = np.minimum(g.index.isocalendar().week.to_numpy(dtype=int), 52)
        df = pd.DataFrame({"g": g.to_numpy(), "wk": wk, "yr": g.index.year}, index=g.index)
        thr = {}
        for (w, yr), _ in df.groupby(["wk", "yr"]):
            past = df[(df.wk == w) & (df.yr < yr) & (df.yr >= yr - 30)]["g"]
            if past.index.year.nunique() >= 5:
                thr[(w, yr)] = np.quantile(past, 0.99)
        t = pd.Series([thr.get(k, np.nan) for k in zip(df.wk, df.yr, strict=True)],
                      index=df.index)
        storm = (df["g"] > t).astype(float).where(t.notna())
        out.append(pd.DataFrame({"storm": storm, "exchange": city}))
    s = pd.concat(out).reset_index().rename(columns={"index": "date"})
    s = s.rename(columns={s.columns[0]: "date"})
    p = panel.reset_index().rename(columns={"index": "date"})
    p = p.rename(columns={p.columns[0]: "date"})
    m = p.merge(s, on=["date", "exchange"], how="left").set_index("date")
    m["heat"] = (m["temp_z"] > 2).astype(float).where(m["temp_z"].notna())
    return m


def main() -> None:
    panel, _ = S2.build_panel()
    all28 = {c for c, *_ in EXCHANGES}
    new = all28 - S2.STUDY1
    rows = []

    # 1. 28-exchange version of S1-S9 (no placebo).
    for r in S2.run_specs(panel, all28, with_placebo=False):
        rows.append(dict(group="28 exchanges", test=r["test"], var=r["var"], coef=r["coef"],
                         t=r["t"], p=r["p"], n=r["n"]))

    # 2. Pre/post 2003, hemispheres, developed vs emerging, raw returns, |y| volatility.
    d26 = panel[panel["exchange"].isin(new)].copy()
    d26["r_bp"] = d26["y"] * d26["sigma"] * 100
    d26["absy"] = d26["y"].abs()
    splits = {
        "pre-2003": d26[d26.index < "2003-07-01"], "post-2003": d26[d26.index >= "2003-07-01"],
        "northern": d26[d26["south"] == 0], "southern": d26[d26["south"] == 1],
        "developed": d26[d26["exchange"].isin(DEVELOPED)],
        "emerging": d26[~d26["exchange"].isin(DEVELOPED)],
    }
    for w, sign in VARS:
        for lab, d in splits.items():
            e = pooled(d, w, sign)
            rows.append(dict(group=lab, test=w, var=w, coef=e["coef"], t=e["t"], p=e["p"],
                             n=e["n"]))
        e = pooled(d26, w, sign, y="r_bp")
        rows.append(dict(group="raw returns (bp)", test=w, var=w, coef=e["coef"], t=e["t"],
                         p=e["p"], n=e["n"]))
        e = pooled(d26, w, 0, y="absy")
        rows.append(dict(group="|y| (volatility)", test=w, var=w, coef=e["coef"], t=e["t"],
                         p=e["p"], n=e["n"]))

    # 3. Joint model with all seven anomalies.
    ws = [w for w, _ in VARS]
    for w, sign in VARS:
        e = S2.fe_ols_dk(d26, [*ws, *S2.CONTROLS], w)
        rows.append(dict(group="joint model", test=w, var=w, coef=e["coef"], t=e["t"],
                         p=S2.p_value(e["t"], sign), n=e["n"]))

    # 4. Extreme events.
    m = extreme_events(d26.drop(columns=["r_bp", "absy"]))
    for w in ("storm", "heat"):
        e = pooled(m, w, -1)
        rows.append(dict(group="extreme events", test=w, var=w, coef=e["coef"], t=e["t"],
                         p=e["p"], n=e["n"]))

    # 5. Halloween horse race (pooled 26).
    d26["halloween"] = ((d26.index.month >= 11) | (d26.index.month <= 4)).astype(float)
    xs = ["sad", "fall", "halloween", *S2.CONTROLS]
    for w in ("sad", "halloween"):
        e = S2.fe_ols_dk(d26, xs, w)
        rows.append(dict(group="Halloween horse race", test=w, var=w, coef=e["coef"],
                         t=e["t"], p=S2.p_value(e["t"], 1), n=e["n"]))

    # 6. Per-exchange estimates with BH-FDR at 10% across exchange x variable.
    per = []
    for city in sorted(all28):
        d = panel[panel["exchange"] == city]
        ctrl = [c for c in S2.CONTROLS if not (city == "New York" and c == "us_prev")]
        for w, sign in VARS:
            e = ols_coef(d, "y", [w, *ctrl], w, sign if sign else 1)
            p = S2.p_value(e.t, sign)
            per.append(dict(exchange=city, var=w, coef=e.coef, se=e.se, t=e.t, p=p, n=e.n))
    bh = multipletests([r["p"] for r in per], alpha=0.10, method="fdr_bh")
    for r, rej, q in zip(per, bh[0], bh[1], strict=True):
        r["q_bh"], r["fdr_reject"] = float(q), bool(rej)

    (OUT / "study2_secondary.json").write_text(json.dumps(rows, indent=2, default=str))
    pd.DataFrame(per).to_csv(OUT / "study2_per_exchange.csv", index=False)
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    pe = pd.DataFrame(per)
    print("\nFDR discoveries:\n", pe[pe.fdr_reject].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
