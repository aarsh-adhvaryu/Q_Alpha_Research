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
- **regime — HMM risk-state (Sprint 1) done, honest NEGATIVE** (`reports/riskstate_nifty_findings.md`,
  pre-reg `regime/PREREGISTRATION_riskstate.md`): walk-forward filtered Gaussian HMM (`regime/
  risk_state.py`, no-look-ahead + synthetic-recovery tested) drives a defensive *sell* overlay via a
  research-side runner (`regime/overlay_backtest.py`, `scripts/exp_riskstate.py`) that **reuses qalpha
  unmodified** — fidelity vs `run_backtest` = **0.0e+00** equity diff. Across a (τ,floor) sweep the
  overlay **fails the money test**: best 14.5% CAGR / Sharpe 1.04 vs always-invested 17.2% / 1.08,
  ~1pt less DD but **₹94–128k realised capital-gains tax**, and trails 1/N. **Mechanism:** filtered
  signal de-risks late / re-risks high, and selling appreciated equity to dodge a *recoverable*
  drawdown costs more tax than it saves (the tax-first thesis, reconfirmed). Breadth/valuation won't
  rescue a *sell* overlay (more firing → more tax). **Rescope:** only a tax-free **fresh-capital
  deploy-throttle** (route new SIP inflows to cash in stress, never sell) is worth testing — needs a
  contribution stream the lump-sum book lacks; else keep risk-state as a dashboard reporting signal.
- **🎯 ACTIVE PLAN — Sprint 2: systemic-fragility gauge + tax-FREE hedge overlay** (pre-registered,
  `regime/PREREGISTRATION_systemic.md`). Chosen with the user after a long design session that reframed
  the whole track. Key reasoning, locked in: (1) crashes come from an **unbounded, unpredictable
  trigger set** (2008 US-housing *contagion* — not an Indian bubble; oil; USD-INR; war; domestic 2018;
  exogenous COVID) → **don't predict the cause; build a CAUSE-AGNOSTIC fragility + transmission gauge**
  (three layers: global fragility · India transmission [FII flows/INR/spreads/correlation→1] · domestic
  vulnerability). (2) The objective is **risk-adjusted return ("reduce risk, keep profit")**, not
  prediction. (3) Sprint 1's sell-overlay died on **capital-gains tax** → the action is now **tax-free
  hedge**: dry powder + sector rotation (concentrated froth) + **short-futures/puts hedge** ("keep the
  shares, nullify the exposure") + optional **net market short** (flagged as *speculation*, not a hedge)
  + a **tax-minimised-sell fallback** (sell only when avoided-loss > realised-tax — the FIFO engine
  computes this exactly). Lever chosen by **concentrated-vs-systemic** (rotation only helps a sector
  bubble; in a systemic crash correlations→1 so only cash/hedge work). **Phasing:** P1 build+validate
  the gauge (free cross-asset data: FRED/niftyindices/RBI/NSE/AMFI; must elevate before 2000/08/13/18,
  stay calm in benign years, **silent before COVID**) → P2 futures-hedge money test (linear; **F&O =
  business-income tax**, not CG) → P3 puts + rotation + sell-fallback. **NOW CODING P1.**
- **Deferred (after Sprint 2):** fresh-capital deploy-throttle; agentic news/macro track; LPPLS on
  midcaps/single names (its real habitat).
- **Compute:** CPU by default. GPU only for quantum scaling (cuQuantum Aer) or a local-LLM agentic
  design — not for HMM/valuation/LPPLS (those would leave the card idle). User has GPU available on ask.

## Gates

ruff · ruff-format · mypy strict · pytest — keep green before committing (mirrors the product repo).
