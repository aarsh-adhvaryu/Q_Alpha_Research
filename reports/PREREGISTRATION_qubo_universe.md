# Pre-registration — QUBO / quantum portfolio selection on Nifty 100

_Registered 2026-06-18, before running. Inherited iron rule: beat 1/N walk-forward, net of Zerodha
cost + capital-gains tax, on a survivorship-free universe; no tuning to manufacture a finding; an
honest negative is valid._

## Motivation
The classical 3-factor + shrink strategy showed **no breadth bonus** on Nifty 100 (qalpha
`reports/universe_breadth_findings.md`). Question: does **combinatorial cardinality-constrained
selection** (the QUBO) — genuinely different from the continuous optimiser — find a better subset of
the 100 names? And can the **quantum** solver (QAOA) play any role at this scale?

## Two walls (stated up front)
1. **Quantum scaling wall (hard).** QAOA on a statevector simulator needs 2ⁿ amplitudes; n=100 (2¹⁰⁰)
   is infeasible, and the existing benchmark already failed at n=10 (~12 min, gap +0.20). NISQ
   hardware can't do 100 clean qubits at depth either. ⇒ The **full 100-asset QUBO is solved
   classically (simulated annealing)**; QAOA is demonstrated only on a **reduced (~12–14 qubit)**
   real-data instance.
2. **Survivorship wall.** The static current-constituents Nifty-100 is biased (same as the classical
   screen); a 1/N-on-survivors baseline is the largest beneficiary. ⇒ Read the **strategy − 1/N gap**,
   directional only; this is **not** a GO.

## Stage A — QUBO selection on real Nifty 100 (classical SA), walk-forward
- Annual rebalance, 2012–2024. At each date: **causal** trailing-252d returns over names priced
  as-of → expected returns μ (annualised mean) + covariance Σ → cardinality-constrained QUBO
  (`build_portfolio_qubo`, **k = 20**, risk_aversion **q = 1.0**, penalty auto) → **solve_simulated_
  annealing** → equal-weight the k picks.
- Execute through qalpha's **`Portfolio.rebalance`** (real FIFO cost + capital-gains tax,
  `min_trade_fraction = 0.10`); qalpha unmodified. Daily mark-to-market for the equity curve.
- Baselines: **1/N** (`equal_weight_pit`) and **Nifty-50 TRI**; reference: the qalpha shrink book's
  published numbers.
- **Pre-registered decision:** if QUBO selection does not beat 1/N on the gap (full window **and**
  rolling 3y) even with the survivorship tailwind → **negative** (QUBO selection adds nothing over the
  robust baseline — the expected result, consistent with the estimation-error literature and the
  existing quantum report). No k/q tuning to flip it.
- Parameters **k=20, q=1.0 are fixed before running.** One run, reported as-is.

## Stage B — QAOA quantum showcase on a reduced real instance
- Collapse Nifty-100 into **~12–14 sector buckets** (equal-weight constituent returns per sector) →
  real μ/Σ → QUBO (k≈5). Solve with **exact · SA · QAOA** (needs `--extra quantum`), report the
  optimality gap. Goal: show QAOA reproduces the exact optimum **on a real instance** (extending the
  synthetic `quantum_benchmark.py`), and document that n=100 itself is simulator-infeasible.
- This validates the **solver**, not portfolio returns (same honest scope as the existing benchmark).

## Metrics
Full-window CAGR/Sharpe/maxDD net cost+tax; rolling-3y-hold distribution; **strategy − 1/N gap**;
realized tax; selected-book sector spread; (Stage B) per-solver optimality gap + runtime.
