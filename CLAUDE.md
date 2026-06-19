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

- **✅ hedge.py open-episode tax bug FIXED (2026-06-19)** (`regime/hedge.py`, `tests/test_hedge.py`).
  *What:* `apply_futures_hedge` taxed an episode's F&O gain only on its ON→OFF *close*; a window that
  ended **mid-hedge** never hit that branch, so the last open episode's gain went untaxed → an
  optimistic edge-case bias. *Why it was harmless to the record:* every published window ends calm
  (hedge off), and the crash decomposition (`exp_hedge_crashes.py`) slices **one** post-tax
  full-window run (each crash episode closes on recovery, well before the end), so **no published
  number was affected** — it was a latent oversight, not an active error. *Fix:* after the loop, tax a
  still-open episode's gain too (3 lines) + a test (`test_open_episode_at_window_end_is_taxed`) that a
  window ending mid-hedge is taxed; the no-look-ahead test now compares `iloc[:cut-1]` vs `iloc[:-1]`
  because the truncated run's *final* bar legitimately carries the terminal-episode settlement. *Found
  by:* a product-side audit; the qalpha hedge was also promoted to a **read-only product dashboard tab**
  (product-side signal, no import from here — see the product repo's CLAUDE.md, 2026-06-19 sprint).
- **quantum:** built (QUBO/QAOA + synthetic benchmark report). Stable.
- **▶ QUBO/quantum on Nifty 100 (2026-06-18) — DONE, honest near-miss.** After the classical
  3-factor+shrink showed no breadth bonus on Nifty 100 (qalpha), tested whether **combinatorial QUBO
  selection** does better. Pre-reg `reports/PREREGISTRATION_qubo_universe.md`. **Stage A**
  (`scripts/exp_qubo_universe.py` → `reports/qubo_universe_findings.md`): annual walk-forward, causal
  252d μ/Σ → cardinality QUBO (k=20) → **classical SA** (n≈90, the only feasible solver) → equal-weight,
  executed through qalpha's `Portfolio.rebalance` for **real FIFO cost+tax** (qalpha unmodified; reads
  the Nifty-100 static universe + price cache from ../qalpha). Result: **23.6% CAGR / Sharpe 1.46 /
  maxDD −33.3%, ₹273k tax** vs survivorship-inflated **1/N 26.3% / 1.49 / −36.6%** → **−2.7pt CAGR
  (DOES NOT clear the bar) but essentially ties risk-adjusted** (Sharpe 1.46 vs 1.49, lower DD, ≥1/N in
  58% of 3y holds, median +1.1pt) — **far closer than the classical screen's −9.9pt / 16%**. The QUBO's
  variance term genuinely de-risks; the limiter is the **₹273k tax from full annual reselection** (the
  tax-first thesis again — a found bug: a 0.10 no-trade band > the 5% per-name weight had frozen
  reselection to ₹0 tax; fixed to band=0). **Survivorship-contaminated baseline → directional, NOT a
  GO.** **Stage B** (`scripts/exp_qubo_quantum.py` → `reports/qubo_quantum_findings.md`, needs
  `--extra quantum`): **QAOA reproduced the exact optimum** on a **real** 8-sector Nifty-100 QUBO
  (−0.5903, 54s) — extends the synthetic benchmark to real data. **Quantum scaling wall (hard):** the
  full n=100 QUBO is simulator-infeasible (2¹⁰⁰; wall already at n=10), so quantum is showcase-only on a
  reduced instance; the real selection is solved classically. **Takeaway: QUBO selection is risk-aware
  and competitive but tax-throttled, doesn't beat the (contaminated) 1/N; a lower-turnover QUBO variant
  is the pre-registered follow-up. Keep in research.**
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
- **🏁 SPRINT 2 CONCLUDED (2026-06-16).** Result: the **tax-free short-futures hedge on a selective,
  cause-agnostic systemic-stress gauge** is the track's first positive — clears the pre-registered bar
  on the index (OOS-robust) AND on the qalpha book (Sharpe 1.08→1.13, beats 1/N, **COVID DD −25→−10**);
  futures beat puts (the selective gauge negates put convexity). The whole regime arc is one honest
  story: **LPPLS negative → HMM sell-overlay negative (tax drag) → tax-free hedge positive** — *the tax
  was always the killer; hedge, don't sell.* **USER DECISION: keep everything in research as a proven
  capstone; do NOT promote into the qalpha product now** (keeps qalpha pristine/resume-clean). If
  revisited later, the safe first promotion is **the gauge as a read-only dashboard advisory signal**
  ("systemic risk: normal/elevated" + a 'consider a hedge' suggestion — fits the advisor model, no
  derivatives in the core); the actual futures-hedge execution would be a separate **gated Phase-1**
  feature needing real F&O cost/tax re-validation + more-than-COVID crash evidence + a manual-trader
  operations plan. Deferred research levers below remain open.
