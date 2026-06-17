# Multi-crash decomposition — sensex (1997-07-02 → 2026-06-16) — robustness C

_Pre-registered: regime/PREREGISTRATION_robustness.md (C). Same hedge as Sprint 2 (h=0.5, τ=0.7, persist=5, lag=1) on the passive sensex index. Bar: cut drawdown in BOTH deep, differently-caused events (2008 GFC **and** COVID), with calm-year cost drag < 2 CAGR pts._

## Per-event drawdown (hedged vs unhedged)

| event | unhedged_DD_% | hedged_DD_% | DD_cut_pts | hedge_days_% | deep | cut? |
| --- | --- | --- | --- | --- | --- | --- |
| GFC 2008 (US housing) | -60.9 | -52.1 | 8.8 | 33.2 | deep | ✅ |
| Euro/downgrade 2011 | -20.5 | -20.7 | -0.3 | 5.2 | — | ❌ |
| China-yuan 2015–16 | -18.9 | -17.2 | 1.7 | 49.7 | — | ✅ |
| IL&FS 2018 | -13.1 | -13.1 | -0.0 | 0.0 | — | ❌ |
| COVID 2020 | -38.1 | -22.8 | 15.2 | 41.5 | deep | ✅ |
| Rate-hikes 2022 | -16.2 | -19.7 | -3.5 | 38.0 | — | ❌ |

- Full window: unhedged maxDD -60.9% → hedged -53.0%.
- Full-window cost drag (gross − net CAGR): **0.63 pts** (bar < 2.0; hedge fires only in stress, so calm years carry ~no cost).
- Deep events both cut: **yes** (2008 contagion + COVID exogenous — different causes ⇒ cause-agnostic).

## C verdict: PASS

- **The hedge is not a COVID one-off.** It cut drawdown in the 2008 GFC (a US-housing contagion with no Indian bubble) and COVID (a pure exogenous shock) — two crashes with nothing in common except the transmission symptoms the gauge reads. That is the cause-agnostic claim holding on out-of-window history.
