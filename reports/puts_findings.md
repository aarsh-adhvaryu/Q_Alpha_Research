# Protective puts vs short futures — Nifty (2008-03-03 → 2026-06-16)

_Pre-registered: regime/PREREGISTRATION_systemic.md (P3). Both gauge-triggered (τ=0.7, h=0.5), book never sold. Puts priced Black–Scholes with India VIX; rolled ~monthly. Net of F&O cost + 30% business-income tax on option/futures gains._

## FULL 2008–26

| leg | CAGR_% | Sharpe | maxDD_% |
| --- | --- | --- | --- |
| Unhedged | 8.7 | 0.53 | -51.7 |
| Short futures h=0.5 | 9.3 | 0.6 | -40.2 |
| Protective put h=0.5 | 9.5 | 0.59 | -45.8 |

## 2008 GFC (H2)

| leg | CAGR_% | Sharpe | maxDD_% |
| --- | --- | --- | --- |
| Unhedged | -6.6 | 0.07 | -46.7 |
| Short futures h=0.5 | 7.1 | 0.37 | -34.1 |
| Protective put h=0.5 | 0.3 | 0.2 | -40.4 |

## COVID 2020

| leg | CAGR_% | Sharpe | maxDD_% |
| --- | --- | --- | --- |
| Unhedged | 14.3 | 0.59 | -38.4 |
| Short futures h=0.5 | 21.7 | 1.04 | -23.3 |
| Protective put h=0.5 | 21.9 | 0.97 | -26.5 |

## calm 2017

| leg | CAGR_% | Sharpe | maxDD_% |
| --- | --- | --- | --- |
| Unhedged | 27.9 | 2.83 | -4.1 |
| Short futures h=0.5 | 27.9 | 2.83 | -4.1 |
| Protective put h=0.5 | 27.9 | 2.83 | -4.1 |

## Honest read

- **Both hedges beat unhedged** on CAGR, Sharpe and drawdown — but **short futures beat puts here.** In the deep, grinding 2008 crash the linear short rides the *whole* decline (DD −46.7→−34.1) while the OTM put's protection is bounded and decays (−40.4); in the sharp COVID V they are close.
- **The put's theoretical edge barely shows, because the gauge is *selective*.** Puts are designed to avoid bleeding premium when you hedge needlessly — but in calm 2017 the gauge **never fired**, so all three legs are identical (no premium drag at all). The rare-firing discipline already solves what put convexity is for, so the simpler futures hedge wins.
- **When would puts win?** With a *noisier / more-leading* gauge that fires often and early (more false alarms that rebound) — there the put's keep-the-upside convexity would pay off. With this coincident, selective gauge, it does not.
- **Caveats:** BS with India VIX is an implied-vol proxy (real chains have skew/liquidity); single strike (5% OTM) and ~1m tenor; coincident gauge → partial protection.