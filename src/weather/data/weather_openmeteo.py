"""ERA5 hourly cloud cover and temperature from the Open-Meteo archive API (no key).

Used for placebo-city inference and as a single-source robustness check for NYC and Sydney
(pre-registration section 6). Cloud cover (%) is converted to oktas (x 8/100).
"""

from __future__ import annotations

import json
import logging
import time

import numpy as np
import pandas as pd
import requests

from weather.data.hourly import daily_window
from weather.data.net import CACHE, HEADERS

URL = "https://archive-api.open-meteo.com/v1/archive"
log = logging.getLogger(__name__)


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def era5_daily(name: str, lat: float, lon: float, tz: str, start: str = "1950-01-01",
               end: str = "2026-08-31") -> pd.DataFrame:
    """Daily 06:00-16:00 local cloud (oktas) and temperature from ERA5 hourly data."""
    path = CACHE / "era5" / f"{_slug(name)}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    params = {"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
              "hourly": "cloud_cover,temperature_2m", "timezone": "UTC", "timeformat": "unixtime"}
    for attempt in range(12):
        r = requests.get(URL, params=params, headers=HEADERS, timeout=300)
        if r.status_code == 200:
            break
        wait = min(3600, 60 * 2**attempt) if r.status_code == 429 else 2**attempt
        log.warning("%s: HTTP %s (%s); retry in %ss", name, r.status_code, r.text[:120], wait)
        time.sleep(wait)
    else:
        raise RuntimeError(f"Open-Meteo failed for {name}")
    h = json.loads(r.content)["hourly"]
    hourly = pd.DataFrame(
        {"cloud": np.asarray(h["cloud_cover"], dtype=float) * 8 / 100,
         "temp": np.asarray(h["temperature_2m"], dtype=float), "precip": np.nan},
        index=pd.DatetimeIndex(pd.to_datetime(h["time"], unit="s"), name="utc"),
    )
    d = daily_window(hourly, tz)[["cloud", "temp"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    d.to_parquet(path)
    return d
