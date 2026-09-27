import math

import numpy as np
import pandas as pd
import pytest

from weather.data.placebo_cities import CITIES, PLACEBO_CITIES
from weather.features.daylight import night_hours, sad_fall
from weather.features.deseason import trailing_anomaly


@pytest.mark.parametrize(
    "city,date,daylight_h",
    [
        ("NYC", "2024-06-21", 15 + 5 / 60),
        ("NYC", "2024-12-21", 9 + 15 / 60),
        ("SYD", "2024-06-21", 9 + 53 / 60),
        ("SYD", "2024-12-21", 14 + 25 / 60),
    ],
)
def test_night_length_matches_published_daylight(city, date, daylight_h):
    lat = CITIES[city][0]
    night = night_hours(pd.DatetimeIndex([date]), lat).iloc[0]
    # KKL's 7.72 constant is an approximation; 15 minutes is its known accuracy.
    assert abs((24 - night) - daylight_h) < 0.25


def test_sad_fall_hemispheres_are_opposite():
    d = pd.DatetimeIndex(["2024-01-15", "2024-07-15", "2024-10-15", "2024-04-15"])
    n = sad_fall(d, CITIES["NYC"][0])
    s = sad_fall(d, CITIES["SYD"][0])
    assert n["sad"].iloc[0] > 0 and n["sad"].iloc[1] == 0
    assert s["sad"].iloc[0] == 0 and s["sad"].iloc[1] > 0
    assert n["fall"].tolist() == [0, 0, 1, 0]
    assert s["fall"].tolist() == [0, 0, 0, 1]


def test_trailing_anomaly_has_no_lookahead():
    rng = np.random.default_rng(0)
    idx = pd.date_range("1970-01-01", "2010-12-31", freq="D")
    x = pd.Series(rng.normal(size=len(idx)), index=idx)
    a = trailing_anomaly(x)
    x2 = x.copy()
    x2.loc["2000-01-01":] += 100.0  # change the future only
    a2 = trailing_anomaly(x2)
    common = a.loc[:"1999-12-31"].index
    assert np.allclose(a.loc[common], a2.loc[common])
    # First usable year needs 5 prior years.
    assert a.index.min().year == 1975


def test_trailing_anomaly_removes_seasonal_cycle():
    idx = pd.date_range("1950-01-01", "2020-12-31", freq="D")
    season = 10 * np.sin(2 * np.pi * idx.dayofyear / 365.25)
    x = pd.Series(season + np.random.default_rng(1).normal(size=len(idx)), index=idx)
    a = trailing_anomaly(x)
    assert abs(a.corr(pd.Series(season, index=idx).reindex(a.index))) < 0.05
    assert 0.8 < a.std() < 1.5


def _km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    c = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)
    return 6371 * math.acos(min(1.0, max(-1.0, c)))


def test_placebo_cities_rule():
    assert len(PLACEBO_CITIES) == 100
    assert len({c[0] for c in PLACEBO_CITIES}) == 100
    for name, lat, lon, _ in PLACEBO_CITIES:
        for ex in ("NYC", "SYD"):
            elat, elon, _ = CITIES[ex]
            assert _km(lat, lon, elat, elon) > 1000, (name, ex)
