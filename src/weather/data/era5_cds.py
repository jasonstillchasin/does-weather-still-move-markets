"""ERA5 hourly point time series from the Copernicus CDS (deviation D5).

Dataset ``reanalysis-era5-single-levels-timeseries``: total cloud cover (0-1) and 2 m
temperature (K) at a point, hourly UTC. Needs ~/.cdsapirc with the user's own CDS key and the
dataset licence accepted on the CDS website. Output matches ``weather_openmeteo.era5_daily``.
"""

from __future__ import annotations

import io
import logging
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from weather.data.hourly import daily_window
from weather.data.net import CACHE

DATASET = "reanalysis-era5-single-levels-timeseries"
DIR = CACHE / "era5_cds"
log = logging.getLogger(__name__)


def slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def path_for(name: str) -> Path:
    return DIR / f"{slug(name)}.parquet"


def _read_csv_payload(raw: bytes) -> pd.DataFrame:
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            frames = [pd.read_csv(z.open(n)) for n in z.namelist() if n.endswith(".csv")]
        return pd.concat(frames, axis=1).loc[:, lambda d: ~d.columns.duplicated()]
    return pd.read_csv(io.BytesIO(raw))


def fetch(name: str, lat: float, lon: float, tz: str, start: str = "1950-01-01",
          end: str = "2026-08-31") -> pd.DataFrame:
    import cdsapi

    out = path_for(name)
    if out.exists():
        return pd.read_parquet(out)
    raw_path = DIR / "raw" / f"{slug(name)}.bin"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_path.exists():
        request = {"variable": ["2m_temperature", "total_cloud_cover"],
                   "location": {"longitude": lon, "latitude": lat},
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
    d = _read_csv_payload(raw_path.read_bytes())
    tcol = next(c for c in d.columns if c.lower() in ("valid_time", "time", "date"))
    hourly = pd.DataFrame(
        {"cloud": d["tcc"].to_numpy(dtype=float) * 8,
         "temp": d["t2m"].to_numpy(dtype=float) - 273.15, "precip": np.nan},
        index=pd.DatetimeIndex(pd.to_datetime(d[tcol]).dt.tz_localize(None), name="utc"),
    )
    daily = daily_window(hourly, tz)[["cloud", "temp"]]
    daily.to_parquet(out)
    return daily