- **🎯 Sprint 2 detail — systemic-fragility gauge + tax-FREE hedge overlay** (pre-registered,
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
- **✅ ROBUSTNESS BATTERY DONE (2026-06-17) — the hedge survives, with one envelope refinement.**
  Before any product-integration talk, stress-tested the Sprint-2 operating point against its four
  admitted caveats (pre-reg `regime/PREREGISTRATION_robustness.md`; `scripts/exp_hedge_robustness.py`
  → `reports/hedge_robustness_findings.md`, `scripts/exp_hedge_crashes.py` →
  `reports/hedge_crashes_findings.md`; all reuse the tested hedge module + the validated engine,
  qalpha untouched). **B (decisive) PASS** — the *coincident* gauge's protection survives a realistic
  2–3 trading-day manual-execution delay (lag 1→3: Sharpe 1.13→1.11, maxDD held −22.5 vs always −25.2)
  → the load-bearing "can you actually execute it" worry is retired. **C (decisive) PASS** — on
  1997–2026 Sensex it cut drawdown in **both** deep, differently-caused crashes (2008 GFC −60.9→−52.1
  AND COVID −38.1→−22.8), calm-year drag 0.63 CAGR pts → **not a COVID one-off; the cause-agnostic
  claim holds out-of-window** (milder corrections mixed — 2022 slightly worsened by a coincident fire
  that didn't deepen, honest). **D PASS** — edge holds to ≫10× modelled F&O cost + 40% tax bracket
  (not a cost mirage). **A PARTIAL** — robust across **every** h and persist at τ∈{0.7,0.8} (24/24),
  but **τ=0.6 fragile** (3/12): a low threshold hedges too eagerly and a coincident gauge then bleeds
  CAGR. **Refinement: operate at τ≥0.7; don't run it eager.** A added the cost-override params to
  `regime/hedge.py` (+test). **Verdict: concrete enough to consider for integration, at τ≥0.7** — but
  the standing USER DECISION still holds (keep in research; if ever promoted, dashboard advisory first).
- **Deferred (after Sprint 2):** fresh-capital deploy-throttle; agentic news/macro track; LPPLS on
  midcaps/single names (its real habitat).
- **✅ Repo-wide gate sweep (2026-06-17):** fixed all outstanding lint/type/format issues across the
  whole tree (`ruff check .`, `ruff format --check .`, `mypy src scripts tests`, `pytest` all green —
  30 files, 22 passed/1 skipped). Notable real fix: a `B023` late-binding closure bug in
  `scripts/run_lppls_nifty.py` (the `lead` fn captured loop vars `pre`/`peak`) → hoisted to a
  `_lead(frame, peak, thr)` helper; plus two `Hashable.date()` mypy fixes and a missing test
  annotation. mypy had also crashed on a corrupt `.mypy_cache` (fresh-sync artifact) — `rm -rf` fixed.
- **Compute:** CPU by default. GPU only for quantum scaling (cuQuantum Aer) or a local-LLM agentic
  design — not for HMM/valuation/LPPLS (those would leave the card idle). User has GPU available on ask.

## Gates

ruff · ruff-format · mypy strict · pytest — keep green before committing (mirrors the product repo).
