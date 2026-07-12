# Pre-registration — the low-turnover QUBO on the CLEAN universe (the Stage-A follow-up)

_Registered 2026-07-12, before running. Inherited iron rule: beat 1/N walk-forward, net of Zerodha
cost + capital-gains tax, on the survivorship-free universe; no tuning to manufacture a finding; an
honest negative is valid and will be published._

## Motivation (what Stage A left open)
Stage A (`PREREGISTRATION_qubo_universe.md` → `qubo_universe_findings.md`): QUBO selection on the
static Nifty-100 **lost to 1/N by −2.7pt CAGR but essentially tied risk-adjusted** (Sharpe 1.46 vs
1.49, maxDD −33.3% vs −36.6%). The named mechanism was **₹273k of capital-gains tax from full annual
reselection** — the same tax drag every other track found. Stage A committed to exactly one follow-up:
*"a lower-turnover QUBO variant."* Two confounds must also fall away this time:
1. **Clean universe.** Run on the **point-in-time Nifty-50** (dead names in) — the same universe the
   validated core cleared its bar on — so the 1/N comparison is fair and a real verdict is possible
   (Stage A's static-100 was survivorship-biased → directional only).
2. **Attribution.** Run the **plain QUBO as a control** on the same clean universe, so "the clean
   universe changed things" and "the turnover fix changed things" are separately visible.

## Design — two variants, one run each, parameters fixed here
Identical to Stage A wherever not stated: annual walk-forward **2012-01-01 → 2024-12-31** (the
validated core's window), causal trailing-252d μ/Σ (strictly before the rebalance day), cardinality
**k = 20**, risk_aversion **q = 1.0**, SA solver (steps 6000, restarts 4, seed 0), equal-weight the
picks, executed through qalpha's **`Portfolio.rebalance`** (real FIFO cost + capital-gains tax;
qalpha unmodified), **no-trade band = 0** (the turnover control is the incumbency term below, one
mechanism only, clean attribution).

**PIT candidate rule:** at each rebalance, candidates = `Universe.members_on(date)` ∩ names with a
full clean 252-day price history as-of. A held name that leaves the index stops being a candidate and
is sold at the next rebalance (the realistic index-exit treatment). A held name that delists between
rebalances loses its mark when its prices end (conservative; same treatment Stage A had).

- **V0 — control:** plain QUBO (as Stage A), on the clean PIT-50.
- **V1 — primary: the low-turnover QUBO.** One change: an **incumbency (switching-cost) term** —
  currently-held names get their expected return raised by a fixed **c = 0.02** (2 %/yr) inside the
  QUBO, i.e. `μ_eff = μ + c·held`. This says: *replacing an incumbent must clear the real friction of
  the switch.* **c is derived, not tuned:** round-trip switch friction ≈ sell-side cost ~0.3 % +
  LTCG 12.5 % × a typical ~1-year embedded gain of 12–15 % (≈ 1.5–1.9 %) + re-buy cost ~0.3 % ≈ **2 %
  of position value**. Fixed before running; it will not be adjusted after seeing results.

## Baselines & references
- **The bar: 1/N PIT** (`equal_weight_pit` — look-ahead-free, membership-aware, frictionless), the
  same baseline the validated core's GO used (published: 17.7 % CAGR).
- Reference lines (published, not re-run): Nifty-50 TRI 14.5 %/0.98 · the validated core (annual ·
  shrink) 18.2 %/1.13.

## Pre-registered decision rule
- **V1 clears the bar iff:** full-window **CAGR > 1/N's** (net of cost+tax, vs frictionless 1/N —
  the same asymmetry the core had to beat) **AND** the **median rolling-3y-hold gap vs 1/N ≥ 0**.
- **If V1 clears:** it is promoted to a **fourth book in the product's forward harness** (alongside
  System/Shadow/Baseline) to prove itself forward — the same path every promoted idea takes.
- **If V1 fails:** an honest negative; QUBO stays archived as a near-miss + quantum showcase. No
  re-runs with different k/q/c to flip the verdict.
- V0 is attribution context only; it carries no decision weight.

## Metrics
Full-window CAGR/Sharpe/maxDD net cost+tax · realized capital-gains tax · rebalances executed + names
switched per rebalance (turnover actually realized) · rolling-3y-hold gap distribution vs 1/N
(% ≥ 0, median, worst).
