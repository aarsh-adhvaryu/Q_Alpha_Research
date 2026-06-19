# Stage-A — QUBO selection on real Nifty 100 (classical SA), walk-forward

⚠️ **Survivorship-biased static universe — directional, NOT a GO.** Read the strategy − 1/N gap. Pre-reg: `reports/PREREGISTRATION_qubo_universe.md`. qalpha reused unmodified (Portfolio FIFO cost+tax).

Config: annual · cardinality QUBO k=20 · risk_aversion=1.0 · SA(steps=6000, restarts=4) · no-trade band=0.0. 11 rebalances.

## Full-window (net cost + tax)

| series | CAGR | Sharpe | maxDD | vs 1/N |
|---|---|---|---|---|
| **QUBO-select (k=20)** | 23.6% | 1.46 | -33.3% | **-2.7pt** |
| 1/N (same universe) | 26.3% | 1.49 | -36.6% | — |

Realized capital-gains tax ₹273,410 (full annual reselection turnover).

## The honest read

- **Return bar:** full-window **-2.7pt** vs 1/N → DOES NOT beat 1/N on CAGR.
- **Risk-adjusted:** QUBO Sharpe **1.46** vs 1/N **1.49**, maxDD **-33.3%** vs **-36.6%** — the QUBO's variance term de-risks (lower DD, comparable/again Sharpe) even on the biased universe.
- **Rolling 3y holds:** QUBO ≥ 1/N in **58%** of holds; worst-3y gap **-16.0pt**, median **+1.1pt**.
- **Mechanism:** full annual reselection realizes **₹273,410** capital-gains tax — the same tax drag the regime track found; it is what keeps QUBO below the frictionless, survivorship-inflated 1/N on raw return. A lower-turnover QUBO variant is the natural (pre-registered) follow-up, not tuned here.

## Selected book — sector spread (picks across rebalances)

- FIN: 44
- PHARMA: 26
- FMCG: 20
- IT: 19
- INFRA: 17
- CONSUMER: 16
- ENERGY: 15
- AUTO: 14
- METAL: 13
- CEMENT: 11
- POWER: 9
- CHEMICALS: 8
- TELECOM: 6
- REALTY: 2
