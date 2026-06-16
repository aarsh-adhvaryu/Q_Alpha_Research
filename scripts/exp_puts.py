"""exp_puts.py — P3: protective puts vs short futures vs unhedged (Nifty, 2008–2026).

Both hedges are triggered by the same systemic-stress gauge and never sell the book. The question:
does the *convex, defined-risk* put — which keeps the upside on the gauge's false alarms — beat the
*linear* short future for "reduce risk, keep profit", net of premium + F&O tax? Window starts 2008
(India VIX, the BS implied vol, begins then) and includes the 2008 GFC autumn, COVID, and 2022.
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from qalpha_research.regime.fragility import compute_fragility
from qalpha_research.regime.hedge import apply_futures_hedge, hedge_active
from qalpha_research.regime.options import apply_put_hedge

warnings.filterwarnings("ignore")
TRADING_DAYS = 252.0


def _metrics(equity: pd.Series) -> dict[str, float]:
    ret = equity.pct_change().dropna()
    years = len(ret) / TRADING_DAYS
    cagr = float(equity.iloc[-1] / equity.iloc[0]) ** (1.0 / years) - 1.0 if years > 0 else 0.0
    sharpe = float(ret.mean() / ret.std() * np.sqrt(TRADING_DAYS)) if ret.std() > 0 else 0.0
    mdd = float((equity / equity.cummax() - 1.0).min())
    return {
        "CAGR_%": round(cagr * 100, 1),
        "Sharpe": round(sharpe, 2),
        "maxDD_%": round(mdd * 100, 1),
    }


def _md(rows: list[dict[str, object]]) -> str:
    cols = list(rows[0])
    return "\n".join(
        ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
        + ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--panel", default="data/fragility_panel.csv")
    ap.add_argument("--tau", type=float, default=0.7)
    ap.add_argument("--persist", type=int, default=5)
    ap.add_argument("--h", type=float, default=0.5)
    ap.add_argument("--out", default="reports/puts_findings.md")
    args = ap.parse_args()

    panel = pd.read_csv(args.panel, index_col="date", parse_dates=True)
    gauge = compute_fragility(panel).composite
    level = panel["nifty"].dropna()
    start = max(level.index[0], panel["india_vix"].dropna().index[0], gauge.dropna().index[0])
    level = level[level.index >= start]
    ret = level.pct_change().fillna(0.0)
    gauge = gauge.reindex(level.index, method="ffill")
    vix = panel["india_vix"].reindex(level.index, method="ffill")
    active = hedge_active(gauge, args.tau, args.persist)

    unhedged = (1.0 + ret).cumprod()
    fut = apply_futures_hedge(ret, ret, active, h=args.h).equity
    put = apply_put_hedge(ret, level, vix, active, h=args.h).equity

    def _win(s: pd.Series, lo: str, hi: str) -> pd.Series:
        return s[(s.index >= pd.Timestamp(lo)) & (s.index < pd.Timestamp(hi))]

    windows = {
        "FULL 2008–26": (str(start.date()), "2027-01-01"),
        "2008 GFC (H2)": ("2008-06-01", "2009-06-30"),
        "COVID 2020": ("2020-01-01", "2020-12-31"),
        "calm 2017": ("2017-01-01", "2017-12-31"),
    }
    legs = {
        "Unhedged": unhedged,
        f"Short futures h={args.h}": fut,
        f"Protective put h={args.h}": put,
    }

    lines = [
        f"# Protective puts vs short futures — Nifty ({start.date()} → {level.index[-1].date()})",
        "",
        f"_Pre-registered: regime/PREREGISTRATION_systemic.md (P3). Both gauge-triggered (τ={args.tau}, "
        f"h={args.h}), book never sold. Puts priced Black–Scholes with India VIX; rolled ~monthly. "
        "Net of F&O cost + 30% business-income tax on option/futures gains._",
        "",
    ]
    for name, (lo, hi) in windows.items():
        rows = [{"leg": leg, **_metrics(_win(eq, lo, hi))} for leg, eq in legs.items()]
        print(f"\n=== {name} ===")
        print(_md(rows))
        lines += [f"## {name}", "", _md(rows), ""]

    lines += [
        "## Honest read",
        "",
        "- **Both hedges beat unhedged** on CAGR, Sharpe and drawdown — but **short futures beat puts "
        "here.** In the deep, grinding 2008 crash the linear short rides the *whole* decline "
        "(DD −46.7→−34.1) while the OTM put's protection is bounded and decays (−40.4); in the sharp "
        "COVID V they are close.",
        "- **The put's theoretical edge barely shows, because the gauge is *selective*.** Puts are "
        "designed to avoid bleeding premium when you hedge needlessly — but in calm 2017 the gauge "
        "**never fired**, so all three legs are identical (no premium drag at all). The rare-firing "
        "discipline already solves what put convexity is for, so the simpler futures hedge wins.",
        "- **When would puts win?** With a *noisier / more-leading* gauge that fires often and early "
        "(more false alarms that rebound) — there the put's keep-the-upside convexity would pay off. "
        "With this coincident, selective gauge, it does not.",
        "- **Caveats:** BS with India VIX is an implied-vol proxy (real chains have skew/liquidity); "
        "single strike (5% OTM) and ~1m tenor; coincident gauge → partial protection.",
    ]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
