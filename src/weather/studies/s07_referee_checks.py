"""Checks prompted by review comments (exploratory; reported in the appendix).

1. Australian dividend add-back: every AU primary test with price-only returns, and with
   calendar-month fixed effects (which absorb any month-specific add-back exactly).
2. Bandwidth sensitivity: Newey-West lags 5/10/20 for H1-US; Driscoll-Kraay lags 5/10/20 for S6.
"""

from __future__ import annotations

import json
import warnings

import pandas as pd

from weather.data import returns
from weather.models.regress import ols_coef
from weather.panel import market_panel
from weather.studies import s02_primary as S
from weather.studies import s11_study2 as S2
from weather.studies.common import OUT

warnings.filterwarnings("ignore")


def month_dummies(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    d = df.copy()
    cols = []
    for m in range(2, 13):
        c = f"m{m}"
        d[c] = (d.index.month == m).astype(float)
        cols.append(c)
    return d, cols


def au_checks() -> list[dict]:
    rows = []
    tot = S.market_panel("AU")
    px = market_panel("AU", with_dividends=False)
    div = returns.au_dividend_addback(pd.DatetimeIndex(tot.index))
    for w in ("cloud_z", "temp_z"):
        c = tot[w].corr(div)
        rows.append(dict(check=f"corr(dividend add-back, {w})", value=float(c)))
    for spec in S.SPECS:
        if spec[1] != "AU":
            continue
        for lab, df in (("total return (primary)", tot), ("price only", px)):
            e = S.estimate(df, spec, spec[3])
            rows.append(dict(check=f"{spec[0]} {lab}", coef_bp=e.coef * 100, t=e.t,
                             p_one=e.p_one, n=e.n))
        if spec[0] != "H3-AU":  # month FE would absorb the seasonal SAD terms
            d, mcols = month_dummies(tot)
            sid, market, y, wvar, extra, tested, direction = spec
            dd = S._prepare(d, wvar)
            xs = [*extra, *(["W"] if tested == "W" and "W" not in extra else [])]
            if tested not in xs:
                xs.append(tested)
            xs += S._controls(market, y) + mcols
            e = ols_coef(dd, y, xs, tested, direction)
            rows.append(dict(check=f"{spec[0]} total return + month FE", coef_bp=e.coef * 100,
                             t=e.t, p_one=e.p_one, n=e.n))
    return rows


def bandwidth_checks() -> list[dict]:
    rows = []
    p = S.panels()
    spec = S.SPECS[0]  # H1-US
    d = S._prepare(p["US"], "cloud_z")
    for lags in (5, 10, 20):
        e = ols_coef(d, "r", ["W", *S._controls("US", "r")], "W", -1, lags=lags)
        rows.append(dict(check=f"H1-US Newey-West lags={lags}", coef_bp=e.coef * 100, t=e.t,
                         p_one=e.p_one, n=e.n))
    _ = spec
    panel, _ = S2.build_panel()
    new = {c for c, *_ in S2.EXCHANGES} - S2.STUDY1
    d2 = panel[panel["exchange"].isin(new)]
    for lags in (5, 10, 20):
        e = S2.fe_ols_dk(d2, ["rain_a", *S2.CONTROLS], "rain_a", lags=lags)
        rows.append(dict(check=f"S6 Driscoll-Kraay lags={lags}", coef_bp=None,
                         coef_pct_sd=e["coef"] * 100, t=e["t"],
                         p_one=S2.p_value(e["t"], -1), n=e["n"]))
    return rows


def main() -> None:
    rows = au_checks() + bandwidth_checks()
    (OUT / "referee_checks.json").write_text(json.dumps(rows, indent=2, default=str))
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
