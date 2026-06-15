"""Q-Alpha Research — the frontier / exploratory track, split out of the product repo.

This package holds work that is deliberately *not* production-ready and must not be imported by the
Q-Alpha product engine. Everything here is held to the same iron rule when it makes a performance
claim — it must beat the relevant baseline (1/N, or the existing rule) **walk-forward, net of
Zerodha cost + capital-gains tax** — but it lives here so the product repo stays clean and auditable.

It depends on the validated `qalpha` engine and *imports* it (accounting / backtest / factors) rather
than copying it: one source of truth for the tax-aware FIFO/cost engine, so research claims are
validated against the exact same code that trades.

Sub-tracks:
- `quantum`  — portfolio selection as a QUBO + QAOA/exact/SA solvers (Q_alpha.md §15, AUM-gated).
- (planned) `regime`  — bubble / crash detection (LPPLS, HMM, valuation/breadth); deploy-throttle only.
- (planned) `agentic` — news / speech / macro / sentiment agents.
"""
