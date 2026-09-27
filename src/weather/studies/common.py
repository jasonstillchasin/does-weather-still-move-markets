"""Shared output helpers for study scripts."""

from __future__ import annotations

import json

import pandas as pd

from weather.data.net import ROOT

OUT = ROOT / "results"
TABLES = ROOT / "paper" / "tables"


def fmt_row(r: dict) -> str:
    flag = {True: "PASS", False: "FAIL", None: "info"}[r.get("passed")]
    return (f"{r['test']:<48} pred {r['pred']:>3}  b={r['coef']:+.4f}  se={r['se']:.4f}  "
            f"t={r['t']:+.2f}  p1={r['p_one']:.3f}  n={r['n']}  [{flag}]")


def write_table(rows: list[dict], name: str, caption: str) -> None:
    OUT.mkdir(exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(rows, indent=2, default=str))
    df = pd.DataFrame(rows)
    md = [f"# {caption}", "", "| Test | Pred | β | SE | t | p (1-sided) | N | Verdict |",
          "|---|---|---|---|---|---|---|---|"]
    tex = [r"\begin{table}[htbp]\centering\small", rf"\caption{{{caption}}}",
           r"\begin{tabular}{lcrrrrrc}\toprule",
           r"Test & Pred. & $\beta$ & SE & $t$ & $p_{1}$ & $N$ & Verdict \\ \midrule"]
    for r in df.to_dict("records"):
        v = {True: "pass", False: "fail"}.get(r.get("passed"), "--")
        md.append(f"| {r['test']} | {r['pred']} | {r['coef']:.4f} | {r['se']:.4f} | {r['t']:.2f} "
                  f"| {r['p_one']:.3f} | {r['n']} | {v} |")
        pred = r["pred"].replace("<", "$<$").replace(">", "$>$")
        tex.append(f"{r['test']} & {pred} & {r['coef']:.4f} & {r['se']:.4f} & {r['t']:.2f} & "
                   f"{r['p_one']:.3f} & {r['n']} & {v} \\\\")
    tex += [r"\bottomrule\end{tabular}\end{table}"]
    (OUT / f"{name}.md").write_text("\n".join(md) + "\n")
    (TABLES / f"{name}.tex").write_text("\n".join(tex) + "\n")
