"""Night length and SAD/FALL variables (Kamstra, Kramer and Levi 2003, AER).

KKL: declination lambda_t = 0.4102 sin(2*pi/365 * (doy - 80.25)) and
night length H_t = 24 - 7.72 * arccos(-tan(lat) tan(lambda_t)), using signed latitude.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def night_hours(dates: pd.DatetimeIndex, lat: float) -> pd.Series:
    doy = dates.dayofyear.to_numpy()
    decl = 0.4102 * np.sin(2 * np.pi / 365 * (doy - 80.25))
    x = np.clip(-np.tan(np.radians(lat)) * np.tan(decl), -1.0, 1.0)
    return pd.Series(24 - 7.72 * np.arccos(x), index=dates, name="night_hours")


def _in_window(dates: pd.DatetimeIndex, start: tuple[int, int], end: tuple[int, int]) -> np.ndarray:
    """True where (month, day) lies in [start, end], wrapping over the new year if needed."""
    md = dates.month.to_numpy() * 100 + dates.day.to_numpy()
    s, e = start[0] * 100 + start[1], end[0] * 100 + end[1]
    return (md >= s) & (md <= e) if s <= e else (md >= s) | (md <= e)


def sad_fall(dates: pd.DatetimeIndex, lat: float) -> pd.DataFrame:
    """SAD = H - 12 in local autumn/winter (else 0); FALL = 1 in local autumn."""
    north = lat >= 0
    winter_half = ((9, 21), (3, 20)) if north else ((3, 21), (9, 20))
    autumn = ((9, 21), (12, 20)) if north else ((3, 21), (6, 20))
    h = night_hours(dates, lat)
    sad = np.where(_in_window(dates, *winter_half), h - 12, 0.0)
    fall = _in_window(dates, *autumn).astype(float)
    return pd.DataFrame({"night": h, "sad": sad, "fall": fall}, index=dates)
