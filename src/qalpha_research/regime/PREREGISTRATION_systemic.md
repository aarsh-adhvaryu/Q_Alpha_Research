# Pre-registration — Systemic-fragility gauge + tax-aware defensive overlay (regime track, Sprint 2)

Written **before** collecting data or looking at any result, per the Q-Alpha iron rule (no tuning to
manufacture a finding; a negative result reported honestly is valid). This supersedes the
sell-overlay framing of `PREREGISTRATION_riskstate.md` (which **failed** the money test on tax drag —
see `reports/riskstate_nifty_findings.md`) with a **tax-free hedge** design and a **cause-agnostic**
gauge.

## Problem statement (what / why / how / bar)

- **What:** a **cause-agnostic systemic-fragility + stress gauge** for Indian equities — *not* a crash
  predictor. It scores how much "dry tinder" exists (fragility) and whether it is starting to burn
  (stress), regardless of the trigger.
- **Why:** crashes arrive from an **unbounded, unpredictable trigger set** — global contagion
  (2008 US housing, *not* an Indian bubble), oil shocks, USD-INR crises, war, domestic credit blowups
  (2018 IL&FS), and pure exogenous shocks (COVID). You cannot enumerate or time the trigger. But the
  *fragility* (valuation, leverage, concentration, complacency) is measurable, and the *transmission
  symptoms* (FII outflows, INR weakness, vol, credit spreads, correlation→1) are **common across all
  causes**. The objective is **risk-adjusted return — "reduce risk, keep profit as much as we can"**
  (i.e. Sharpe, net of cost+tax) — *not* prediction.
- **How (the action model):** the gauge drives a **tax-aware defensive overlay**, choosing the lever
  by whether the risk is *concentrated* or *systemic*, and always preferring the tax-free option:
  1. **Dry powder** — throttle *new* deployment to cash when fragility is extreme (tax-free; only
     defers buys). Deploy hard *after* the fall ("invest heavily when it falls").
  2. **Sector rotation** — when froth is *concentrated* (one sector/factor stretched), route **new
     money** to cheaper sectors (tax-free). Note: rotation does **not** help a *systemic* crash —
     correlations go to 1 and every sector falls together (the 2008 lesson).
  3. **Hedge ("keep the shares, nullify the exposure")** — when risk is *systemic*, offset downside
     **without selling**: short Nifty futures (linear, modelled first) and/or long puts (convex,
     later). No capital-gains tax realised on the held book; cost is premium/carry + a timing bet.
  4. **Net market short** — *optional, extreme-conviction only.* Short MORE than the long book = a
     **directional bet** (profits if the market falls, **loses if it rises**). Flagged as speculation,
     **not** a hedge — it can violate "reduce risk" when the (often early) signal is wrong.
  5. **Tax-minimised sell (fallback)** — if no tax-free lever suffices, **sell and pay the tax only
     when the avoided loss exceeds the realised tax.** Tax is *minimised, not forbidden*; the §4.6
     FIFO/tax engine + advisor compute this comparison exactly.
- **The bar:** acting **rarely** (only at fragility extremes), the overlay must **beat always-invested
  net of ALL costs** (option premium / futures carry / F&O tax + equity cost+tax), **cut drawdown in
  2000 / 2008 / 2018**, **stay calm in benign years** (few false alarms), and **stay honestly silent
  before the unforecastable** (COVID 2020 — silence there is *correct*, not a miss).

## Hypothesis

**H1 (the real claim):** a cause-agnostic fragility gauge driving a **tax-free hedge** overlay
improves risk-adjusted return (Sharpe) and/or cuts drawdown, **net of all costs**, vs staying fully
invested — because hedging removes the capital-gains-tax drag that sank the sell-overlay (Sprint 1),
and fires rarely enough that premium/carry doesn't bleed the edge away.

