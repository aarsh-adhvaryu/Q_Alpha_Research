# CLAUDE.md — Q_Alpha_Research

Guidance for Claude Code working in the **research / frontier** repo.

## What this is

The exploratory track split out of the [Q-Alpha product repo](https://github.com/aarsh-adhvaryu/Q_Alpha)
(2026-06-15) so the product stays clean and audit-ready. This repo **imports the validated `qalpha`
engine as a dependency** (accounting / backtest / factors) — never copies it, so every performance
claim is checked against the exact same tax-aware FIFO/cost code that trades. **The product never
imports from here.**

## Iron rule (inherited — do not violate)

A performance claim must beat its baseline (1/N, or the existing rule) **walk-forward, net of Zerodha
cost + capital-gains tax**, on the survivorship-free universe. No tuning to manufacture a finding
(pre-register the bar before running). A negative result, reported honestly, is a valid outcome.

## Setup

```bash
uv sync --extra dev                  # core + dev (pulls the qalpha engine)
uv sync --extra dev --extra quantum  # + qiskit stack
PYTHONPATH=src python -m pytest      # QUBO/LPPLS tests run on numpy; QAOA needs --extra quantum
```

`qalpha` resolves from the GitHub product repo by default (`[tool.uv.sources]`); for local
co-dev with both repos checked out as siblings, override to `{ path = "../qalpha", editable = true }`.

## Tracks

```
src/qalpha_research/
  quantum/   QUBO + QAOA/exact/SA solvers (Q_alpha.md §15, AUM-gated). Migrated from product repo.
  regime/    bubble/crash detection. lppls.py (Sornette LPPLS) + PREREGISTRATION.md. agentic = planned.
```

## ⏯️ STATE / NEXT SESSION

- **quantum:** built (QUBO/QAOA + benchmark report). Stable; no open thread.
- **regime — LPPLS done, honest NEGATIVE on Nifty** (`reports/lppls_nifty_findings.md`): max
  confidence ~0.33, no useful lead on endogenous peaks; correctly silent (0.00) before the exogenous
  COVID crash + near-zero false positives. Fitter validated (recovers synthetic `tc` to 4dp).
  **Conclusion: Nifty large-cap had no parabolic LPPLS bubbles 2012–2026.**
- **OPEN DECISION (user to steer next session):**
  1. **HMM + valuation/breadth risk-state** on the index — most likely to clear the money test.
  2. **LPPLS on midcaps / single names** — give the bubble detector its real habitat.
  3. **Agentic news/macro track** — the info-driven falls LPPLS can't see.
- **Compute:** CPU by default. GPU only for quantum scaling (cuQuantum Aer) or a local-LLM agentic
  design — not for HMM/valuation/LPPLS (those would leave the card idle). User has GPU available on ask.

## Gates

ruff · ruff-format · mypy strict · pytest — keep green before committing (mirrors the product repo).
