# Pre-registration — HMM + valuation/breadth risk-state (regime track, Sprint 1)

Written **before** looking at any result, per the Q-Alpha iron rule (no tuning to manufacture a
finding; a negative result reported honestly is a valid outcome). This is the regime track's pivot
after the [LPPLS negative](PREREGISTRATION.md): Nifty large-cap drawdowns are driven by rich
valuation + macro/vol regimes, **not** parabolic LPPLS singularities — so we test a regime detector
built for *that* mechanism.

## Hypothesis (what we are actually testing)

**H1 (the real claim):** a **risk-state** indicator — a Hidden Markov regime on index
returns/volatility, optionally confirmed by **breadth** (% of constituents > 200DMA) and
**valuation** (Nifty P/E percentile) — identifies stress regimes early and persistently enough to
drive a **defensive overlay / deploy-throttle** that improves risk-adjusted return (Sharpe) and/or
cuts drawdown, **net of Zerodha cost + capital-gains tax, walk-forward**, vs staying fully invested.

**H0 (the null we expect could well hold):** the overlay does **not** beat the always-invested
validated engine net of cost + tax — because the signal is lagging (de-risks at the bottom, buys
back high), gives up too much secular-bull upside, or the de-risking churns enough tax to erase the
drawdown benefit.

**Explicit non-claim:** we do **not** claim to forecast *exogenous* shocks (e.g. COVID Mar-2020). A
filtered regime model reacts to volatility once it appears; catching the *first* leg down of an
exogenous crash is out of scope. Reducing the *depth/duration* of the drawdown once stress is
underway is in scope.

## Data (fixed now)

- **Index:** Nifty 50 via NIFTYBEES daily close, 2012-01-02 → 2026 (`data/nifty50_nifbees_close.csv`).
- **Breadth (layered feature):** % of the point-in-time Nifty 50 constituents trading above their
  own 200-day MA, derived from the qalpha PIT price panel into a committed
  `data/nifty50_breadth.csv` (one-time data-prep, so the experiment is self-contained and does not
  depend on the sibling repo at run time).
- **Valuation (layered feature):** Nifty 50 daily P/E (niftyindices.com historical) → committed
  `data/nifty50_pe.csv`; used as a trailing **percentile rank** (no forward-looking normalisation).
- **Train / test split (committed in advance):** model selection (n_states, feature set, τ) is done
  **only** on **2012-01-02 → 2019-12-31**. The held-out evaluation window is **2020-01-01 → 2026**,
  never inspected during model choice. The walk-forward backtest additionally re-fits online (below),
  so the 2020+ window is genuinely out-of-sample for every hyperparameter.

## Method

- **Gaussian HMM** (`hmmlearn`, 2–3 states) on standardised daily features: log-return, trailing
  realised volatility (e.g. 21d), and drawdown-from-rolling-high. State count chosen on the
  **training window only** by BIC, capped at 3 for interpretability (calm / neutral / stress).
- **State labelling is mechanical, not outcome-fitted:** "stress" := the state with the highest
  fitted return-variance (and non-positive mean) under the **training** parameters. We never pick the
  state by which one lined up with a known crash.
- **NO LOOK-AHEAD — the load-bearing rule for HMMs.** We never use the *smoothed* (full-sample)
  state posterior — that peeks at the future. At each decision date *t* we use only the **filtered**
  posterior P(state | data up to *t*), via an **expanding-window walk-forward**: re-fit the HMM
  periodically (e.g. annually) on data ≤ *t*, then forward-filter to *t*. The decision at *t* uses
  information available at *t* only. (A unit test asserts filtered ≠ smoothed and that the signal at
  *t* is invariant to data after *t*.)
- **Method validation (mirrors the LPPLS tc-recovery discipline):** fit the HMM to data generated
  from a *known* 2-state Gaussian HMM and confirm it recovers the means, variances, and transition
  matrix within tolerance — so a signal, if found, is the model working, not a fitting artifact.

## Decision rule under test (defensive overlay — NEVER auto-sell on a whim)

When the filtered P(stress) ≥ τ (optionally AND breadth < b / valuation percentile > v as
confirmers), **scale equity exposure down** (route fresh-capital deployment to cash and/or reduce the
target weight toward a defensive floor); restore when P(stress) < τ. Exposure changes flow through
the **validated tax-aware engine** so every de-risk/re-risk pays real cost + capital-gains tax — the
overlay must be worth its friction. τ (and b, v) are **not** tuned to the OOS outcome: chosen on the
training window, then reported as a full sweep on the test window.

## Success bar (fixed in advance — ALL must hold)

The overlay is declared **useful** only if, on the **2020+ held-out window**, walk-forward, net of
Zerodha cost + capital-gains tax, run through the same engine as the baseline:

1. **The money test (primary):** the overlay beats the **always-invested annual-`shrink` baseline**
   on **Sharpe**, *without* a materially worse end wealth — OR delivers materially lower **max
   drawdown** (≥ 5 absolute pts) at ≥ equal Sharpe. A pure drawdown cut that sacrifices Sharpe is a
   **fail** (you can do that more cheaply by holding less equity).
2. **Beats 1/N:** the overlaid strategy still clears the equal-weight baseline net of cost + tax
   (the standing iron-rule bar).
3. **Not a tax mirage:** the realised cost + tax of the overlay is reported; if the drawdown benefit
   is wiped out once friction is charged, that is a **fail**.
4. **Robust, not a single-window fluke:** the benefit holds across the rolling/sub-period
   walk-forward views (same discipline as the Phase-A frequency study), not just point-to-point 2020+.

If any of 1–4 fails, the honest finding is recorded as such and the track is rescoped (e.g. demote
the risk-state from a return-overlay to a pure *risk-reporting* dashboard signal, or hand the baton
to the agentic news/macro track for the info-driven falls this model structurally cannot see).

## Status

- [x] HMM risk-state implemented (walk-forward filtered, no look-ahead) + unit-tested
- [x] Synthetic-recovery validation (recovers a known 2-state HMM's params) + no-look-ahead test
- [x] Overlay rides the **exact** validated engine (fidelity vs `run_backtest`: 0.0e+00 equity diff)
- [~] Breadth + valuation features — **not wired**: shown moot for the *sell* overlay (would fire
  more → more realised tax → worse money test). Reserve for a risk-*reporting* signal only.
- [x] The money test — overlay vs always-invested + 1/N, net cost + tax, (τ,floor) sweep, train/holdout/full
- [x] Findings recorded honestly (`reports/riskstate_nifty_findings.md`)

## Outcome (recorded honestly — see `reports/riskstate_nifty_findings.md`)

**The HMM risk-state does NOT clear the money test as a defensive *sell* overlay.** All criteria 1–3
failed and the failure is robust (criterion 4): best config 14.5% CAGR / Sharpe 1.04 vs always-invested
17.2% / 1.08, cutting drawdown only ~1pt while realising **₹94k–128k** of capital-gains tax; it also
trails 1/N. The signal is sound (catches every high-vol regime; synthetic-recovery + no-look-ahead
tests pass) — it fails because a *filtered* model de-risks late / re-risks high, and **selling
appreciated equity to dodge a recoverable drawdown costs more tax than it saves** (the project's
tax-first thesis, confirmed again). **Rescope:** the only tax-neutral version worth testing is a
**fresh-capital deploy-throttle** (route new contributions to cash in stress, never sell) — untestable
on the lump-sum book here; needs a contribution stream. Keep the risk-state as a dashboard
risk-*reporting* / new-deployment-sizing signal, not a sell trigger.
