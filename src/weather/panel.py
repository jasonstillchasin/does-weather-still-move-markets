"""Daily analysis panels for each market (pre-registration section 3)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from weather.data import hourly, returns
from weather.data.net import CACHE
from weather.data.placebo_cities import CITIES
from weather.features.daylight import sad_fall
from weather.features.deseason import fullsample_anomaly, trailing_anomaly

END = pd.Timestamp("2026-08-31")
PUB_BREAK = pd.Timestamp("2003-07-01")
HYBRID = pd.Timestamp("2007-01-24")
COVID_FLOOR = pd.Timestamp("2020-03-23")


def city_weather(city: str) -> pd.DataFrame:
    """Daily 06:00-16:00 weather for NYC or SYD, with trailing and full-sample anomalies."""
    path = CACHE / "daily" / f"{city}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    tz = CITIES[city][2]
    hr = hourly.nyc_hourly() if city == "NYC" else hourly.syd_hourly()
    d = hourly.daily_window(hr, tz)
    for v in ("cloud", "temp"):
        d[f"{v}_z"] = trailing_anomaly(d[v].rename(v))
        d[f"{v}_zfull"] = fullsample_anomaly(d[v].rename(v))
    path.parent.mkdir(parents=True, exist_ok=True)
    d.to_parquet(path)
    return d


def calendar_controls(dates: pd.DatetimeIndex, tax_month: int) -> pd.DataFrame:
    """Day-of-week, turn-of-year, pre/post-holiday and tax-year-end dummies from trading dates."""
    d = pd.DataFrame(index=dates)
    for k, name in enumerate(["mon", "tue", "wed", "thu"]):
        d[name] = (dates.dayofweek == k).astype(float)
    s = pd.Series(dates, index=dates)
    nxt, prv = s.shift(-1), s.shift(1)
    # Weekdays skipped between consecutive trading dates mark a holiday.
    gap_after = np.array([np.busday_count(a.date(), b.date()) - 1 if pd.notna(b) else 0
                          for a, b in zip(s, nxt, strict=True)])
    gap_before = np.array([np.busday_count(b.date(), a.date()) - 1 if pd.notna(b) else 0
                           for a, b in zip(s, prv, strict=True)])
    d["preholiday"] = (gap_after > 0).astype(float)
    d["postholiday"] = (gap_before > 0).astype(float)
    ym = pd.Series(dates.year * 100 + dates.month, index=dates)
    rank_in_month = ym.groupby(ym).cumcount()
    rank_from_end = ym.groupby(ym).cumcount(ascending=False)
    d["turn_of_year"] = (
        ((dates.month == 12) & (rank_from_end == 0)) | ((dates.month == 1) & (rank_in_month < 5))
    ).astype(float)
    d["tax_year_end"] = ((dates.month == tax_month) & (rank_from_end < 5)).astype(float)
    return d


CONTROLS = ["mon", "tue", "wed", "thu", "preholiday", "postholiday", "turn_of_year",
            "tax_year_end", "lag1", "lag2"]


def market_panel(market: str, with_dividends: bool = True) -> pd.DataFrame:
    """Returns + controls + weather + SAD for 'US' or 'AU', up to END."""
    if market == "US":
        r = returns.us_market().rename("r")
        city, tax_month = "NYC", 12
    else:
        r = returns.au_market(with_dividends=with_dividends).rename("r")
        city, tax_month = "SYD", 6
    r = r[r.index <= END]
    df = r.to_frame()
    df["lag1"], df["lag2"] = r.shift(1), r.shift(2)
    df = df.join(calendar_controls(pd.DatetimeIndex(df.index), tax_month))
    w = city_weather(city)
    df = df.join(w[["cloud", "temp", "rain", "cloud_z", "temp_z", "cloud_zfull", "temp_zfull"]])
    lat = CITIES[city][0]
    df = df.join(sad_fall(pd.DatetimeIndex(df.index), lat))
    if market == "AU":
        us = returns.us_market()
        df["r_us_prev"] = returns.prior_us_return(pd.DatetimeIndex(df.index), us).to_numpy()
        nyc = sad_fall(pd.DatetimeIndex(df.index), CITIES["NYC"][0])
        df["sad_nyc"], df["fall_nyc"] = nyc["sad"], nyc["fall"]
        m = df.index.month
        df["halloween"] = ((m >= 11) | (m <= 4)).astype(float)
    df["post"] = (df.index >= PUB_BREAK).astype(float)
    df["hybrid"] = (df.index >= HYBRID).astype(float)
    df["covid_floor"] = (df.index >= COVID_FLOOR).astype(float)
    return df.dropna(subset=["r", "lag1", "lag2"])
