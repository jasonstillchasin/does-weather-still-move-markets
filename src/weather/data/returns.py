"""Daily index returns (log, percent), cached as parquet.

US: Ken French daily Mkt = Mkt-RF + RF (CRSP value-weighted, total return) and size deciles.
AU: S&P/ASX All Ordinaries price index (Yahoo ^AORD) plus a dividend add-back (deviation D3):
    the average calendar-month dividend return per trading day, from ^AXJT - ^AXJO (2019+).
"""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd
import yfinance as yf

from weather.data.net import CACHE, get

FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}_CSV.zip"
RCACHE = CACHE / "returns"


def _french_csv(name: str) -> str:
    raw = get(FRENCH.format(name=name))
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return z.read(z.namelist()[0]).decode("latin-1")


def _french_blocks(text: str) -> list[pd.DataFrame]:
    """Split a Ken French CSV into its data blocks (header row + yyyymmdd rows)."""
    blocks, header, rows = [], None, []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) > 1 and parts[0] == "" and header is None:
            header = parts[1:]
        elif header and parts[0].isdigit() and len(parts[0]) == 8:
            rows.append(parts)
        elif header and rows:
            blocks.append(_frame(header, rows))
            header, rows = None, []
            if len(parts) > 1 and parts[0] == "":
                header = parts[1:]
    if header and rows:
        blocks.append(_frame(header, rows))
    return blocks


def _frame(header: list[str], rows: list[list[str]]) -> pd.DataFrame:
    df = pd.DataFrame([r[1 : len(header) + 1] for r in rows], columns=header, dtype=float)
    df.index = pd.to_datetime([r[0] for r in rows], format="%Y%m%d")
    df.index.name = "date"
    return df.replace([-99.99, -999], np.nan)


def _cached(name: str, build) -> pd.DataFrame:
    RCACHE.mkdir(parents=True, exist_ok=True)
    path = RCACHE / f"{name}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    df = build()
    df.to_parquet(path)
    return df


def french_factors_daily() -> pd.DataFrame:
    return _cached(
        "ff3_daily", lambda: _french_blocks(_french_csv("F-F_Research_Data_Factors_daily"))[0]
    )


def french_size_daily() -> pd.DataFrame:
    """Value-weighted daily returns of size portfolios (first block of the file)."""
    return _cached(
        "size_daily", lambda: _french_blocks(_french_csv("Portfolios_Formed_on_ME_daily"))[0]
    )


def french_industry49_daily() -> pd.DataFrame:
    return _cached(
        "ind49_daily", lambda: _french_blocks(_french_csv("49_Industry_Portfolios_daily"))[0]
    )


def yahoo_close(symbol: str) -> pd.Series:
    def build() -> pd.DataFrame:
        raw = yf.Ticker(symbol).history(period="max", auto_adjust=False, actions=False)
        idx = pd.DatetimeIndex(raw.index.tz_localize(None).normalize(), name="date")
        s = pd.Series(raw["Close"].to_numpy(), index=idx, name="close").dropna()
        return s[~s.index.duplicated(keep="last")].sort_index().to_frame()

    safe = symbol.replace("^", "IDX_").replace(".", "_")
    return _cached(f"yahoo_{safe}", build)["close"]


def logret(price: pd.Series) -> pd.Series:
    p = price[price > 0]
    return (np.log(p).diff() * 100).dropna()


def us_market() -> pd.Series:
    f = french_factors_daily()
    return (np.log1p((f["Mkt-RF"] + f["RF"]) / 100) * 100).rename("r_us")


def us_small_minus_big() -> pd.Series:
    s = french_size_daily()
    return (s["Lo 10"] - s["Hi 10"]).rename("smb10")


def au_dividend_addback(dates: pd.DatetimeIndex) -> pd.Series:
    """Daily dividend return (percent) for the ASX market on ``dates`` (deviation D3).

    ^AXJT - ^AXJO has stale-price artefacts (paired +/- swings) and occasional glitches, so we
    use its average per trading day in each calendar month (|daily diff| > 1% dropped),
    applied to every year.
    """
    tr, px = logret(yahoo_close("^AXJT")), logret(yahoo_close("^AXJO"))
    diff = (tr - px).dropna()
    diff = diff[(diff.index > diff.index.min() + pd.Timedelta(days=5)) & (diff.abs() <= 1.0)]
    profile = diff.groupby(diff.index.month).mean()
    return pd.Series(profile.reindex(dates.month).to_numpy(), index=dates, name="div")


def au_market(with_dividends: bool = True) -> pd.Series:
    r = logret(yahoo_close("^AORD")).rename("r_au")
    if with_dividends:
        r = r + au_dividend_addback(pd.DatetimeIndex(r.index))
    return r.rename("r_au")


def prior_us_return(au_dates: pd.DatetimeIndex, us: pd.Series) -> pd.Series:
    """US return on the latest US session dated strictly before each AU date.

    The NYSE closes at 06:00-08:00 Sydney time on the next calendar day, so the US session
    of date t-1 is fully known before the ASX opens on date t.
    """
    left = pd.DataFrame({"date": au_dates})
    right = us.rename("r_us_prev").reset_index().rename(columns={us.index.name or "index": "date"})
    m = pd.merge_asof(left, right.sort_values("date"), on="date", allow_exact_matches=False)
    return m.set_index("date")["r_us_prev"]
