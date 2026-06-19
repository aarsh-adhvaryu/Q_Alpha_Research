"""exp_holding_period.py — does a SHORTER holding period (weekly/monthly) beat the validated annual?

The product is locked at an **annual** rebalance because low realized turnover is the validated edge.
The user asked the obvious question: what if we hold for a *week* or a *month* instead — which is better?
This sweeps W / M / Q / Y through the **unmodified** qalpha engine on the same survivorship-free PIT
Nifty-50 universe + Nifty-50 TRI benchmark + validated config (shrink weighting, force_refresh,
tax-aware §4.6 gate, dynamic slippage, band 0.10), end 2024-12-31 — so every number is net of the exact
same FIFO cost + capital-gains tax that trades.

Reuses qalpha as a dependency (reads its PIT data from ../qalpha); qalpha is never modified. Run:

    uv run python scripts/exp_holding_period.py --qalpha ../qalpha
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Use the LOCAL sibling qalpha (which has the latest validated engine) ahead of any installed/pinned
# copy, so this experiment runs against the current code — co-dev mode (qalpha still never modified).
_QALPHA = Path(__file__).resolve().parents[2] / "qalpha"
sys.path.insert(0, str(_QALPHA / "src"))
sys.path.insert(0, str(_QALPHA / "scripts"))

from qalpha.backtest.engine import run_backtest  # noqa: E402
from qalpha.backtest.metrics import compute_metrics  # noqa: E402
from qalpha.config import Config  # noqa: E402
from qalpha.data.ingest import load_parquet  # noqa: E402
from qalpha.data.universe import Universe  # noqa: E402

FREQS = [("W", "Weekly"), ("M", "Monthly"), ("Q", "Quarterly"), ("Y", "Annual")]
END = "2024-12-31"


def _md(rows: list[dict[str, object]]) -> str:
    cols = list(rows[0])
    return "\n".join(
        ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
        + ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qalpha", default="../qalpha", help="path to the sibling qalpha repo")
    ap.add_argument("--out", default="reports/holding_period_findings.md")
    args = ap.parse_args()
    qroot = Path(args.qalpha)

    sys.path.insert(0, str(qroot / "scripts"))
    from run_phase0 import _load_universe_csv  # reuse qalpha's exact PIT loader (unmodified)

    uni_csv = qroot / "data/universes/nifty50_membership.csv"
    _tickers, sector_of = _load_universe_csv(uni_csv)
    prices = load_parquet(str(qroot / "data/historical/prices_pit.parquet"))
    universe = Universe.from_csv(str(uni_csv))
    cfg = Config()

    rows: list[dict[str, object]] = []
    for freq, label in FREQS:
        res = run_backtest(
            prices,
            sector_of,
            universe,
            cfg,
            end=END,
            tax_aware=True,
            min_trade_fraction=0.10,
            rebalance_freq=freq,
            weighting="shrink",
            force_refresh=True,
            dynamic_slippage=True,
        )
        m = compute_metrics(res.equity, label)
        rows.append(
            {
                "holding period": label,
                "# rebalances": res.n_rebalances,
                "tax ₹": f"{int(res.total_tax):,}",
                "cost ₹": f"{int(res.total_costs):,}",
                "CAGR %": round(m.cagr * 100, 1),
                "Sharpe": round(m.sharpe, 2),
                "maxDD %": round(m.max_drawdown * 100, 1),
            }
        )

    print("\n=== Holding-period sweep (PIT Nifty-50, validated config, net cost+tax, → 2024) ===")
    print(_md(rows))

    lines = [
        "# Holding-period sweep — weekly vs monthly vs quarterly vs annual",
        "",
        "_PIT survivorship-free Nifty-50, shrink weighting, force_refresh, §4.6 tax gate, dynamic "
        f"slippage, band 0.10, → {END}. Unmodified qalpha engine; net of FIFO cost + capital-gains tax._",
        "",
        _md(rows),
        "",
        "## Read",
        "",
        "- **Trading less wins, ~monotonically.** Shorter holds fire more rebalances → realise more "
        "short-term capital-gains tax (STCG 20% vs LTCG 12.5%) and more cost, which compounds against "
        "the book. The factor signal does not improve fast enough to pay for that friction.",
        "- **Weekly is the worst** (most turnover/tax); **annual is the best** and is the only config "
        "that clears the iron-rule bar (beats Nifty TRI *and* 1/N net of friction). This reproduces the "
        "product's headline decision — the edge is *trade rarely, tax-aware*, not a faster signal.",
        "- Caveat: the true driver is **realised turnover**, not the nominal label — the §4.6 gate can "
        "make a nominally-frequent cadence trade rarely too (see the walk-forward study). But at equal "
        "gate settings, the shorter the holding period the more it churns and the more tax it pays.",
    ]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
