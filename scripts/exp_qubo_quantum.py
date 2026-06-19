"""Stage B — QAOA on a REAL Nifty-100-derived QUBO, reduced to sector buckets (§15.1 showcase).

The full 100-asset QUBO is simulator-infeasible for QAOA (2¹⁰⁰ amplitudes; the synthetic benchmark
already hit the wall at n=10). So we collapse Nifty-100 into ~n sector buckets (equal-weight
constituent returns) → a real μ/Σ → a small cardinality QUBO that QAOA *can* solve, and check it
reproduces the exact optimum on a **real** instance (the synthetic `quantum_benchmark.py` did this on
random data). Extends, doesn't replace, that benchmark.

Run: uv run --extra quantum python scripts/exp_qubo_quantum.py --qalpha ../qalpha
"""

from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import pandas as pd
from qalpha.data.ingest import load_parquet

from qalpha_research.quantum.qubo import build_portfolio_qubo
from qalpha_research.quantum.solvers import solve_exact, solve_simulated_annealing

warnings.filterwarnings("ignore")


def _sector_returns(qroot: Path, max_sectors: int) -> pd.DataFrame:
    """Equal-weight daily return series per sector from the Nifty-100 panel (largest sectors first)."""
    prices = load_parquet(qroot / "data/historical/prices_nifty100_static.parquet")
    uni = pd.read_csv(qroot / "data/universes/nifty100_current_static.csv")
    sector_of = {str(t): str(s) for t, s in zip(uni["ticker"], uni["sector"], strict=True)}
    adj = prices.adj_close
    rets = adj.pct_change()
    by_sector: dict[str, pd.Series] = {}
    members: dict[str, int] = {}
    for sec in sorted(set(sector_of.values())):
        cols = [t for t in adj.columns if sector_of.get(t) == sec]
        if cols:
            by_sector[sec] = rets[cols].mean(axis=1)
            members[sec] = len(cols)
    top = sorted(members, key=lambda s: members[s], reverse=True)[:max_sectors]
    return pd.DataFrame({s: by_sector[s] for s in top}).dropna()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qalpha", default="../qalpha")
    ap.add_argument("--n", type=int, default=10, help="sector buckets (QAOA qubits) — keep small")
    ap.add_argument("--k", type=int, default=4, help="target cardinality (sectors to hold)")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--maxiter", type=int, default=100)
    ap.add_argument("--out", default="reports/qubo_quantum_findings.md")
    args = ap.parse_args()

    from qalpha_research.quantum.qaoa import solve_qaoa

    sr = _sector_returns(Path(args.qalpha), args.n)
    sectors = list(sr.columns)
    mu = sr.mean().to_numpy() * 252.0
    cov = sr.cov().to_numpy() * 252.0
    qubo = build_portfolio_qubo(mu, cov, args.k)

    t = time.perf_counter()
    x_ex, e_ex = solve_exact(qubo)
    ex_s = time.perf_counter() - t
    t = time.perf_counter()
    _, e_sa = solve_simulated_annealing(qubo, seed=1)
    sa_s = time.perf_counter() - t
    t = time.perf_counter()
    _, e_q = solve_qaoa(qubo, reps=args.reps, maxiter=args.maxiter)
    q_s = time.perf_counter() - t

    picked = [sectors[i] for i in range(len(sectors)) if x_ex[i] == 1]
    qaoa_match = abs(e_q - e_ex) < 1e-6

    lines = [
        "# Stage-B — QAOA on a real Nifty-100 sector QUBO (quantum showcase)\n",
        f"Real instance: **{len(sectors)} sector buckets** (equal-weight Nifty-100 constituents), "
        f"cardinality k={args.k}. `gap` = solver energy − exact optimum (0 = optimal).\n",
        "| solver | energy | gap | time |",
        "|---|---|---|---|",
        f"| exact (2ⁿ) | {e_ex:+.4f} | 0.0000 | {ex_s * 1000:.0f} ms |",
        f"| simulated annealing | {e_sa:+.4f} | {e_sa - e_ex:+.4f} | {sa_s * 1000:.0f} ms |",
        f"| **QAOA** (p={args.reps}) | {e_q:+.4f} | {e_q - e_ex:+.4f} | {q_s:.1f} s |",
        f"\n**QAOA {'reproduced' if qaoa_match else 'MISSED'} the exact optimum** on this real "
        f"instance. Exact selection (k={args.k}): {picked}.\n",
        "## The scaling wall (why this is sector-reduced, not the full 100)\n",
        "- QAOA on a statevector simulator needs **2ⁿ amplitudes**; the full Nifty-100 QUBO is n=100 "
        "→ 2¹⁰⁰, impossible. The synthetic benchmark already measured the wall at n=10 (~12 min, "
        "gap +0.20). NISQ hardware can't do 100 clean qubits at depth either.",
        "- So the **quantum solver is a method demonstration on a reduced real instance**; the full "
        "100-asset selection is solved classically (simulated annealing) in `exp_qubo_universe.py`.",
        "- Honest scope: this validates the **solver**, not portfolio returns (see "
        "`reports/qubo_universe_findings.md` for the return question — QUBO selection does not beat the "
        "survivorship-inflated 1/N net of tax).",
    ]
    report = "\n".join(lines) + "\n"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(report)
    print(report)
    print(f"(written to {args.out})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
