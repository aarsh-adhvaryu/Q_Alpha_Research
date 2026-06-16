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
  business-income tax**, not CG) → P3 puts + rotation + sell-fallback.
  - **✅ P1 DONE** (`regime/fragility.py`, `scripts/build_fragility_dataset.py` → committed
    `data/fragility_panel.csv` 13 series 1996–2026, `scripts/validate_fragility.py`,
    `reports/fragility_gauge_validation.md`, tests). Causal no-look-ahead stress composite (US/India
    vol, MOVE, HYG/LQD credit proxy, DXY, USD-INR, drawdown, India↔global correlation). **Validated:**
    elevates in every crash (peaks 0.67–0.99), **1% false-alarm** in calm years at τ=0.70. Honest:
    it's **coincident** (spikes with the drawdown, esp. COVID 0.99) → a hedge/throttle trigger, not a
    forecast. The price-extension *fragility* sub-score was too always-on (≈0.68 every calm year) →
    **dropped**; real leading fragility needs true valuation (P/E, credit-tightness, concentration) —
    a later data task (FRED keyless CSV now capped to ~3y; P/E + FII flows deferred).
  - **✅ P2 DONE — the tax-free hedge CLEARS THE BAR** (`scripts/exp_hedge.py`,
    `reports/hedge_findings.md`). Short index-futures overlay on a passive Sensex book 1997–2026
    (incl. 2008 + COVID), book never sold (no CG tax), net of F&O txn/roll + 30% business-income tax,
    **1-day execution lag** (fixed an initial same-day look-ahead that had inflated it). Rarely-firing
    best config (h=0.5, τ=0.7, 6.7% of days): DD −60.9→−53.0, Sharpe 0.55→0.57, CAGR ~flat, cost drag
    <1pt. **ROBUST OOS (2015+, untuned): DD −38.1→−22.8 (mostly COVID), Sharpe 0.62→0.66.** First
    regime overlay to clear the bar — the **tax-free HEDGE wins where Sprint 1's SELL overlay failed**
    (tax was the killer, confirmed). Caveats: price index not TRI, F&O tax modelled simply, coincident
    gauge → partial protection, single market.
  - **✅ P3 CORE DONE — hedge on the qalpha strategy book also clears the bar** (`regime/hedge.py`
    [tested module: `hedge_active` + `apply_futures_hedge`, no-look-ahead lag encapsulated],
    `tests/test_hedge.py`, `scripts/exp_hedge_book.py`, `reports/hedge_book_findings.md`). Nifty-futures
    hedge on the validated annual-shrink book (exposure≡1.0, fidelity 0.0), 2012–26, holdings never
    sold: **FULL Sharpe 1.08→1.13, maxDD −25.2→−22.5, CAGR ~flat, still beats 1/N**; OOS 2018+ Sharpe
    1.20→1.29; **COVID-2020 drawdown −25.2→−9.7, Sharpe 1.55→2.47.** exp_hedge.py (P2) refactored onto
    the tested module (reproduces P2 exactly). Caveats: coincident gauge (partial protection), only
    COVID is a severe crash in the 2012–26 book window, F&O tax modelled simply, single h=0.5.
  - **✅ P3 PUTS DONE — futures beat puts (honest)** (`regime/options.py` [bs_put + apply_put_hedge,
    BS priced with India VIX, tested no-look-ahead/crash/keeps-upside], `tests/test_options.py`,
    `scripts/exp_puts.py`, `reports/puts_findings.md`). On Nifty 2008–26 both hedges beat unhedged, but
    **short futures > puts**: in the deep grinding 2008 crash the linear short rides the whole decline
    (DD −46.7→−34.1) vs the OTM put's bounded/decaying protection (−40.4); close in the sharp COVID V.
    The put's keep-the-upside edge barely shows because the gauge is **selective** (calm 2017 → never
    fired → zero premium drag; all legs identical). Puts would win with a noisier/earlier gauge; with
    this coincident one they don't. **→ Short futures is the recommended hedge instrument.**
  - **▶ P3 REMAINING (lower priority / data-blocked):** **sector rotation** (needs sector decomposition
    + a concentrated-vs-systemic classifier the gauge doesn't yet have); **tax-minimised-sell** fallback
    (a live-advisor decision rule — sell only when avoided-loss > realised-tax — more than a clean
    backtest); **leading-valuation fragility inputs** (P/E, credit-tightness, concentration) to give the
    gauge *lead* — **data-blocked here** (same fundamentals-sourcing problem; FRED keyless capped, no
    niftyindices P/E feed). The gauge stays coincident until that data is sourced.
- **Deferred (after Sprint 2):** fresh-capital deploy-throttle; agentic news/macro track; LPPLS on
  midcaps/single names (its real habitat).
- **Compute:** CPU by default. GPU only for quantum scaling (cuQuantum Aer) or a local-LLM agentic
  design — not for HMM/valuation/LPPLS (those would leave the card idle). User has GPU available on ask.

## Gates

ruff · ruff-format · mypy strict · pytest — keep green before committing (mirrors the product repo).
