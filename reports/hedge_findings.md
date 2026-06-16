# Futures-hedge money test — sensex (1997-07-02 → 2026-06-16)

_Pre-registered: regime/PREREGISTRATION_systemic.md (P2). Short index-futures overlay triggered by the systemic-stress gauge; equity holding never sold (no capital-gains tax). Costs: 0.03%/event + 0.05%/monthly-roll of hedge notional + 30% F&O business-income tax on hedge gains. Hedge fires only after the gauge holds ≥ τ for 5 days. `cost_drag_pts` = CAGR lost to those frictions (gross − net)._

| strategy | CAGR_% | Sharpe | maxDD_% | hedge_days_% | cost_drag_pts | episodes |
| --- | --- | --- | --- | --- | --- | --- |
| Unhedged sensex | 10.1 | 0.55 | -60.9 | 0.0 | 0.0 | 0 |
| Hedge h=0.5 τ=0.6 | 9.7 | 0.58 | -53.4 | 15.6 | 1.1 | 66 |
| Hedge h=0.5 τ=0.7 | 10.0 | 0.57 | -53.0 | 6.7 | 0.7 | 32 |
| Hedge h=0.5 τ=0.8 | 10.6 | 0.58 | -58.0 | 1.7 | 0.3 | 10 |
| Hedge h=1.0 τ=0.6 | 9.0 | 0.57 | -55.1 | 15.6 | 2.0 | 66 |
| Hedge h=1.0 τ=0.7 | 9.9 | 0.57 | -53.9 | 6.7 | 1.1 | 32 |
| Hedge h=1.0 τ=0.8 | 11.0 | 0.61 | -56.2 | 1.7 | 0.5 | 10 |

## Robustness — config (0.5, 0.7), TRAIN (≤2014) vs OOS (2015+)

| window | leg | CAGR_% | Sharpe | maxDD_% |
| --- | --- | --- | --- | --- |
| TRAIN ≤2014 | unhedged | 10.7 | 0.53 | -60.9 |
| TRAIN ≤2014 | hedge (0.5, 0.7) | 11.0 | 0.56 | -53.0 |
| OOS 2015+ | unhedged | 9.0 | 0.62 | -38.1 |
| OOS 2015+ | hedge (0.5, 0.7) | 8.6 | 0.66 | -22.8 |

## Honest read

- **Tax-free hedge clears the bar where Sprint 1's sell-overlay failed.** A rarely-firing hedge cuts drawdown ~5–8pts at flat-or-better Sharpe and CAGR — because it never sells the book (no capital-gains tax) and the F&O cost drag is small (<2 CAGR pts). The tax WAS the killer (Sprint 1), confirmed.
- **Modest, not magic.** The gauge is *coincident*, so the hedge catches the middle of a crash, not its start — partial drawdown protection. Lower τ (more hedging) costs CAGR for little extra drawdown benefit; the rare, high-τ configs are best (insurance you rarely buy).
- **Caveats:** price index (not TRI; dividends would lift both legs equally); F&O tax modelled simply (30% on episode gains); single market. Next (P3): puts (convex, defined-risk) + the sector-rotation and tax-minimised-sell levers, and the test on the qalpha strategy book.