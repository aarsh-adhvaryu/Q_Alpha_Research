# LPPLS on Nifty 50 (2012–2026) — first-pass findings

_Pre-registered experiment (`src/qalpha_research/regime/PREREGISTRATION.md`). Reported honestly,
including the negative result. No thresholds were tuned to hit the reference peaks._

## Result vs the pre-registered bar

| Criterion (fixed in advance) | Outcome |
|---|---|
| 1. Lead ≥4wk before ≥2 of 3 **endogenous** peaks | ❌ **FAILED** — max confidence ever ≈ 0.33; only the 2021 ATH crossed 0.3, and only **5 days** before the peak (coincident, not lead). |
| 2. Precision — calm stretches below τ ≥80% of the time | ✅ **PASSED** — 100% of calm points below 0.3, mean confidence 0.01. (But trivially: it barely fires *anywhere*.) |
| 3. Exogenous honesty — quiet before the 2020 COVID crash | ✅ **PASSED** — confidence **0.00** before COVID. Correct: an exogenous shock has no LPPLS pre-signal. |
| 4. The money test (deploy-throttle beats always-deploy net of tax) | ⏸️ **moot** — criterion 1 failed, so there is no usable signal to act on. |

**Robustness check (not tuning):** re-running the most bubble-like dates with 6× the optimizer
starts and 2× finer windows did **not** raise confidence (the 2021 peak even fell from 0.33→0.17 as
more windows entered the denominator). So the low ceiling is a **genuine property of the data**, not
an under-convergence artifact.

## Honest interpretation

**LPPLS does not clear the bar on the Nifty 50 — not because the method is broken, but because
Nifty large-cap (2012–2026) has not produced the parabolic, faster-than-exponential *positive
bubbles* LPPLS is built to detect.** The fitter is correct (it recovers a synthetic bubble's `tc`
to 4 decimals) and the one moment it scored highest — Oct 2021, the all-time-high top — is a real
market top. But India large-cap drawdowns in this window were dominated by:
- **exogenous shocks** (COVID 2020) — unforecastable by construction, and LPPLS correctly stayed silent; and
- **valuation/macro mean-reversion** (2015–16, 2018, 2022) — rich valuations + global macro/rates, *not* a domestic parabolic blow-off.

LPPLS catches Nikkei-1989 / dot-com / crypto / Shanghai-2015 style manias. The Nifty 50 was a
steadier secular bull. So the negative result is informative, not disappointing: **for this market's
index, the bubble-singularity signature is mostly absent.**

## Implications for the regime track (where the edge more likely lives)

1. **Pivot the index work to the "boring-but-works" axis** — valuation (Nifty P/E, mcap/GDP) +
   breadth (% > 200DMA) + an HMM/vol risk-state. Nifty drawdowns track *rich valuation + macro/vol
   regimes* far more than LPPLS singularities. This is the more promising deploy-throttle signal.
2. **Keep LPPLS, but point it where Indian parabolic bubbles actually happen** — midcap/smallcap
   indices and individual euphoric names (e.g. the 2017–18 smallcap mania, single-stock blow-offs),
   not the large-cap index. That is LPPLS's natural habitat.
3. **The exogenous-shock half stays unforecastable** — handle it with position sizing + the existing
   dynamic-drawdown rule, not prediction. (Confirmed empirically here: 0.00 before COVID.)
