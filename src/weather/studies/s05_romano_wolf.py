"""Romano-Wolf stepdown for the 9 primary tests (pre-registration section 5, robustness).

Joint stationary bootstrap over the union of all test dates (mean block 10 days, 5,000 reps,
seed 20260927), so dependence across tests and markets is preserved. The statistic for test j
is direction_j * (b*_j - b_j) / se_j, with se_j the original HAC standard error.
"""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from weather.studies import s02_primary as S
from weather.studies.common import OUT

warnings.filterwarnings("ignore")
REPS, BLOCK, SEED = 5000, 10.0, 20260927


def design(df: pd.DataFrame, spec) -> tuple[pd.DataFrame, np.ndarray, int]:
    sid, market, y, wvar, extra, tested, direction = spec
    d = S._prepare(df, wvar) if wvar else df
    xs = [*extra, *(["W"] if wvar and "W" not in extra and tested == "W" else [])]
    if tested not in xs:
        xs.append(tested)
    xs += S._controls(market, y)
    d = d[[y, *xs]].dropna()
    X = np.column_stack([np.ones(len(d)), d[xs].to_numpy()])
    return d, np.column_stack([d[y].to_numpy(), X]), xs.index(tested) + 1


def stationary_positions(n: int, rng: np.random.Generator) -> np.ndarray:
    idx = np.empty(n, dtype=np.int64)
    idx[0] = rng.integers(n)
    new = rng.random(n) < 1 / BLOCK
    fresh = rng.integers(0, n, n)
    for t in range(1, n):
        idx[t] = fresh[t] if new[t] else (idx[t - 1] + 1) % n
    return idx


def main() -> None:
    p = S.panels()
    tests = []
    for spec in S.SPECS:
        d, M, k = design(p[spec[1]], spec)
        e = S.estimate(p[spec[1]], spec, spec[3])
        tests.append(dict(id=spec[0], dates=d.index, M=M, k=k, b=e.coef, se=e.se,
                          dirn=spec[6], t=spec[6] * e.t))
    union = pd.DatetimeIndex(sorted(set().union(*[set(t["dates"]) for t in tests])))
    for t in tests:
        pos = pd.Series(np.arange(len(t["dates"])), index=t["dates"])
        t["map"] = pos.reindex(union).fillna(-1).to_numpy(dtype=np.int64)
    rng = np.random.default_rng(SEED)
    stats = np.empty((REPS, len(tests)))
    for r in range(REPS):
        u = stationary_positions(len(union), rng)
        for j, t in enumerate(tests):
            rows = t["map"][u]
            rows = rows[rows >= 0]
            M = t["M"][rows]
            y, X = M[:, 0], M[:, 1:]
            b = np.linalg.solve(X.T @ X, X.T @ y)[t["k"]]
            stats[r, j] = t["dirn"] * (b - t["b"]) / t["se"]
    # Stepdown: order tests by observed statistic, compare with max over remaining.
    order = np.argsort([-t["t"] for t in tests])
    p_rw = np.empty(len(tests))
    running = 0.0
    for step, j in enumerate(order):
        remaining = order[step:]
        pmax = float(np.mean(stats[:, remaining].max(axis=1) >= tests[j]["t"]))
        running = max(running, pmax)
        p_rw[j] = running
    out = [dict(test=t["id"], t_directional=t["t"], p_romano_wolf=float(p_rw[j]))
           for j, t in enumerate(tests)]
    (OUT / "romano_wolf.json").write_text(json.dumps(out, indent=2))
    print(pd.DataFrame(out).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
