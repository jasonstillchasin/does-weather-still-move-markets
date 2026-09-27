"""Paper figures: placebo-city distributions and rolling cloud coefficients."""

from __future__ import annotations

import warnings

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from weather.data.net import ROOT  # noqa: E402
from weather.data.placebo_cities import CITIES, PLACEBO_CITIES  # noqa: E402
from weather.models.regress import ols_coef  # noqa: E402
from weather.studies import s02_primary as S  # noqa: E402

warnings.filterwarnings("ignore")
FIGS = ROOT / "paper" / "figs"
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e6e5e1"
BAR = "#b7d3f6"

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.bbox": "tight",
})


def placebo_figure(p: dict[str, pd.DataFrame]) -> None:
    home = {"US": "NYC", "AU": "SYD"}
    label = {"US": "New York cloud → US market", "AU": "Sydney cloud → Australian market"}
    placebo_w = {c[0]: S.era5_anomalies(*c) for c in PLACEBO_CITIES}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
    for ax, sid, color in zip(axes, ("H1-US", "H1-AU"), (BLUE, ORANGE), strict=True):
        spec = next(s for s in S.SPECS if s[0] == sid)
        market = spec[1]
        base = p[market].drop(columns=["cloud_z", "temp_z"])
        bs = np.array([S.estimate(base.join(w[["cloud_z"]]), spec, "cloud_z").coef
                       for w in placebo_w.values()]) * 100
        real = S.era5_anomalies(home[market], *CITIES[home[market]])
        b = S.estimate(base.join(real[["cloud_z"]]), spec, "cloud_z").coef * 100
        ax.hist(bs, bins=np.arange(-3.0, 3.01, 0.25), color=BAR, edgecolor="white",
                linewidth=1.0)
        ax.axvline(b, color=color, linewidth=2)
        share = np.mean(bs <= b)
        ax.text(b, ax.get_ylim()[1] * 0.92,
                f"  {home[market]}: {b:.1f} bp\n  {share:.0%} of placebos ≤",
                color=INK, fontsize=8, va="top", ha="left" if b < 0 else "right")
        ax.set_title(label[market], fontsize=9, color=INK, loc="left")
        ax.set_xlabel("Cloud coefficient (bp per 1 SD)")
    axes[0].set_ylabel("Placebo cities")
    axes[0].yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    fig.savefig(FIGS / "placebo_h1.pdf")
    fig.savefig(FIGS / "placebo_h1.png", dpi=200)
    plt.close(fig)


def rolling_figure(p: dict[str, pd.DataFrame], window_years: int = 10) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
    for ax, market, color in zip(axes, ("US", "AU"), (BLUE, ORANGE), strict=True):
        df = p[market]
        ctrl = S._controls(market, "r")
        years = range(df.index.year.min() + window_years - 1, 2027)
        rows = []
        for y in years:
            d = df.loc[f"{y - window_years + 1}":f"{y}"]
            if d["cloud_z"].notna().sum() < 1500:
                continue
            e = ols_coef(d, "r", ["cloud_z", *ctrl], "cloud_z", -1)
            rows.append((y, e.coef * 100, e.lo95 * 100, e.hi95 * 100))
        r = pd.DataFrame(rows, columns=["year", "b", "lo", "hi"]).set_index("year")
        ax.fill_between(r.index, r.lo, r.hi, color=color, alpha=0.15, linewidth=0)
        ax.plot(r.index, r.b, color=color, linewidth=2)
        ax.axhline(0, color=MUTED, linewidth=0.8)
        ax.axvline(2003.5, color=MUTED, linewidth=0.8, linestyle="--")
        ax.text(2003.8, 5.6, "HS 2003\npublished", fontsize=7,
                color=MUTED, va="top")
        city = "New York" if market == "US" else "Sydney"
        ax.set_title(f"{city} cloud, trailing {window_years}-year window", fontsize=9,
                     color=INK, loc="left")
        ax.set_xlabel("Window end year")
    axes[0].set_ylabel("Coefficient (bp per 1 SD), 95% CI")
    axes[0].set_ylim(-8, 6)
    fig.savefig(FIGS / "rolling_cloud.pdf")
    fig.savefig(FIGS / "rolling_cloud.png", dpi=200)
    plt.close(fig)


def main() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    p = S.panels()
    placebo_figure(p)
    rolling_figure(p)
    print("figures written to", FIGS)


if __name__ == "__main__":
    main()
