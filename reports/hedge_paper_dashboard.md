# Q-Alpha Research — Tax-Free Hedge (forward paper run)

_Forward paper overlay of the Sprint-2 gauge-triggered short-futures hedge on a passive NIFTY book — **no real derivatives traded**. Validated config: τ=0.7, persist=5, h=0.5. As of **2026-06-23** (started 2026-06-19)._

## Gauge & hedge state now

| | |
|---|---|
| Systemic-stress gauge | 🟢 **0.54** (calm) |
| Hedge state | **— hedge off** |
| Forward paper days | 3 |
| Hedge episodes so far | 0 |

## Forward paper performance (indexed to 1.0 at start)

| Book | Return | Final |
|---|---|---|
| Unhedged NIFTY | -1.42% | 0.9858 |
| Hedged (paper) | -1.42% | 0.9858 |

Hedge effect to date: **+0.00 pts** (F&O cost 0.00% + tax 0.00% of book, both modelled).

## Validated backtest evidence (what this forward run re-tests)

_qalpha book 2012–26 (incl. COVID); index 1997–2026 (incl. 2008 GFC + COVID)._

- **Full book:** Sharpe 1.08→1.13, maxDD −25.2→−22.5, CAGR ~flat, still beats 1/N
- **COVID 2020:** drawdown −25.2→−9.7, Sharpe 1.55→2.47
- **Index 2008 + COVID:** 2008 GFC DD −60.9→−52.1 · COVID −38.1→−22.8 (OOS, untuned)
- **Robustness:** survives 2–3d execution lag, ≫10× cost + 40% tax bracket; operate at τ≥0.7

## Honest read

- The gauge is **coincident** and severe crashes are rare → a calm window keeps the hedge OFF and the two curves identical. That is *expected_*; the hedge only earns its keep through a real stress event, which can't be scheduled. Absence of an event is **not disproof**.
- This is **research, forward in real time** — if it holds through a live event over months it is ready to integrate alongside the product's GO. It trades nothing; the product never imports from here.

---
_Regenerated daily by the cron (`scripts/hedge_paper.py daily`); not by hand._