**H0 (the null we must take seriously):** it does not beat always-invested net of all costs — the
gauge is too laggy, premium/carry drag over many calm years exceeds the occasional avoided loss, or
it cries wolf. (Recall: fragility signals are often *early by 1–3 years* — "markets stay irrational
longer than you stay solvent" — so a hedge held too long bleeds and misses upside.)

**Explicit non-claims:** we do **not** predict the trigger or the crash date; we do **not** claim to
catch exogenous shocks (COVID). Silence before an unforecastable shock is a correct result.

## The gauge — three cause-agnostic layers

1. **Global fragility (multi-asset — "where is the dry tinder?"):** US/global **credit spreads**
   (BofA HY/IG OAS — the 2008 early tell), US equity & tech valuation + **concentration** (Mag-7
   share, NASDAQ P/E), **MOVE** (bond vol), housing, China property, crypto, commodities.
2. **Transmission to India (the contagion pipes):** **FII/DII net flows**, **USD-INR**, India VIX,
   US VIX, DXY, EM credit (EMBI) spreads, **cross-asset correlation** rising toward 1.
3. **Domestic vulnerability (amplifier, not cause):** Nifty & sector P/E, mcap/GDP, **credit-to-GDP
   gap**, breadth (% > 200DMA), leverage (F&O OI, margin).

The score is a **small, robust, percentile-ranked composite** (z-score blend of a *pre-committed*
short factor list) — **NOT** a supervised crash classifier. India has only ~4 true crash events; a
fitted classifier would overfit hopelessly. The composite + a Greenwood-Shleifer-style *conditional*
crash-frequency reading is the honest object. **Pre-commit the factor list and the weighting scheme
here before any fitting.**

## Method / discipline

- **No look-ahead** — every input lagged to its real release; percentile ranks use trailing windows
  only (same rule as the HMM filtered posterior).
- **Walk-forward / OOS** — choose any thresholds on a pre-2015 training span; evaluate on the rest.
- **Run through the validated engine** — the overlay reuses qalpha's `Portfolio`/`decide_rebalance`
  via the research-side runner (`overlay_backtest.py`), extended with a derivatives leg; the equity
  book's cost+tax stays the exact validated FIFO code. qalpha is **never modified**.
- **Validation of the gauge itself** — must elevate before 2000/2008/2013/2018 and stay low in calm
  spans, *before* any money test is run on it.

## Phasing (honest — the hedge backtest is a real lift)

- **P1 — Build + validate the gauge.** Assemble the cross-asset dataset (all free: FRED, niftyindices,
  RBI, NSE, AMFI). Confirm it elevates before the endogenous crashes, stays calm in benign years, and
  is silent before COVID. *No trading claim yet.*
- **P2 — Futures-hedge money test.** Short-Nifty-futures overlay (linear: index returns + carry/roll +
  **F&O business-income tax + STT**, which differs from capital-gains). The first real "reduce risk,
  keep profit" test.
- **P3 — Puts + sector rotation + the tax-minimised-sell fallback.** Options pricing (Black-Scholes
  with India VIX, or historical chains) for the convex hedge; rotation on new money; the
  avoided-loss > tax sell rule.

## Success bar (fixed in advance — ALL must hold, on the OOS span, net of ALL costs)

1. **Money test:** the overlay beats always-invested on **Sharpe** without materially worse end
   wealth, OR delivers **≥5pt lower max drawdown at ≥ equal Sharpe**. A drawdown cut that sacrifices
   Sharpe is a fail.
2. **Beats 1/N** net of all costs.
3. **Not a premium/tax mirage:** total premium + carry + F&O tax is reported; if it erases the
   benefit, that's a fail.
4. **Right when it matters, quiet when it doesn't:** cuts drawdown in ≥2 of {2000, 2008, 2018},
   stays below threshold in calm years ≥80% of the time, and is silent before COVID.
5. **Robust** across sub-periods / rolling holds, not a single-window fluke.

If any of 1–5 fails, record the honest negative and rescope (e.g. demote to a dashboard
risk-reporting / position-sizing signal — the Sprint-1 fallback).

## Status

- [ ] P1: cross-asset fragility dataset assembled (committed CSVs) + gauge validated vs 2000/08/13/18
- [ ] P2: futures-hedge money test (net F&O tax) vs always-invested + 1/N
- [ ] P3: puts + rotation + tax-minimised-sell fallback
- [ ] Findings recorded honestly (`reports/systemic_findings.md`)

## Outcome

_(to be filled in after the run — positive or negative, reported either way)_
