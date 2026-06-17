"""exp_hedge_crashes.py — robustness experiment C: per-crash decomposition (1997–2026).

Pre-registered in regime/PREREGISTRATION_robustness.md (C). The qalpha book lacks pre-2012 data, so
its hedge headline rests almost entirely on COVID. This generalisation test runs the SAME hedge
(h=0.5, τ=0.7, persist=5, lag=1) on the passive Sensex index back to 1997 — which contains crashes of
genuinely different causes — and decomposes hedged-vs-unhedged drawdown event by event.

The cause-agnostic claim (PREREGISTRATION_systemic.md) requires the hedge to cut drawdown in BOTH the
2008 GFC (US-housing contagion) AND COVID (exogenous shock) — not just COVID. Reuses the tested hedge
module; qalpha is never touched (this is a pure index overlay).
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import pandas as pd

from qalpha_research.regime.fragility import compute_fragility
from qalpha_research.regime.hedge import apply_futures_hedge, hedge_active

warnings.filterwarnings("ignore")

TRADING_DAYS = 252.0
TICK = "✅"
CROSS = "❌"

# Pre-committed crash windows (PREREGISTRATION_robustness.md, C). The two DEEP, differently-caused
# events the bar is set on are 2008 and COVID; the rest are milder corrections (bonus, not required).
CRASHES: list[tuple[str, str, str, bool]] = [
    ("GFC 2008 (US housing)", "2008-01-01", "2009-06-30", True),
    ("Euro/downgrade 2011", "2011-07-01", "2012-01-31", False),
    ("China-yuan 2015–16", "2015-08-01", "2016-02-29", False),
    ("IL&FS 2018", "2018-09-01", "2019-03-31", False),
    ("COVID 2020", "2020-01-01", "2020-06-30", True),
    ("Rate-hikes 2022", "2022-01-01", "2022-07-31", False),
]


def _max_dd(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min())


def _cagr(equity: pd.Series) -> float:
    years = len(equity.pct_change().dropna()) / TRADING_DAYS
    return float(equity.iloc[-1] / equity.iloc[0]) ** (1.0 / years) - 1.0 if years > 0 else 0.0


def _md(rows: list[dict[str, object]]) -> str:
    cols = list(rows[0])
    return "\n".join(
        ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
        + ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--panel", default="data/fragility_panel.csv")
    ap.add_argument("--base", default="sensex")
    ap.add_argument("--tau", type=float, default=0.7)
    ap.add_argument("--persist", type=int, default=5)
    ap.add_argument("--h", type=float, default=0.5)
    ap.add_argument("--out", default="reports/hedge_crashes_findings.md")
    args = ap.parse_args()

    panel = pd.read_csv(args.panel, index_col="date", parse_dates=True)
    gauge = compute_fragility(panel).composite
    base = panel[args.base].dropna()
    base_ret = base.pct_change().dropna()
    base_ret = base_ret[base_ret.index >= gauge.dropna().index[0]]
    gauge = gauge.reindex(base_ret.index, method="ffill")

    active = hedge_active(gauge, args.tau, args.persist)
    unhedged = (1.0 + base_ret).cumprod()
    net = apply_futures_hedge(base_ret, base_ret, active, h=args.h, apply_costs=True)
    gross = apply_futures_hedge(base_ret, base_ret, active, h=args.h, apply_costs=False)
    hedged = net.equity

    def _win(s: pd.Series, lo: str, hi: str) -> pd.Series:
        return s[(s.index >= pd.Timestamp(lo)) & (s.index <= pd.Timestamp(hi))]

    rows: list[dict[str, object]] = []
    deep_ok = True
    for name, lo, hi, is_deep in CRASHES:
        u, hd = _win(unhedged, lo, hi), _win(hedged, lo, hi)
        if len(u) < 2:
            continue
        u_dd, h_dd = _max_dd(u) * 100, _max_dd(hd) * 100
        cut = h_dd > u_dd  # less negative = shallower drawdown
        fired = 100.0 * float(_win(active.shift(1).fillna(False), lo, hi).mean())
        if is_deep:
            deep_ok = deep_ok and cut
        rows.append(
            {
                "event": name,
                "unhedged_DD_%": round(u_dd, 1),
                "hedged_DD_%": round(h_dd, 1),
                "DD_cut_pts": round(h_dd - u_dd, 1),
                "hedge_days_%": round(fired, 1),
                "deep": "deep" if is_deep else "—",
                "cut?": TICK if cut else CROSS,
            }
        )

    # calm-year friction: full-window CAGR drag (gross − net); the hedge is dormant outside stress.
    cost_drag = (_cagr(gross.equity) - _cagr(hedged)) * 100
    full_u_dd = _max_dd(unhedged) * 100
    full_h_dd = _max_dd(hedged) * 100

    win = f"{base_ret.index[0].date()} → {base_ret.index[-1].date()}"
    c_verdict = deep_ok and cost_drag < 2.0
    lines = [
        f"# Multi-crash decomposition — {args.base} ({win}) — robustness C",
        "",
        "_Pre-registered: regime/PREREGISTRATION_robustness.md (C). Same hedge as Sprint 2 "
        f"(h={args.h}, τ={args.tau}, persist={args.persist}, lag=1) on the passive {args.base} index. "
        "Bar: cut drawdown in BOTH deep, differently-caused events (2008 GFC **and** COVID), with "
        "calm-year cost drag < 2 CAGR pts._",
        "",
        "## Per-event drawdown (hedged vs unhedged)",
        "",
        _md(rows),
        "",
        f"- Full window: unhedged maxDD {full_u_dd:.1f}% → hedged {full_h_dd:.1f}%.",
        f"- Full-window cost drag (gross − net CAGR): **{cost_drag:.2f} pts** "
        f"(bar < 2.0; hedge fires only in stress, so calm years carry ~no cost).",
        f"- Deep events both cut: **{'yes' if deep_ok else 'no'}** "
        "(2008 contagion + COVID exogenous — different causes ⇒ cause-agnostic).",
        "",
        f"## C verdict: {'PASS' if c_verdict else 'FAIL'}",
        "",
        (
            "- **The hedge is not a COVID one-off.** It cut drawdown in the 2008 GFC (a US-housing "
            "contagion with no Indian bubble) and COVID (a pure exogenous shock) — two crashes with "
            "nothing in common except the transmission symptoms the gauge reads. That is the "
            "cause-agnostic claim holding on out-of-window history."
            if c_verdict
            else "- **The generalisation is weaker than the COVID headline suggested** — see the per-event "
            "table for which deep event was not protected; record honestly and do not promote on one "
            "crash."
        ),
        "",
    ]
    print(f"=== Multi-crash decomposition on {args.base} ({win}) ===")
    print(_md(rows))
    print(f"\ncost drag {cost_drag:.2f} pts · deep both cut: {deep_ok} · C verdict: {c_verdict}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
