"""The low-turnover QUBO on the CLEAN universe (PREREGISTRATION_qubo_lowturnover.md).

Stage A's committed follow-up: QUBO selection lost to 1/N by −2.7pt with ₹273k of reselection tax on
a survivorship-biased universe. This run removes both confounds at once — the **point-in-time
Nifty-50** (dead names in; the validated core's own universe, so the bar is fair) and an **incumbency
switching-cost term** (`μ_eff = μ + c·held`, c = 0.02 fixed from the real round-trip friction, NOT
tuned) so a held name is only replaced when the challenger clears the cost of switching. The plain
QUBO runs alongside as the attribution control. Executed through qalpha's `Portfolio.rebalance`
(real FIFO cost + capital-gains tax; qalpha unmodified).

Run: uv run python scripts/exp_qubo_lowturnover.py --qalpha ../Q_Alpha
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from qalpha.backtest.baselines import equal_weight_pit
from qalpha.backtest.metrics import compute_metrics, max_drawdown
from qalpha.backtest.portfolio import Portfolio, to_decimal_price
from qalpha.config import Config
from qalpha.data.ingest import load_parquet
from qalpha.data.universe import Universe

from qalpha_research.quantum.qubo import build_portfolio_qubo
from qalpha_research.quantum.solvers import solve_simulated_annealing

START, END = "2012-01-01", "2024-12-31"
LOOKBACK = 252  # trailing window for μ/Σ (causal: strictly before the rebalance day)
K = 20  # cardinality (pre-registered, = Stage A)
RISK_AVERSION = 1.0
INCUMBENCY = 0.02  # V1's switching-cost term (2%/yr ≈ real round-trip friction; fixed, not tuned)
SA_STEPS, SA_RESTARTS, SA_SEED = 6000, 4, 0


def _annual_rebalance_days(dates: pd.DatetimeIndex) -> list[pd.Timestamp]:
    out: list[pd.Timestamp] = []
    for yr in sorted({d.year for d in dates}):
        days = dates[dates.year == yr]
        if len(days):
            out.append(days[0])
    return out


def _ann(curve: pd.Series) -> float:
    years = max((curve.index[-1] - curve.index[0]).days / 365.25, 1e-9)
    return float((curve.iloc[-1] / curve.iloc[0]) ** (1.0 / years) - 1.0)


def _rolling(curve: pd.Series, window: int = 756) -> pd.Series:
    ratio = (curve.shift(-window) / curve).dropna()
    return ratio ** (252.0 / window) - 1.0


@dataclass
class VariantResult:
    name: str
    equity: pd.Series
    tax: Decimal
    rebalances: int
    switches: list[int]  # names sold per rebalance (realized reselection churn)


def _run_variant(
    *,
    name: str,
    incumbency: float,
    adj: pd.DataFrame,
    rets: pd.DataFrame,
    universe: Universe,
    trading_days: pd.DatetimeIndex,
    rebal_days: set[pd.Timestamp],
    cfg: Config,
) -> VariantResult:
    """One walk-forward pass. ``incumbency`` = 0 is the plain-QUBO control; > 0 is the low-turnover
    variant (held names' μ raised by that amount inside the QUBO — replace only if worth the switch)."""
    portfolio = Portfolio(cfg.cost, cfg.tax, cash=cfg.capital.starting_capital)
    equity_rows: list[tuple[pd.Timestamp, float]] = []
    tax = Decimal("0")
    rebalances = 0
    switches: list[int] = []

    for d in trading_days:
        # One typed price map per day (dropna → only really-priced names appear).
        row_px: dict[str, float] = {
            str(t): fv for t, v in adj.loc[d].dropna().items() if (fv := float(str(v))) > 0
        }
        if d in rebal_days:
            members = universe.members_on(d.date())
            window = rets.loc[:d].iloc[:-1].tail(LOOKBACK)
            valid = [
                t
                for t in window.columns
                if t in members and t in row_px and window[t].notna().all()
            ]
            if len(valid) >= K:
                held = set(portfolio.positions())
                mu = window[valid].mean().to_numpy() * 252.0
                cov = window[valid].cov().to_numpy() * 252.0
                # The one pre-registered change: incumbents' expected return is raised by the fixed
                # switching cost, so a challenger must beat the real friction of replacing them.
                mu_eff = mu + incumbency * np.array(
                    [1.0 if t in held else 0.0 for t in valid], dtype=np.float64
                )
                qubo = build_portfolio_qubo(mu_eff, cov, K, risk_aversion=RISK_AVERSION)
                sel, _ = solve_simulated_annealing(
                    qubo, steps=SA_STEPS, restarts=SA_RESTARTS, seed=SA_SEED
                )
                picks = [valid[i] for i in range(len(valid)) if sel[i] == 1]
                if picks:
                    weights = pd.Series(1.0 / len(picks), index=picks)
                    prices_dec = {t: to_decimal_price(p) for t, p in row_px.items()}
                    records = portfolio.rebalance(
                        d.date(), weights, prices_dec, min_trade_fraction=0.0
                    )
                    tax += sum((r.tax for r in records), Decimal("0"))
                    switches.append(len(held - set(picks)))
                    rebalances += 1

        prices_dec = {t: to_decimal_price(p) for t, p in row_px.items()}
        equity_rows.append((d, float(portfolio.market_value(prices_dec))))

    eq = pd.Series(dict(equity_rows)).sort_index()
    return VariantResult(name=name, equity=eq, tax=tax, rebalances=rebalances, switches=switches)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qalpha", default="../Q_Alpha")
    ap.add_argument("--out", default="reports/qubo_lowturnover_findings.md")
    args = ap.parse_args()

    qroot = Path(args.qalpha)
    cfg = Config()
    prices = load_parquet(qroot / "data/historical/prices_pit_2026.parquet")
    universe = Universe.from_csv(str(qroot / "data/universes/nifty50_membership_2026.csv"))

    adj = prices.adj_close
    rets = adj.pct_change()
    trading_days = pd.DatetimeIndex(
        [d for d in adj.index if START <= d.strftime("%Y-%m-%d") <= END]
    )
    rebal_days = set(_annual_rebalance_days(trading_days))

    def run(name: str, c: float) -> VariantResult:
        return _run_variant(
            name=name,
            incumbency=c,
            adj=adj,
            rets=rets,
            universe=universe,
            trading_days=trading_days,
            rebal_days=rebal_days,
            cfg=cfg,
        )

    v1 = run("V1 low-turnover QUBO (c=0.02)", INCUMBENCY)
    v0 = run("V0 plain QUBO (control)", 0.0)

    idx = pd.DatetimeIndex(v1.equity.index)
    one_n = equal_weight_pit(prices, universe, idx, cfg.capital.starting_capital)
    n_cagr = _ann(one_n)
    n_mtr = compute_metrics(one_n, "Y")
    roll_n = _rolling(one_n)

    lines = [
        "# The low-turnover QUBO on the CLEAN universe (PIT Nifty-50, net cost + tax)\n",
        "Pre-reg: `reports/PREREGISTRATION_qubo_lowturnover.md` — Stage A's committed follow-up. "
        "Clean point-in-time universe (dead names in) → a real verdict, unlike the static-100 run. "
        f"Config: annual 2012–2024 · k={K} · q={RISK_AVERSION} · SA({SA_STEPS}×{SA_RESTARTS}, "
        f"seed {SA_SEED}) · band 0 · incumbency c={INCUMBENCY} (V1 only, fixed pre-run). "
        "qalpha reused unmodified (Portfolio FIFO cost+tax).\n",
        "## Full-window (net cost + tax)\n",
        "| series | CAGR | Sharpe | maxDD | tax | rebal | vs 1/N |",
        "|---|---|---|---|---|---|---|",
    ]
    verdict_v1 = ""
    for v in (v1, v0):
        cagr = _ann(v.equity)
        mtr = compute_metrics(v.equity, "Y")
        roll = _rolling(v.equity)
        rs, rn = roll.align(roll_n, join="inner")
        gap = rs - rn
        lines.append(
            f"| **{v.name}** | {cagr * 100:.1f}% | {mtr.sharpe:.2f} | "
            f"{max_drawdown(v.equity) * 100:.1f}% | ₹{float(v.tax):,.0f} | {v.rebalances} | "
            f"**{(cagr - n_cagr) * 100:+.1f}pt** |"
        )
        if v is v1:
            beats_full = cagr > n_cagr
            median_gap = float(gap.median())
            pct_ge = float((gap >= 0).mean()) * 100
            worst = float(gap.min())
            verdict_v1 = (
                f"\n## Pre-registered verdict (V1)\n\n"
                f"- Full-window CAGR vs 1/N: **{(cagr - n_cagr) * 100:+.1f}pt** → "
                f"{'PASSES' if beats_full else 'FAILS'} leg 1.\n"
                f"- Rolling-3y-hold gap: median **{median_gap * 100:+.1f}pt**, ≥1/N in "
                f"**{pct_ge:.0f}%** of holds, worst **{worst * 100:+.1f}pt** → "
                f"{'PASSES' if median_gap >= 0 else 'FAILS'} leg 2.\n"
                f"- Switching churn: names sold per rebalance {v.switches} (control: see V0 row).\n\n"
                f"**VERDICT: {'CLEARS THE BAR — promote to a forward-harness book' if (beats_full and median_gap >= 0) else 'DOES NOT clear the bar — honest negative, stays archived'}.**\n"
            )
    lines.append(
        f"| 1/N PIT (frictionless, the bar) | {n_cagr * 100:.1f}% | {n_mtr.sharpe:.2f} | "
        f"{max_drawdown(one_n) * 100:.1f}% | ₹0 | — | — |"
    )
    lines.append(
        "| _references (published)_: Nifty-50 TRI 14.5%/0.98 · validated core (annual·shrink) "
        "18.2%/1.13 | | | | | | |"
    )
    lines.append(verdict_v1)
    lines.append(
        "V0-vs-V1 is the attribution: the same QUBO on the same clean universe, with and without the "
        "switching-cost term — the difference is what the turnover fix (not the universe) bought.\n"
    )

    report = "\n".join(lines) + "\n"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(report)
    print(report)
    print(f"(written to {args.out})")


if __name__ == "__main__":
    main()
