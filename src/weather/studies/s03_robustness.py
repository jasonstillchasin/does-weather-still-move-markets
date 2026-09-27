"""Exploratory / secondary analyses (pre-registration section 4, "Secondary / exploratory").

None of these are in the Holm family. One-sided p-values are in the direction the original
literature predicts; they are reported for description, not as confirmatory tests.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from arch import arch_model

from weather.data import hourly, returns
from weather.data.placebo_cities import CITIES
from weather.features.deseason import trailing_anomaly
from weather.models.regress import Est, logit_coef, ols_coef
from weather.panel import CONTROLS
from weather.studies import s02_primary as S
from weather.studies.common import OUT, write_table

warnings.filterwarnings("ignore")


def row(test: str, pred: str, e: Est, **extra) -> dict:
    d = dict(test=test, pred=pred, **vars(e), passed=None, **extra)
    if pred == "±":  # no directional prediction: report the two-sided p-value
        d["p_one"] = 2 * min(e.p_one, 1 - e.p_one)
    return d


def garch_coef(df: pd.DataFrame, y: str, xs: list[str], name: str, direction: int) -> Est:
    d = df[[y, *xs]].dropna()
    res = arch_model(d[y], x=d[xs], mean="LS", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
    from scipy import stats

    b, se = float(res.params[name]), float(res.std_err[name])
    t = b / se
    return Est(b, se, t, float(stats.norm.sf(direction * t)), len(d), b - 1.96 * se, b + 1.96 * se)


def weather_specs(p: dict[str, pd.DataFrame]) -> list[dict]:
    rows = []
    alt = {"US": "CHI", "AU": "MEL"}
    home = {"US": "NYC", "AU": "SYD"}
    au_px = S.market_panel("AU", with_dividends=False)
    for sid in ("H1-US", "H1-AU", "H2-US", "H2-AU", "H4-US", "H4-AU"):
        spec = next(s for s in S.SPECS if s[0] == sid)
        market, wvar, direction = spec[1], spec[3], spec[6]
        pred = "<0" if direction < 0 else ">0"
        df = p[market]
        base = df.drop(columns=["cloud_z", "temp_z"])
        rows.append(row(f"{sid} station (primary)", pred, S.estimate(df, spec, wvar)))
        era = S.era5_anomalies(home[market], *CITIES[home[market]])
        rows.append(row(f"{sid} ERA5 weather", pred,
                        S.estimate(base.join(era[[wvar]]), spec, wvar)))
        a = S.era5_anomalies(alt[market], *CITIES[alt[market]])
        rows.append(row(f"{sid} {alt[market]} weather (ERA5)", pred,
                        S.estimate(base.join(a[[wvar]]), spec, wvar)))
        full = df.copy()
        full[wvar] = full[wvar.replace("_z", "_zfull")]
        rows.append(row(f"{sid} full-sample deseasonalisation", pred,
                        S.estimate(full, spec, wvar)))
        if market == "AU":
            rows.append(row(f"{sid} AU price-only returns", pred, S.estimate(au_px, spec, wvar)))
        if sid.startswith("H2"):
            b01 = df.copy()
            b01["post"] = (b01.index >= "2001-01-01").astype(float)
            rows.append(row(f"{sid} break at 2001-01 (HS working paper)", pred,
                            S.estimate(b01, spec, wvar)))
        if sid.startswith(("H1", "H4")):
            xs = [wvar, *S._controls(market, "r")]
            rows.append(row(f"{sid} logit up/down", pred, logit_coef(df, "r", xs, wvar, direction)))
            rows.append(row(f"{sid} GARCH(1,1)-t mean", pred,
                            garch_coef(df, "r", xs, wvar, direction)))
    for market in ("US", "AU"):
        xs = ["rain", *S._controls(market, "r")]
        rows.append(row(f"RAIN-{market} (06-16h rain dummy)", "<0",
                        ols_coef(p[market], "r", xs, "rain", -1)))
    return rows


def seasonal_specs(p: dict[str, pd.DataFrame]) -> list[dict]:
    rows = []
    us = p["US"]
    for lab, d in (("1955-2026", us.loc["1955":]), ("1928-2026", us.loc["1928":]),
                   ("post-2003", us[us.post == 1])):
        xs = ["sad", "fall", *CONTROLS]
        rows.append(row(f"US SAD, {lab}", ">0", ols_coef(d, "r", xs, "sad", 1)))
        rows.append(row(f"US FALL, {lab}", "<0", ols_coef(d, "r", xs, "fall", -1)))
    au = p["AU"]
    ctrl = S._controls("AU", "r")
    rows.append(row("AU SAD (own season), alone", ">0",
                    ols_coef(au, "r", ["sad", "fall", *ctrl], "sad", 1)))
    rows.append(row("AU SAD_NYC (calendar), alone", ">0",
                    ols_coef(au, "r", ["sad_nyc", "fall_nyc", *ctrl], "sad_nyc", 1)))
    rows.append(row("AU Halloween (Nov-Apr), alone", ">0",
                    ols_coef(au, "r", ["halloween", *ctrl], "halloween", 1)))
    xs = ["sad", "fall", "halloween", *ctrl]
    rows.append(row("AU SAD with Halloween", ">0", ols_coef(au, "r", xs, "sad", 1)))
    rows.append(row("AU Halloween with SAD", ">0", ols_coef(au, "r", xs, "halloween", 1)))
    for lab, d in (("pre-2003", au[au.post == 0]), ("post-2003", au[au.post == 1])):
        rows.append(row(f"AU Halloween, {lab}", ">0",
                        ols_coef(d, "r", ["halloween", *ctrl], "halloween", 1)))
    return rows


def structure_specs(p: dict[str, pd.DataFrame]) -> list[dict]:
    rows = []
    us = S._prepare(p["US"], "cloud_z")
    us["W_covid"] = us["W"] * us["covid_floor"]
    xs = ["W", "covid_floor", "W_covid", *CONTROLS]
    rows.append(row("US cloud x post-2020-03 floor closure", ">0",
                    ols_coef(us, "r", xs, "W_covid", 1)))
    for lab, d in (("1955-2006", us[us.hybrid == 0]), ("2007-2026", us[us.hybrid == 1])):
        rows.append(row(f"US cloud, {lab}", "<0",
                        ols_coef(d, "r", ["W", *CONTROLS], "W", -1)))
    # AU small minus large (Small Ords minus ASX 50), 2013+.
    sml = (returns.logret(returns.yahoo_close("^AXSO"))
           - returns.logret(returns.yahoo_close("^AFLI"))).dropna().rename("sml")
    au = p["AU"].join(sml, how="inner")
    au["sml_lag1"], au["sml_lag2"] = au["sml"].shift(1), au["sml"].shift(2)
    xs = ["cloud_z", *S._controls("AU", "sml")]
    rows.append(row("AU small-minus-large (^AXSO-^AFLI) on cloud", "<0",
                    ols_coef(au, "sml", xs, "cloud_z", -1)))
    return rows


def industry_specs(p: dict[str, pd.DataFrame]) -> list[dict]:
    """Physical channel: industry returns on weather anomalies, controlling for the same-day
    market return (so a low-beta industry does not mechanically 'win' on down days)."""
    rows = []
    ind = returns.french_industry49_daily()
    ff = returns.french_factors_daily()
    mkt = ff["Mkt-RF"] + ff["RF"]
    us = p["US"]
    for name in ("Util", "Oil", "Coal", "Agric", "Food", "Rtail", "Meals", "Insur"):
        d = us.join(ind[name].rename("ind"), how="inner").join(mkt.rename("mkt"))
        d["ind_lag1"], d["ind_lag2"] = d["ind"].shift(1), d["ind"].shift(2)
        ctrl = ["mkt", *S._controls("US", "ind")]
        for w in ("temp_z", "cloud_z"):
            rows.append(row(f"Industry {name} (market-adjusted) on {w}", "±",
                            ols_coef(d, "ind", [w, *ctrl], w, 1)))
    return rows


def strategy() -> tuple[list[dict], pd.DataFrame]:
    """Long SPY open-to-close only on mornings sunnier than normal (NYC 06-10h cloud)."""
    hr = hourly.nyc_hourly()
    morning = hourly.daily_window(hr, "America/New_York", start_h=6, end_h=10, min_obs=2)
    mz = trailing_anomaly(morning["cloud"].rename("m")).rename("mcloud_z")
    import yfinance as yf

    spy = yf.Ticker("SPY").history(period="max", auto_adjust=True)
    spy.index = spy.index.tz_localize(None).normalize()
    oc = (np.log(spy["Close"] / spy["Open"]) * 100).rename("oc")
    d = pd.concat([oc, mz], axis=1, join="inner").loc[:"2026-08-31"].dropna()
    rows, curves = [], {}
    for cost_bp in (0.0, 1.0, 2.0):
        c = cost_bp / 100
        always = d["oc"] - c
        in_sunny = (d["mcloud_z"] < 0).to_numpy()
        sunny = np.where(in_sunny, d["oc"] - c, 0.0)
        cloudy = np.where(~in_sunny, d["oc"] - c, 0.0)
        for lab, r, held in (("every day", always, np.ones(len(d), bool)),
                             ("sunny mornings only", sunny, in_sunny),
                             ("cloudy mornings only", cloudy, ~in_sunny)):
            r = pd.Series(np.asarray(r), index=d.index)
            ann = r.mean() * 252
            sr = r.mean() / r.std() * np.sqrt(252)
            rows.append(dict(strategy=lab, cost_bp_roundtrip=cost_bp, ann_return_pct=ann,
                             sharpe=sr, days_in_market=int(held.sum()), n=len(r)))
            if cost_bp == 1.0:
                curves[lab] = r.cumsum()
    gross = d.groupby(d["mcloud_z"] < 0)["oc"].agg(["mean", "std", "count"])
    diff = gross.loc[True, "mean"] - gross.loc[False, "mean"]
    se = np.sqrt((gross["std"] ** 2 / gross["count"]).sum())
    rows.append(dict(strategy="sunny minus cloudy mornings, mean open-close (bp)",
                     cost_bp_roundtrip=None, ann_return_pct=diff * 100, sharpe=diff / se,
                     days_in_market=None, n=len(d)))
    return rows, pd.DataFrame(curves)


def main() -> None:
    p = S.panels()
    groups = {
        "robust_weather": ("Robustness of the weather tests (exploratory)", weather_specs(p)),
        "robust_seasonal": ("Seasonal tests: SAD, FALL and Halloween (exploratory)",
                            seasonal_specs(p)),
        "robust_structure": ("Market-structure and size tests (exploratory)",
                             structure_specs(p)),
        "robust_industry": ("Industry-minus-market on weather (physical channel, exploratory)",
                            industry_specs(p)),
    }
    for name, (cap, rows) in groups.items():
        write_table(rows, name, cap)
        print(f"\n## {cap}")
        for r in rows:
            print(f"{r['test']:<55} b={r['coef'] * 100:+6.2f}bp  t={r['t']:+5.2f}  "
                  f"p={r['p_one']:.3f}  n={r['n']}")
    srows, curves = strategy()
    s = pd.DataFrame(srows)
    s.to_csv(OUT / "strategy.csv", index=False)
    curves.to_csv(OUT / "strategy_curves.csv")
    print("\n## Cloud-timed SPY open-to-close strategy")
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
