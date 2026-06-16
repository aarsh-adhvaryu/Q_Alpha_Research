# HMM risk-state deploy-throttle on the Nifty 50 — money-test findings

_Pre-registered experiment (`src/qalpha_research/regime/PREREGISTRATION_riskstate.md`). Reported
honestly, including the negative result. Selection of (τ, floor) was confined to the 2012–2019
training window; the 2020+ holdout was never used to choose a config._

## What was tested

The regime track's pivot after the [LPPLS negative](../src/qalpha_research/regime/PREREGISTRATION.md):
a **Gaussian HMM risk-state** (filtered P(stress) on index return / realised-vol / drawdown,
walk-forward, no look-ahead) driving a **defensive exposure overlay** — scale equity toward cash when
the regime turns to stress, redeploy when it clears. The question: does timing exposure on this
signal beat **staying fully invested** in the validated annual-`shrink` strategy, and beat **1/N**,
net of Zerodha cost + capital-gains tax?

**Engine fidelity (the methodological anchor).** The overlay is run through a research-side loop that
reuses qalpha's *exact* validated primitives (`decide_rebalance` + `Portfolio` FIFO/cost/tax); the
product repo is never modified. With exposure ≡ 1.0 the loop reproduces `qalpha.run_backtest`
**bit-for-bit — max relative equity difference 0.0e+00**. So every equity difference below is caused
by the overlay alone, measured by the same code that trades.

## Result vs the pre-registered bar

**TRAIN 2012–2019 (the only window allowed for choosing a config):**

| strategy | CAGR | Sharpe | maxDD |
|---|---|---|---|
| Overlay τ=0.5/0.8, floor=0.0 | 3.0% | 0.33 | -19.1% |
| Overlay τ=0.5/0.8, floor=0.5 | 9.1% | 0.83 | -17.2% |
| Always-invested (shrink) | 12.1% | 0.87 | -20.9% |
| 1/N equal-weight | 15.5% | 1.01 | -21.1% |

**FULL 2012–2026 (net cost + tax):**

| strategy | CAGR | Sharpe | maxDD | realised cost+tax |
|---|---|---|---|---|
| Overlay floor=0.0 | 11.2% | 0.86 | -21.4% | **₹127,699** |
| Overlay floor=0.5 | 14.5% | 1.04 | -24.2% | **₹94,454** |
| Always-invested (shrink) | 17.2% | 1.08 | -25.2% | — |
| 1/N equal-weight | 16.6% | 1.02 | -39.0% | — |

| Criterion (fixed in advance) | Outcome |
|---|---|
| 1. Money test — beat always-invested on Sharpe (no material wealth loss) OR ≥5pt lower DD at ≥equal Sharpe | ❌ **FAILED** — best config loses Sharpe (1.04 vs 1.08) and 2.7pts CAGR while cutting DD only ~1pt. |
| 2. Beat 1/N net of cost + tax | ❌ **FAILED** — 14.5% vs 16.6% CAGR. |
| 3. Not a tax mirage | ❌ **CONFIRMED mirage** — the small drawdown relief is swamped by **₹94k–128k** of realised capital-gains tax. |
| 4. Robust, not a single-window fluke | ✅ (for the negative) — fails on train **and** full window; the lone marginal Sharpe blip is on the holdout for the config that was *worst* on train, so it cannot be selected. |

A robustness note, not tuning: **τ = 0.5 and τ = 0.8 give identical results** — the filtered HMM
posterior saturates to ~0/1, so the threshold is not a sensitive knob. The failure is structural.

## Honest interpretation — *why* it fails (the interesting part)

The risk-state itself is **not broken**: it cleanly flags the high-vol regimes (2015–16, 2018, COVID
2020 all peak P(stress) ≈ 1.0) and the synthetic-recovery + no-look-ahead tests pass. It fails as a
*return overlay* for two compounding reasons, both core to this project's thesis:

1. **It de-risks late and re-risks high.** A *filtered* (causal) regime model can only react once
   volatility has already appeared — typically part-way down — and turns off only after calm returns,
   i.e. after the rebound. Selling near troughs and rebuying near recoveries is a structural
   give-up of return; the drawdown it removes is mostly the recoverable part.
2. **Selling appreciated equity in a taxable account is expensive.** Each de-risk realises STCG/LTCG;
   the overlay churned **₹94k–128k** of cost + tax that the always-invested book never pays. This is
   the same force that makes the product's edge "**trade less, tax-aware**" — a timing overlay trades
   *more*, and the tax code punishes it.

**Adding breadth / valuation confirmers would not rescue this.** They were motivated by the HMM
*missing* the low-vol 2021–22 grind — i.e. they would make the signal fire *more often*, which means
*more* de-risk/re-risk events and *more* realised tax. They could improve a pure risk-*reporting*
signal, but they push the *return-overlay* money test further into the red, not out of it.

## Implications / constructive rescope

1. **Reject the sell-down overlay** for the taxable core. The validated always-invested annual-shrink
   book already earns Sharpe 1.08; its drawdowns are *market* drawdowns that cannot be dodged
   tax-efficiently by selling and rebuying the same names.
2. **The one version still worth testing is tax-free by construction: a fresh-capital deploy-throttle**
   — when the regime is stressed, route *new* contributions (SIP inflows) to cash and deploy on the
   all-clear, **never selling existing lots**. That incurs *zero* capital-gains tax (the killer here)
   and only ever defers buys. This backtest could not test it (no inflows in the ₹2L lump-sum book);
   it needs a contribution stream and is the legitimate next experiment.
3. **Keep the risk-state as a reporting / position-sizing signal**, not a sell trigger — surface
   "elevated regime risk" on the dashboard and size *new* deployments, leaving the held book alone.
4. **Exogenous shocks remain out of scope** (filtered model reacts after the fact) — handle with
   position sizing + the existing dynamic-drawdown rule, as pre-registered.

## Reproduce

```bash
uv run python scripts/exp_riskstate.py        # fidelity check + (τ,floor) sweep, net cost+tax
```

Honest read: **the HMM risk-state does not clear the money test as a defensive sell-overlay on the
Nifty 50 — not because it can't see stress, but because acting on it by selling appreciated equity
costs more tax than the drawdown it spares.** The negative is informative: it re-confirms the
project's tax-first thesis and points to the only tax-neutral version worth pursuing (a fresh-capital
deploy-throttle).
