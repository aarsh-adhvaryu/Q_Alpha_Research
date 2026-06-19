# Q-Alpha Research — Tax-Free Hedge (forward paper run)

_Forward paper overlay of the Sprint-2 gauge-triggered short-futures hedge on a passive NIFTY book — **no real derivatives traded**. Validated config: τ=0.7, persist=5, h=0.5. As of **2026-06-16** (started 2026-06-19)._

## Gauge & hedge state now

| | |
|---|---|
| Systemic-stress gauge | 🟢 **0.42** (calm) |
| Hedge state | **— hedge off** |
| Forward paper days | 0 |
| Hedge episodes so far | 0 |

## Forward paper performance (indexed to 1.0 at start)

| Book | Return | Final |
|---|---|---|
| Unhedged | — | — |
| Hedged | — | — |

Hedge effect to date: **+0.00 pts** (F&O cost 0.00% + tax 0.00% of book, both modelled).

## Honest read

- The gauge is **coincident** and severe crashes are rare → a calm window keeps the hedge OFF and the two curves identical. That is *expected_*; the hedge only earns its keep through a real stress event, which can't be scheduled. Absence of an event is **not disproof**.
- This is **research, forward in real time** — if it holds through a live event over months it is ready to integrate alongside the product's GO. It trades nothing; the product never imports from here.

---
_Regenerated daily by the cron (`scripts/hedge_paper.py daily`); not by hand._
