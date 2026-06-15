# Q-Alpha Research

The **frontier / exploratory track** for [Q-Alpha](https://github.com/aarsh-adhvaryu/Q_Alpha) — split
out so the product repo stays clean, auditable, and production-ready.

This repo holds work that is deliberately *not* production-ready: quantum optimisation, regime /
bubble-crash detection, and agentic news/sentiment research. It **imports the validated `qalpha`
engine** (accounting / backtest / factors) rather than copying it — one source of truth for the
tax-aware FIFO/cost engine, so any performance claim here is validated against the exact same code
that trades. **The Q-Alpha product never imports from this repo.**

## Iron rule (inherited)

Any performance claim must beat its baseline (1/N, or the existing rule) **walk-forward, net of
Zerodha cost + capital-gains tax**, on the survivorship-free universe. No in-sample tuning. A negative
result, written down honestly, is a valid and valuable outcome.

## Tracks

| Track | Status | What |
|---|---|---|
| `quantum` | ✅ migrated from product repo | Portfolio selection as a QUBO + QAOA / exact-enumeration / simulated-annealing solvers (Q_alpha.md §15, AUM-gated ₹50L+). |
| `regime`  | 🔜 planned | Bubble / crash detection — LPPLS, HMM regime-switching, valuation/breadth. **Deploy-throttle + human-alert only, never auto-sell.** |
| `agentic` | 🔜 planned | News / speech / macro / sentiment agents. |

## Setup

```bash
uv sync --extra dev                  # core + dev tooling (pulls the qalpha engine)
uv sync --extra dev --extra quantum  # + the quantum stack (qiskit)
uv run pytest                        # QUBO/exact/SA tests run on numpy; QAOA tests need --extra quantum
```

`qalpha` is resolved from the GitHub product repo by default (`[tool.uv.sources]` in `pyproject.toml`).
For local co-development with both repos checked out as siblings, override it with the editable path:

```toml
[tool.uv.sources]
qalpha = { path = "../qalpha", editable = true }
```

## Layout

```
src/qalpha_research/
  quantum/        QUBO formulation + QAOA/exact/SA solvers
  regime/         (planned) LPPLS / HMM / valuation bubble-crash detection
  agentic/        (planned) news / sentiment agents
tests/            mirrors the package
scripts/          quantum_demo.py, quantum_benchmark.py
```
