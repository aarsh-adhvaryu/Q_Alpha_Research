# The low-turnover QUBO on the CLEAN universe (PIT Nifty-50, net cost + tax)

Pre-reg: `reports/PREREGISTRATION_qubo_lowturnover.md` — Stage A's committed follow-up. Clean point-in-time universe (dead names in) → a real verdict, unlike the static-100 run. Config: annual 2012–2024 · k=20 · q=1.0 · SA(6000×4, seed 0) · band 0 · incumbency c=0.02 (V1 only, fixed pre-run). qalpha reused unmodified (Portfolio FIFO cost+tax).

## Full-window (net cost + tax)

| series | CAGR | Sharpe | maxDD | tax | rebal | vs 1/N |
|---|---|---|---|---|---|---|
| **V1 low-turnover QUBO (c=0.02)** | 11.5% | 0.87 | -33.9% | ₹25,933 | 11 | **-5.8pt** |
| **V0 plain QUBO (control)** | 12.3% | 0.92 | -34.0% | ₹28,706 | 11 | **-5.0pt** |
| 1/N PIT (frictionless, the bar) | 17.3% | 1.06 | -39.0% | ₹0 | — | — |
| _references (published)_: Nifty-50 TRI 14.5%/0.98 · validated core (annual·shrink) 18.2%/1.13 | | | | | | |

## Pre-registered verdict (V1)

- Full-window CAGR vs 1/N: **-5.8pt** → FAILS leg 1.
- Rolling-3y-hold gap: median **-2.8pt**, ≥1/N in **16%** of holds, worst **-21.1pt** → FAILS leg 2.
- Switching churn: names sold per rebalance [0, 12, 10, 12, 12, 9, 11, 11, 11, 12, 13] (control: see V0 row).

**VERDICT: DOES NOT clear the bar — honest negative, stays archived.**

V0-vs-V1 is the attribution: the same QUBO on the same clean universe, with and without the switching-cost term — the difference is what the turnover fix (not the universe) bought.

