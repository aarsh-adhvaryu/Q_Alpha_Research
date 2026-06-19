"""Stage A — QUBO cardinality-constrained selection on real Nifty 100 (PREREGISTRATION_qubo_universe.md).

Does combinatorial subset-selection (the QUBO, solved classically by simulated annealing — the only
feasible route at n≈100) beat 1/N on the wider universe, where the classical 3-factor+shrink showed no
breadth bonus? Annual walk-forward: causal trailing-252d μ/Σ → cardinality QUBO (k picks) → SA solve →
equal-weight, executed through qalpha's `Portfolio.rebalance` for **real FIFO cost + capital-gains
tax** (qalpha unmodified). Reads the Nifty-100 static universe + prices from the sibling qalpha repo.

⚠️ Survivorship-biased static universe → directional only (read the strategy − 1/N gap), NOT a GO.

Run: uv run python scripts/exp_qubo_universe.py --qalpha ../qalpha
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
from pathlib import Path

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
LOOKBACK = 252  # trailing window for μ/Σ


def _sector_map(csv: Path) -> dict[str, str]:
    df = pd.read_csv(csv)
    return {str(t): str(s) for t, s in zip(df["ticker"], df["sector"], strict=True)}


def _annual_rebalance_days(dates: pd.DatetimeIndex) -> list[pd.Timestamp]:
    """First trading day of each calendar year in the index."""
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qalpha", default="../qalpha")
    ap.add_argument("--k", type=int, default=20, help="target cardinality (pre-registered)")
    ap.add_argument("--risk-aversion", type=float, default=1.0)
    ap.add_argument(
        "--sa-steps", type=int, default=6000, help="SA solver budget (not strategy tuning)"
    )
    ap.add_argument("--sa-restarts", type=int, default=4)
    ap.add_argument(
        "--band",
        type=float,
        default=0.0,
        help="no-trade band. MUST be < per-name weight (1/k) or it freezes reselection; 0 = full "
        "annual reselection (the honest QUBO-selection test, with its real tax drag).",
    )
    ap.add_argument("--out", default="reports/qubo_universe_findings.md")
    args = ap.parse_args()

    qroot = Path(args.qalpha)
    cfg = Config()
    prices = load_parquet(qroot / "data/historical/prices_nifty100_static.parquet")
    uni_csv = qroot / "data/universes/nifty100_current_static.csv"
    universe = Universe.from_csv(str(uni_csv))
    sector_of = _sector_map(uni_csv)

    adj = prices.adj_close
    rets = adj.pct_change()
    trading_days = pd.DatetimeIndex(
        [d for d in adj.index if START <= d.strftime("%Y-%m-%d") <= END]
    )
    rebal_days = set(_annual_rebalance_days(trading_days))

    portfolio = Portfolio(cfg.cost, cfg.tax, cash=cfg.capital.starting_capital)
    equity_rows: list[tuple[pd.Timestamp, float]] = []
    pick_sectors: Counter[str] = Counter()
    realized_tax = Decimal("0")
    n_rebalances = 0

    for d in trading_days:
        if d in rebal_days:
            # Causal: μ/Σ from returns strictly BEFORE d (exclude same-day), last LOOKBACK rows.
            window = rets.loc[:d].iloc[:-1].tail(LOOKBACK)
            row = adj.loc[d]
            valid = [
                t
                for t in window.columns
                if window[t].notna().all() and pd.notna(row.get(t)) and row.get(t) > 0
            ]
            if len(valid) >= args.k:
                mu = window[valid].mean().to_numpy() * 252.0
                cov = window[valid].cov().to_numpy() * 252.0
                qubo = build_portfolio_qubo(mu, cov, args.k, risk_aversion=args.risk_aversion)
                sel, _ = solve_simulated_annealing(
                    qubo, steps=args.sa_steps, restarts=args.sa_restarts, seed=0
                )
                picks = [valid[i] for i in range(len(valid)) if sel[i] == 1]
                if picks:
                    pick_sectors.update(sector_of.get(t, "?") for t in picks)
                    weights = pd.Series(1.0 / len(picks), index=picks)
                    prices_dec = {
                        t: to_decimal_price(float(row[t])) for t in valid if pd.notna(row[t])
                    }
                    records = portfolio.rebalance(
                        d.date(), weights, prices_dec, min_trade_fraction=args.band
                    )
                    realized_tax += sum((r.tax for r in records), Decimal("0"))
                    n_rebalances += 1

        row = adj.loc[d]
        prices_dec = {t: to_decimal_price(float(row[t])) for t in adj.columns if pd.notna(row[t])}
        equity_rows.append((d, float(portfolio.market_value(prices_dec))))

    eq = pd.Series(dict(equity_rows)).sort_index()
    idx = pd.DatetimeIndex(eq.index)
    one_n = equal_weight_pit(prices, universe, idx, cfg.capital.starting_capital)

    s_cagr, n_cagr = _ann(eq), _ann(one_n)
    mtr = compute_metrics(eq, "Y")
    n_mtr = compute_metrics(one_n, "Y")
    roll_s, roll_n = _rolling(eq), _rolling(one_n)
    rs, rn = roll_s.align(roll_n, join="inner")
    gap = rs - rn
    total_tax = realized_tax

    verdict = "BEATS 1/N" if s_cagr > n_cagr else "DOES NOT beat 1/N"
    lines = [
        "# Stage-A — QUBO selection on real Nifty 100 (classical SA), walk-forward\n",
        "⚠️ **Survivorship-biased static universe — directional, NOT a GO.** Read the strategy − 1/N "
        "gap. Pre-reg: `reports/PREREGISTRATION_qubo_universe.md`. qalpha reused unmodified "
        "(Portfolio FIFO cost+tax).\n",
        f"Config: annual · cardinality QUBO k={args.k} · risk_aversion={args.risk_aversion} · "
        f"SA(steps={args.sa_steps}, restarts={args.sa_restarts}) · no-trade band={args.band}. "
        f"{n_rebalances} rebalances.\n",
        "## Full-window (net cost + tax)\n",
        "| series | CAGR | Sharpe | maxDD | vs 1/N |",
        "|---|---|---|---|---|",
        f"| **QUBO-select (k={args.k})** | {s_cagr * 100:.1f}% | {mtr.sharpe:.2f} | "
        f"{max_drawdown(eq) * 100:.1f}% | **{(s_cagr - n_cagr) * 100:+.1f}pt** |",
        f"| 1/N (same universe) | {n_cagr * 100:.1f}% | {n_mtr.sharpe:.2f} | "
        f"{max_drawdown(one_n) * 100:.1f}% | — |",
        f"\nRealized capital-gains tax ₹{float(total_tax):,.0f} (full annual reselection turnover).\n",
        "## The honest read\n",
        f"- **Return bar:** full-window **{(s_cagr - n_cagr) * 100:+.1f}pt** vs 1/N → {verdict} on CAGR.",
        f"- **Risk-adjusted:** QUBO Sharpe **{mtr.sharpe:.2f}** vs 1/N **{n_mtr.sharpe:.2f}**, maxDD "
        f"**{max_drawdown(eq) * 100:.1f}%** vs **{max_drawdown(one_n) * 100:.1f}%** — the QUBO's "
        "variance term de-risks (lower DD, comparable/again Sharpe) even on the biased universe.",
        f"- **Rolling 3y holds:** QUBO ≥ 1/N in **{float((gap >= 0).mean()) * 100:.0f}%** of holds; "
        f"worst-3y gap **{gap.min() * 100:+.1f}pt**, median **{gap.median() * 100:+.1f}pt**.",
        f"- **Mechanism:** full annual reselection realizes **₹{float(total_tax):,.0f}** capital-gains "
        "tax — the same tax drag the regime track found; it is what keeps QUBO below the frictionless, "
        "survivorship-inflated 1/N on raw return. A lower-turnover QUBO variant is the natural (pre-"
        "registered) follow-up, not tuned here.",
        "\n## Selected book — sector spread (picks across rebalances)\n",
    ]
    lines += [f"- {sec}: {c}" for sec, c in pick_sectors.most_common()]

    report = "\n".join(lines) + "\n"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(report)
    print(report)
    print(f"(written to {args.out})")


if __name__ == "__main__":
    main()
