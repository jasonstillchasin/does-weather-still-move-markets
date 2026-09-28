"""ERA5 point series with the full Study 2 variable set, from the Copernicus CDS.

Daily aggregates over 06:00-16:00 local time:
  cloud  mean total cloud cover (oktas)          sun    solar radiation, MJ/m^2 (sum)
  temp   mean 2 m temperature (deg C)            humid  mean relative humidity (%)
  press  mean sea-level pressure (hPa)           wind   mean 10 m wind speed (m/s)
  rain   precipitation (mm, sum)                 gust   max 10 m wind gust (m/s)
ERA5 accumulations (ssrd, tp) at valid_time cover the preceding hour, so they are shifted back
one hour before windowing. Instantaneous fields use their valid_time.
"""

from __future__ import annotations

import logging
import time

import numpy as np
import pandas as pd

from weather.data.era5_cds import _read_csv_payload, slug
from weather.data.net import CACHE

DATASET = "reanalysis-era5-single-levels-timeseries"
DIR = CACHE / "era5_full"
VARS = ["2m_temperature", "2m_dewpoint_temperature", "total_cloud_cover",
        "surface_solar_radiation_downwards", "10m_u_component_of_wind",
        "10m_v_component_of_wind", "mean_sea_level_pressure", "total_precipitation",
        "10m_wind_gust_since_previous_post_processing"]
log = logging.getLogger(__name__)


def path_for(name: str):
    return DIR / f"{slug(name)}.parquet"


def _rh(t_c: np.ndarray, td_c: np.ndarray) -> np.ndarray:
    """Relative humidity (%) from temperature and dew point (Magnus formula)."""
    a, b = 17.625, 243.04
    return 100 * np.exp(a * td_c / (b + td_c) - a * t_c / (b + t_c))


def _window(s: pd.Series, tz: str, how: str, start_h: int = 6, end_h: int = 16,
            min_obs: int = 3) -> pd.Series:
    local = s.tz_localize("UTC").tz_convert(tz)
    local = local[(local.index.hour >= start_h) & (local.index.hour < end_h)]
    day = local.index.tz_localize(None).normalize()
    g = local.groupby(day)
    out = g.agg(how)
    return out.where(g.count() >= min_obs)


def daily(raw: pd.DataFrame, tz: str) -> pd.DataFrame:
    tcol = next(c for c in raw.columns if c.lower() in ("valid_time", "time", "date"))
    idx = pd.DatetimeIndex(pd.to_datetime(raw[tcol]).dt.tz_localize(None), name="utc")
    h = raw.set_index(idx)
    t, td = h["t2m"] - 273.15, h["d2m"] - 273.15
    inst = {
        "cloud": (h["tcc"] * 8, "mean"), "temp": (t, "mean"),
        "humid": (pd.Series(_rh(t.to_numpy(), td.to_numpy()), index=idx), "mean"),
        "press": (h["msl"] / 100, "mean"),
        "wind": (np.hypot(h["u10"], h["v10"]), "mean"), "gust": (h["fg10"], "max"),
    }
    out = {k: _window(v, tz, how) for k, (v, how) in inst.items()}
    shifted = idx - pd.Timedelta(hours=1)  # accumulation over the hour ending at valid_time
    out["sun"] = _window(pd.Series(h["ssrd"].to_numpy() / 1e6, index=shifted), tz, "sum")
    out["rain"] = _window(pd.Series(h["tp"].to_numpy() * 1000, index=shifted), tz, "sum")
    d = pd.DataFrame(out)
    d.index.name = "date"
    return d


def fetch(name: str, lat: float, lon: float, tz: str, start: str = "1950-01-01",
          end: str = "2026-08-31") -> pd.DataFrame:
    import cdsapi

    out = path_for(name)
    if out.exists():
        return pd.read_parquet(out)
    raw_path = DIR / "raw" / f"{slug(name)}.bin"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_path.exists():
        request = {"variable": VARS, "location": {"longitude": lon, "latitude": lat},
                   "date": [f"{start}/{end}"], "data_format": "csv"}
        client = cdsapi.Client(quiet=True, progress=False)
        for attempt in range(40):
            try:
                client.retrieve(DATASET, request).download(str(raw_path))
                break
            except Exception as e:  # CDS rejects jobs while the user's queue is full
                if "queued requests" not in str(e) and "rejected" not in str(e):
                    raise
                wait = min(600, 30 * (attempt + 1))
                log.warning("%s: CDS queue limit, retry in %ss", name, wait)
                time.sleep(wait)
        else:
            raise RuntimeError(f"CDS kept rejecting {name}")
    d = daily(_read_csv_payload(raw_path.read_bytes()), tz)
    d.to_parquet(out)
    return d
