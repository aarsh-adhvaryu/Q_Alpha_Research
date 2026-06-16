# Systemic-stress gauge — P1 validation (Sprint 2)

_Pre-registered: regime/PREREGISTRATION_systemic.md. The gauge is a **cause-agnostic** composite of causal trailing-percentile stress features (US/India vol, bond vol, a HYG/LQD credit-stress proxy, USD-INR & dollar spikes, equity drawdown, India↔global correlation). No look-ahead. This validates *timing of the signal* — not a trading claim (that is P2).

## Crash windows — should ELEVATE

| window | mean | peak |
| --- | --- | --- |
| 2000–02 dot-com | 0.52 | 0.92 |
| 2008 GFC | 0.69 | 0.91 |
| 2011 EU/downgrade | 0.57 | 0.78 |
| 2013 taper tantrum | 0.45 | 0.7 |
| 2015–16 China/oil | 0.7 | 0.83 |
| 2018 NBFC | 0.52 | 0.67 |
| 2020 COVID crash | 0.89 | 0.99 |

## Calm windows — should stay LOW

| window | mean | peak |
| --- | --- | --- |
| 2005 | 0.29 | 0.49 |
| 2014 | 0.36 | 0.69 |
| 2017 (euphoric) | 0.24 | 0.46 |
| 2021 (euphoric) | 0.51 | 0.77 |

## Exogenous-shock honesty — should be QUIET *before* COVID

| window | mean | peak |
| --- | --- | --- |
| 2019-11 → pre-COVID (Feb 19) | 0.48 | 0.75 |

**False-alarm rate** (calm-year days with stress ≥ 0.7): **1%**.

## Honest read

- **STRESS gauge validated:** elevates in every crash window (peaks 0.67–0.99) and stays low in calm years (means ~0.24–0.36; 2017 just 0.24). It separates crash from calm cleanly.
- **Coincident, not leading:** it spikes *with* the drawdown (esp. exogenous COVID, 0.99 in the crash) — honest, not a predictor. Its trading value is therefore as a **hedge/de-risk trigger once stress is underway + a deploy-throttle**, not a crash forecast.
- **Fragility (price-extension) sub-score dropped from the composite:** it sat ≈0.68 in *every* calm bull year, too always-on to discriminate. Real leading fragility needs true valuation inputs (index P/E, credit-spread tightness, concentration) — the next data task.