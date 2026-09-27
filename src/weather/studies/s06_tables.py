"""LaTeX tables for the paper, built from results/*.json (coefficients in basis points)."""

from __future__ import annotations

import json

import pandas as pd

from weather.studies.common import OUT, TABLES

HYP = {
    "H1-US": "NYC cloud lowers US returns", "H1-AU": "Sydney cloud lowers AU returns",
    "H2-US": "US cloud effect after 2003", "H2-AU": "AU cloud effect after 2003",
    "H3-AU": "AU SAD follows the season", "H4-US": "NYC temperature lowers returns",
    "H4-AU": "Sydney temperature lowers returns", "H5-US": "Effect weakens after NYSE Hybrid",
    "H6-US": "Stronger in small minus big",
}


def _load(name: str):
    return json.loads((OUT / f"{name}.json").read_text())


def _esc(s: str) -> str:
    return (s.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
            .replace("<", "$<$").replace(">", "$>$").replace("±", r"$\pm$")
            .replace("^", r"\^{}"))


def _p(x: float) -> str:
    return "$<$0.001" if x < 0.001 else f"{x:.3f}"


def primary() -> None:
    rows = _load("primary")
    rw = {r["test"]: r["p_romano_wolf"] for r in _load("romano_wolf")}
    plac = pd.read_csv(OUT / "placebo.csv").set_index("test")
    out = [r"\begin{table}[htbp]\centering\footnotesize",
           r"\caption{Pre-registered primary tests. $\beta$ in basis points per one-standard-"
           r"deviation weather shock (for H3, per hour of night beyond 12). One-sided HAC "
           r"$p$-values in the predicted direction; Holm and Romano--Wolf adjust across the "
           r"nine tests. Placebo = share of 100 placebo cities with a coefficient at least as "
           r"extreme (ERA5); Shift = same for 30 year-shifted weather series.}",
           r"\label{tab:primary}",
           r"\resizebox{\textwidth}{!}{%", r"\begin{tabular}{llrcrrrrrrl}\toprule",
           r"ID & Hypothesis & $\beta$ & 95\% CI & $t$ & $p_1$ & Holm & R--W & Placebo "
           r"& Shift & Verdict \\ \midrule"]
    for r in rows:
        pl = plac.loc[r["test"]] if r["test"] in plac.index else None
        pc = f"{pl['pct_city']:.2f}" if pl is not None else "--"
        ps = f"{pl['pct_yearshift']:.2f}" if pl is not None else "--"
        out.append(
            f"{r['test']} & {HYP[r['test']]} & {r['coef'] * 100:+.2f} & "
            f"[{r['lo95'] * 100:+.1f}, {r['hi95'] * 100:+.1f}] & {r['t']:+.2f} & "
            f"{_p(r['p_one'])} & {_p(r['p_holm'])} & {_p(rw[r['test']])} & {pc} & {ps} & "
            f"{r['verdict'].title()} \\\\")
    out += [r"\bottomrule\end{tabular}}\end{table}"]
    (TABLES / "paper_primary.tex").write_text("\n".join(out) + "\n")


def simple(name: str, caption: str, label: str) -> None:
    rows = _load(name)
    out = [r"\begin{table}[htbp]\centering\footnotesize", rf"\caption{{{caption}}}",
           rf"\label{{{label}}}", r"\begin{tabular}{lcrrrr}\toprule",
           r"Specification & Pred. & $\beta$ (bp) & $t$ & $p$ & $N$ \\ \midrule"]
    for r in rows:
        out.append(f"{_esc(r['test'])} & {_esc(r['pred'])} & {r['coef'] * 100:+.2f} & "
                   f"{r['t']:+.2f} & {_p(r['p_one'])} & {r['n']:,} \\\\")
    out += [r"\bottomrule\end{tabular}\end{table}"]
    (TABLES / f"paper_{name}.tex").write_text("\n".join(out) + "\n")


def strategy() -> None:
    s = pd.read_csv(OUT / "strategy.csv")
    body = s[s["cost_bp_roundtrip"].notna()]
    out = [r"\begin{table}[htbp]\centering\footnotesize",
           r"\caption{Cloud-timed SPY open-to-close strategy, 1993--2026. Long SPY from the "
           r"open to the close on days whose 06:00--10:00 New York cloud anomaly is below "
           r"zero (``sunny''), or above it (``cloudy''); otherwise in cash (zero return). "
           r"Costs are per round trip.}", r"\label{tab:strategy}",
           r"\begin{tabular}{lrrrr}\toprule",
           r"Rule & Cost (bp) & Ann.\ return (\%) & Sharpe & Days held \\ \midrule"]
    for r in body.to_dict("records"):
        out.append(f"{r['strategy']} & {r['cost_bp_roundtrip']:.0f} & "
                   f"{r['ann_return_pct']:+.2f} & {r['sharpe']:+.2f} & "
                   f"{int(r['days_in_market']):,} \\\\")
    d = s[s["cost_bp_roundtrip"].isna()].iloc[0]
    out += [r"\midrule", rf"\multicolumn{{5}}{{l}}{{Sunny minus cloudy mornings: "
            rf"{d['ann_return_pct']:+.2f} bp per day ($t = {d['sharpe']:.2f}$), "
            rf"$N = {int(d['n']):,}$}} \\",
            r"\bottomrule\end{tabular}\end{table}"]
    (TABLES / "paper_strategy.tex").write_text("\n".join(out) + "\n")


def main() -> None:
    primary()
    simple("replication", "Replication gate (data up to 2000). Pass = predicted sign with "
           "one-sided $p<0.10$.", "tab:replication")
    simple("robust_weather", "Robustness of the weather tests (exploratory; not "
           "multiplicity-adjusted).", "tab:robust_weather")
    simple("robust_seasonal", "Seasonal tests: SAD, FALL and the Halloween effect "
           "(exploratory).", "tab:robust_seasonal")
    simple("robust_structure", "Market-structure and size tests (exploratory).",
           "tab:robust_structure")
    simple("robust_industry", "US industry returns on weather anomalies, controlling for the "
           "same-day market return (exploratory; two-sided $p$).", "tab:robust_industry")
    strategy()
    print("tables written")


if __name__ == "__main__":
    main()
