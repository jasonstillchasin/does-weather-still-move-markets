"""Replication gate (pre-registration section 8). Uses only data up to 2000-12-31.

HS 2003 NYC: 1982-1997, cloud anomaly deseasonalised on the same window, logit of up days.
KKL 2003 US: 1928-2000, SAD + FALL with lags, Monday and tax dummies (no weather controls);
also 1955-2000 with cloud/temp/rain controls as in KKL's full specification.
Pass = predicted sign with one-sided p < 0.10.
"""

from __future__ import annotations

import pandas as pd

from weather.data import returns
from weather.data.placebo_cities import CITIES
from weather.features.daylight import sad_fall
from weather.features.deseason import fullsample_anomaly
from weather.models.regress import logit_coef, ols_coef
from weather.panel import calendar_controls, city_weather
from weather.studies.common import OUT, fmt_row, write_table


def run() -> list[dict]:
    rows = []
    r = returns.us_market().rename("r")

    # --- HS 2003, NYC 1982-1997
    w = city_weather("NYC")
    win = w.loc["1982-01-01":"1997-12-31", "cloud"]
    hs = pd.DataFrame({"r": r}).join(fullsample_anomaly(win).rename("cloud_hs"), how="inner")
    e = logit_coef(hs, "r", ["cloud_hs"], "cloud_hs", -1)
    rows.append(dict(test="HS 2003 NYC logit (1982-97)", pred="<0", **vars(e), passed=e.coef < 0 and e.p_one < 0.10))
    e = ols_coef(hs, "r", ["cloud_hs"], "cloud_hs", -1)
    rows.append(dict(test="HS 2003 NYC OLS (1982-97)", pred="<0", **vars(e), passed=None))

    # --- KKL 2003, US 1928-2000
    df = r.loc["1928-01-01":"2000-12-31"].to_frame()
    df["lag1"], df["lag2"] = df["r"].shift(1), df["r"].shift(2)
    cal = calendar_controls(pd.DatetimeIndex(df.index), 12)
    df["mon"] = cal["mon"]
    # KKL tax dummy: last trading day of December and first five of January.
    df["tax"] = cal["turn_of_year"]
    df = df.join(sad_fall(pd.DatetimeIndex(df.index), CITIES["NYC"][0]))
    base = ["lag1", "lag2", "mon", "tax", "sad", "fall"]
    for name, pred, direction in (("sad", ">0", 1), ("fall", "<0", -1)):
        e = ols_coef(df, "r", base, name, direction)
        rows.append(dict(test=f"KKL 2003 US {name.upper()} (1928-2000)", pred=pred, **vars(e),
                         passed=(direction * e.coef > 0) and e.p_one < 0.10))
    wx = df.join(w[["cloud_zfull", "temp_zfull", "rain"]]).loc["1955-01-01":]
    for name, pred, direction in (("sad", ">0", 1), ("fall", "<0", -1)):
        e = ols_coef(wx, "r", base + ["cloud_zfull", "temp_zfull", "rain"], name, direction)
        rows.append(dict(test=f"KKL 2003 US {name.upper()} + weather (1955-2000)", pred=pred,
                         **vars(e), passed=None))
    return rows


def main() -> None:
    rows = run()
    write_table(rows, "replication", "Replication gate: pre-2001 data only")
    for r in rows:
        print(fmt_row(r))


if __name__ == "__main__":
    main()
