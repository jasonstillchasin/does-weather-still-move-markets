"""OLS with Newey-West HAC errors, logit, and one-sided p-values."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import statsmodels.api as sm
from scipy import stats

HAC_LAGS = 5


@dataclass
class Est:
    coef: float
    se: float
    t: float
    p_one: float  # one-sided p in the predicted direction
    n: int
    lo95: float
    hi95: float


def _est(res, name: str, direction: int, n: int) -> Est:
    b, se = float(res.params[name]), float(res.bse[name])
    t = b / se
    p_one = float(stats.norm.sf(direction * t))
    return Est(b, se, t, p_one, n, b - 1.96 * se, b + 1.96 * se)


def ols(df: pd.DataFrame, y: str, xs: list[str], lags: int = HAC_LAGS):
    d = df[[y, *xs]].dropna()
    X = sm.add_constant(d[xs], has_constant="add")
    res = sm.OLS(d[y], X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return res, len(d)


def ols_coef(df, y, xs, name: str, direction: int, lags: int = HAC_LAGS) -> Est:
    res, n = ols(df, y, xs, lags)
    return _est(res, name, direction, n)


def logit_coef(df, y: str, xs: list[str], name: str, direction: int) -> Est:
    d = df[[y, *xs]].dropna()
    up = (d[y] > 0).astype(float)
    X = sm.add_constant(d[xs], has_constant="add")
    res = sm.Logit(up, X).fit(disp=0)
    return _est(res, name, direction, len(d))
