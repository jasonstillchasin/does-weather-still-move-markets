"""Hourly station weather from NOAA GHCNh, NOAA ISD-Lite and IEM METAR, cached as parquet.

Every loader returns a UTC-indexed frame with columns:
  cloud  total sky cover in oktas (0-8); obscured/unknown -> NaN
  temp   air temperature, deg C
  precip precipitation amount in the report (mm); NaN when not reported

Sources (see prereg deviations log D1):
  NYC    GHCNh LaGuardia USW00014732 (1948+), fallback JFK USW00094789
  Sydney ISD-Lite Sydney Intl 947670-99999 (to Aug 2025), then IEM METAR YSSY
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from weather.data.net import CACHE, get

log = logging.getLogger(__name__)

GHCNH = (
    "https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/"
    "access/by-year/{year}/parquet/GHCNh_{sid}_{year}.parquet"
)
ISDLITE = "https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/{year}/{sid}-{year}.gz"
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

# METAR cover categories -> oktas, matching ISD-Lite's coding (BKN = 6 in ISD-Lite).
METAR_OKTA = {"CLR": 0, "SKC": 0, "NSC": 0, "NCD": 0, "CAVOK": 0, "FEW": 2, "SCT": 4, "BKN": 6,
              "OVC": 8}
EMPTY = pd.DataFrame(columns=["cloud", "temp", "precip"], index=pd.DatetimeIndex([], name="utc"))


def _cache(kind: str, sid: str, year: int) -> Path:
    p = CACHE / "hourly" / kind / f"{sid}_{year}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _okta_from_summation(s: pd.Series) -> pd.Series:
    """'BKN:07;05' -> 7.0; VV (09) and unknown (10) -> NaN."""
    code = pd.to_numeric(s.str.extract(r":(\d{2})", expand=False), errors="coerce")
    return code.where(code <= 8)


def ghcnh_year(sid: str, year: int) -> pd.DataFrame:
    path = _cache("ghcnh", sid, year)
    if path.exists():
        return pd.read_parquet(path)
    raw = get(GHCNH.format(sid=sid, year=year), allow_404=True)
    if raw is None:
        out = EMPTY.copy()
    else:
        d = pd.read_parquet(io.BytesIO(raw))
        cols = [f"sky_cover_summation_{i}" for i in range(1, 5) if f"sky_cover_summation_{i}" in d]
        layers = pd.concat([_okta_from_summation(d[c].astype("string")) for c in cols], axis=1)
        obscured = pd.concat(
            [d[c].astype("string").str.contains(r":(?:09|10)", na=False) for c in cols], axis=1
        ).any(axis=1)
        cloud = layers.max(axis=1).where(~obscured)
        out = pd.DataFrame(
            {
                "cloud": cloud.to_numpy(dtype=float),
                "temp": pd.to_numeric(d["temperature"], errors="coerce").to_numpy(),
                "precip": pd.to_numeric(d.get("precipitation"), errors="coerce").to_numpy(),
            },
            index=pd.DatetimeIndex(pd.to_datetime(d["DATE"]), name="utc"),
        )
    out.to_parquet(path)
    return out


def isdlite_year(sid: str, year: int) -> pd.DataFrame:
    path = _cache("isdlite", sid, year)
    if path.exists():
        return pd.read_parquet(path)
    raw = get(ISDLITE.format(sid=sid, year=year), allow_404=True)
    if raw is None:
        out = EMPTY.copy()
    else:
        cols = ["y", "m", "d", "h", "temp", "dew", "slp", "wdir", "wspd", "sky", "p1", "p6"]
        d = pd.read_csv(io.BytesIO(raw), compression="gzip", sep=r"\s+", header=None, names=cols)
        d = d.replace(-9999, np.nan)
        idx = pd.to_datetime(
            dict(year=d["y"], month=d["m"], day=d["d"], hour=d["h"])
        ).rename("utc")
        sky = d["sky"].where(d["sky"] <= 8)
        out = pd.DataFrame(
            {"cloud": sky.to_numpy(), "temp": (d["temp"] / 10).to_numpy(),
             "precip": (d["p1"] / 10).to_numpy()},
            index=pd.DatetimeIndex(idx),
        )
    out.to_parquet(path)
    return out


def iem_metar_year(station: str, year: int) -> pd.DataFrame:
    path = _cache("iem", station, year)
    if path.exists():
        return pd.read_parquet(path)
    params = [("station", station), ("tz", "Etc/UTC"), ("format", "onlycomma"),
              ("latlon", "no"), ("missing", "M"), ("trace", "0.0001"),
              ("year1", year), ("month1", 1), ("day1", 1),
              ("year2", year + 1), ("month2", 1), ("day2", 1),
              ("report_type", 3), ("report_type", 4)]
    params += [("data", v) for v in ("tmpc", "p01m", "skyc1", "skyc2", "skyc3", "skyc4")]
    raw = get(IEM, params=params)
    d = pd.read_csv(io.BytesIO(raw), na_values=["M"])
    if d.empty:
        out = EMPTY.copy()
    else:
        sky = d[[f"skyc{i}" for i in range(1, 5)]].astype("string")
        oktas = sky.apply(lambda c: c.str.strip().map(METAR_OKTA))
        obscured = sky.apply(lambda c: c.str.strip().eq("VV")).any(axis=1)
        reported = sky.notna().any(axis=1)
        cloud = oktas.max(axis=1).where(reported & ~obscured)
        out = pd.DataFrame(
            {"cloud": cloud.to_numpy(dtype=float), "temp": d["tmpc"].to_numpy(dtype=float),
             "precip": pd.to_numeric(d["p01m"], errors="coerce").to_numpy()},
            index=pd.DatetimeIndex(pd.to_datetime(d["valid"]), name="utc"),
        )
    out.to_parquet(path)
    return out


def _years(loader, sid: str, start: int, end: int) -> pd.DataFrame:
    frames = [loader(sid, y) for y in range(start, end + 1)]
    frames = [f for f in frames if len(f)]
    if not frames:
        return EMPTY.copy()
    out = pd.concat(frames).sort_index()
    return out[~out.index.duplicated(keep="first")]


def nyc_hourly(start: int = 1948, end: int = 2026) -> pd.DataFrame:
    """LaGuardia, with JFK filling hours LaGuardia lacks."""
    lga = _years(ghcnh_year, "USW00014732", start, end)
    jfk = _years(ghcnh_year, "USW00094789", start, end)
    return lga.combine_first(jfk) if len(jfk) else lga


def syd_hourly(start: int = 1948, end: int = 2026) -> pd.DataFrame:
    """ISD-Lite Sydney Intl, with IEM METAR YSSY (2000+) filling missing reports and the
    period after ISD-Lite ends (deviation D1)."""
    isd = _years(isdlite_year, "947670-99999", start, min(end, 2025))
    iem = _years(iem_metar_year, "YSSY", max(start, 2000), end)
    return isd.combine_first(iem)


def daily_window(
    hourly: pd.DataFrame, tz: str, start_h: int = 6, end_h: int = 16, min_obs: int = 3
) -> pd.DataFrame:
    """Per local day: mean cloud/temp over local hours [start_h, end_h), any-rain flag.

    Reports are first averaged within each clock hour so special reports don't get extra
    weight. A variable is NaN for a day with fewer than ``min_obs`` valid hours.
    """
    local = hourly.tz_localize("UTC").tz_convert(tz)
    local = local[(local.index.hour >= start_h) & (local.index.hour < end_h)]
    hourly_means = local.groupby(local.index.floor("h")).mean()
    day = hourly_means.index.tz_localize(None).normalize()
    g = hourly_means.groupby(day)
    n = g.count()
    out = g.mean()
    for c in ("cloud", "temp"):
        out[c] = out[c].where(n[c] >= min_obs)
    out["rain"] = (g["precip"].max() > 0).astype(float).where(n["precip"] > 0)
    out["n_cloud"] = n["cloud"]
    out.index.name = "date"
    return out[["cloud", "temp", "rain", "n_cloud"]]
