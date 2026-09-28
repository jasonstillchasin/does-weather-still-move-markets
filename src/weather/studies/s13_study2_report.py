"""Study 2 tables and figures for the paper (reads results/study2_*.json/csv)."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from weather.data.exchanges import EXCHANGES  # noqa: E402
from weather.studies.common import OUT, TABLES  # noqa: E402
from weather.studies.s04_figures import BLUE, FIGS, GRID, INK, MUTED, ORANGE  # noqa: E402

LABEL = {"cloud_z": "Cloud", "sun_z": "Sunshine", "temp_z": "Temperature", "wind_z": "Wind",
         "rain_a": "Rain day", "humid_z": "Humidity", "press_z": "Pressure", "sad": "SAD"}
HYP = {"S1": "Cloud (full sample)", "S2": "Cloud, 1998 onward", "S3": "Sunshine",
       "S4": "Temperature", "S5": "Wind", "S6": "Rain day", "S7": "Humidity (two-sided)",
       "S8": "Pressure (two-sided)", "S9": "SAD follows local season"}
DIVERGING = LinearSegmentedColormap.from_list(
    "bluered", ["#104281", "#2a78d6", "#f0efec", "#e34948", "#8e1f1e"])


def _p(x: float) -> str:
    return "$<$0.001" if x < 0.001 else f"{x:.3f}"


def primary_table() -> None:
    rows = json.loads((OUT / "study2_primary.json").read_text())
    out = [r"\begin{table}[htbp]\centering\footnotesize",
           r"\caption{Study 2 pre-registered primary tests, pooled over 26 exchanges not used in "
           r"Study 1. $\beta$ is in percent of a daily return standard deviation per one-SD "
           r"weather shock (rain: per rain day relative to its climatological frequency); bp "
           r"converts at the median daily volatility. Driscoll--Kraay standard errors. Placebo = "
           r"number of the 200 random placebo-city assignments at least as extreme.}",
           r"\label{tab:s2primary}", r"\resizebox{\textwidth}{!}{%",
           r"\begin{tabular}{llrrrrrrrl}\toprule",
           r"ID & Weather variable & $\beta$ (\% SD) & bp & $t$ & $p$ & Holm & Placebo & $N$ "
           r"& Verdict \\ \midrule"]
    for r in rows:
        pl = "--" if r["pct_placebo"] is None or r["pct_placebo"] != r["pct_placebo"] \
            else f"{round(r['pct_placebo'] * 200)}/200"
        out.append(f"{r['test']} & {HYP[r['test']]} & {r['coef'] * 100:+.2f} & "
                   f"{r['bp_at_median_sigma']:+.2f} & {r['t']:+.2f} & {_p(r['p'])} & "
                   f"{_p(r['p_holm'])} & {pl} & {r['n']:,} & {r['verdict'].title()} \\\\")
    out += [r"\bottomrule\end{tabular}}\end{table}"]
    (TABLES / "paper_s2_primary.tex").write_text("\n".join(out) + "\n")


def split_table(sec: pd.DataFrame) -> None:
    groups = ["pre-2003", "post-2003", "developed", "emerging", "northern", "southern",
              "joint model"]
    vars_ = ["cloud_z", "sun_z", "temp_z", "wind_z", "rain_a", "humid_z", "press_z"]
    out = [r"\begin{table}[htbp]\centering\footnotesize",
           r"\caption{Study 2 exploratory splits (26 exchanges). Cells: $\beta$ in percent of "
           r"a daily SD, with $t$-statistics in parentheses. ``Joint'' enters all seven "
           r"anomalies in one regression.}", r"\label{tab:s2splits}",
           r"\resizebox{\textwidth}{!}{%", r"\begin{tabular}{l" + "r" * len(groups) + r"}\toprule",
           "Variable & " + " & ".join(g.replace("joint model", "Joint").capitalize()
                                       for g in groups) + r" \\ \midrule"]
    for v in vars_:
        cells = []
        for g in groups:
            r = sec[(sec.group == g) & (sec["var"] == v)].iloc[0]
            cells.append(f"{r['coef'] * 100:+.2f} ({r['t']:+.1f})")
        out.append(f"{LABEL[v]} & " + " & ".join(cells) + r" \\")
    out += [r"\bottomrule\end{tabular}}\end{table}"]
    (TABLES / "paper_s2_splits.tex").write_text("\n".join(out) + "\n")


def decay_figure(sec: pd.DataFrame) -> None:
    vars_ = ["cloud_z", "sun_z", "rain_a", "press_z", "humid_z", "temp_z", "wind_z"]
    fig, ax = plt.subplots(figsize=(7.0, 2.8))
    x = np.arange(len(vars_))
    for off, g, color in ((-0.15, "pre-2003", BLUE), (0.15, "post-2003", ORANGE)):
        rows = [sec[(sec.group == g) & (sec["var"] == v)].iloc[0] for v in vars_]
        b = np.array([r["coef"] for r in rows]) * 100
        se = np.array([r["coef"] / r["t"] for r in rows]) * 100
        ax.errorbar(x + off, b, yerr=1.96 * se, fmt="o", color=color, markersize=6,
                    elinewidth=2, capsize=0, label={"pre-2003": "Before July 2003",
                                              "post-2003": "July 2003 onward"}[g])
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_xticks(x, [LABEL[v] for v in vars_])
    ax.set_ylabel("β, % of daily SD (95% CI)")
    ax.set_title("Weather effects across 26 exchanges, before and after 2003", loc="left",
                 fontsize=9, color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.grid(axis="x", visible=False)
    fig.savefig(FIGS / "s2_decay.pdf")
    fig.savefig(FIGS / "s2_decay.png", dpi=200)
    plt.close(fig)


def heatmap(per: pd.DataFrame) -> None:
    order = [e[0] for e in EXCHANGES]
    vars_ = ["cloud_z", "sun_z", "rain_a", "press_z", "humid_z", "temp_z", "wind_z"]
    t = per.pivot(index="exchange", columns="var", values="t").reindex(order)[vars_]
    rej = per.pivot(index="exchange", columns="var", values="fdr_reject").reindex(order)[vars_]
    fig, ax = plt.subplots(figsize=(5.2, 7.6))
    im = ax.imshow(t.clip(-4, 4).to_numpy(), cmap=DIVERGING, vmin=-4, vmax=4, aspect="auto")
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            val = t.iat[i, j]
            star = "*" if bool(rej.iat[i, j]) else ""
            ax.text(j, i, f"{val:+.1f}{star}", ha="center", va="center", fontsize=6.5,
                    color="white" if abs(val) > 2.6 else INK,
                    fontweight="bold" if star else "normal")
    ax.set_xticks(range(len(vars_)), [LABEL[v] for v in vars_], rotation=35, ha="right")
    ax.set_yticks(range(len(order)), order)
    ax.grid(False)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.5, pad=0.02)
    cb.set_label("t-statistic (positive = higher returns)", fontsize=8)
    cb.outline.set_visible(False)
    ax.set_title("Per-exchange weather effects (* = FDR 10%)", loc="left", fontsize=9,
                 color=INK)
    fig.savefig(FIGS / "s2_heatmap.pdf")
    fig.savefig(FIGS / "s2_heatmap.png", dpi=200)
    plt.close(fig)


def main() -> None:
    sec = pd.DataFrame(json.loads((OUT / "study2_secondary.json").read_text()))
    per = pd.read_csv(OUT / "study2_per_exchange.csv")
    primary_table()
    split_table(sec)
    decay_figure(sec)
    heatmap(per)
    _ = GRID
    print("study 2 tables and figures written")


if __name__ == "__main__":
    main()
