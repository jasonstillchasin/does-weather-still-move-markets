"""Weather anomalies relative to an ISO-week climatology.

Primary (pre-registration 3.2): trailing climatology from the same ISO week in the previous
30 calendar years, strictly before the observation's year, requiring at least 5 years.
Replication: a full-sample ISO-week mean (Hirshleifer and Shumway 2003).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _week(idx: pd.DatetimeIndex) -> np.ndarray:
    return np.minimum(idx.isocalendar().week.to_numpy(dtype=int), 52)


def trailing_anomaly(
    x: pd.Series, window_years: int = 30, min_years: int = 5, standardise: bool = True
) -> pd.Series:
    """(x - m) / s using same-ISO-week values from years [y - window_years, y - 1]."""
    x = x.dropna()
    idx = pd.DatetimeIndex(x.index)
    df = pd.DataFrame({"x": x.to_numpy(), "year": idx.year, "week": _week(idx)}, index=idx)
    df["x2"] = df["x"] ** 2
    g = df.groupby(["week", "year"]).agg(n=("x", "count"), s=("x", "sum"), ss=("x2", "sum"))
    years = np.arange(df["year"].min(), df["year"].max() + 1)
    full = pd.MultiIndex.from_product([range(1, 53), years], names=["week", "year"])
    g = g.reindex(full, fill_value=0.0)
    g["has"] = (g["n"] > 0).astype(float)
    # Rolling sums over the previous window_years years, excluding the current year.
    roll = (
        g.groupby(level="week")[["n", "s", "ss", "has"]]
        .apply(lambda w: w.rolling(window_years, min_periods=1).sum().shift(1))
        .droplevel(0)
    )
    n = roll["n"]
    mean = roll["s"] / n
    var = (roll["ss"] - n * mean**2) / (n - 1)
    ok = roll["has"] >= min_years
    clim = pd.DataFrame({"m": mean.where(ok), "sd": np.sqrt(var).where(ok)})
    key = pd.MultiIndex.from_arrays([df["week"], df["year"]])
    m = clim["m"].reindex(key).to_numpy()
    sd = clim["sd"].reindex(key).to_numpy()
    out = df["x"].to_numpy() - m
    if standardise:
        out = out / sd
    return pd.Series(out, index=idx, name=x.name).dropna()


def fullsample_anomaly(x: pd.Series, standardise: bool = True) -> pd.Series:
    x = x.dropna()
    wk = _week(pd.DatetimeIndex(x.index))
    grp = x.groupby(wk)
    out = x - grp.transform("mean")
    if standardise:
        out = out / grp.transform("std")
    return out.rename(x.name)
