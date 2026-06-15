# Pre-registration — Bubble/crash detection (regime track)

Written **before** looking at any result, per the Q-Alpha iron rule (no tuning to manufacture a
finding; a negative result reported honestly is a valid outcome).

## Hypothesis (what we are actually testing)
**H1 (bubble, the real claim):** the LPPLS confidence indicator on the Nifty 50 rises *before*
endogenous, valuation-driven drawdowns, with enough lead time (weeks–months) and few enough false
alarms to be useful as a **deploy throttle**.

**H0 (the null we expect to often hold):** it does not beat a naive "always deploy" rule net of
cost + tax, and/or its warnings are too noisy/late to act on.

**Explicit non-claim:** we do **not** claim to forecast *exogenous* shocks (e.g. COVID Mar-2020).
If LPPLS stays quiet before 2020, that is a **correct** result, not a failure — it is the honest
boundary of the method.

## Data
- Nifty 50 via NIFTYBEES daily close, 2012-01-02 → 2026-06-12 (`data/nifty50_nifbees_close.csv`).
- Out-of-sample reference drawdowns (peaks, for lead-time scoring), fixed now:
  - ~Mar 2015 (2015–16 correction) — partly endogenous
  - ~Aug/Sep 2018 (NBFC/IL&FS) — partly endogenous
  - ~Jan 2020 (COVID crash Feb–Mar) — **exogenous** (expected: LPPLS quiet)
  - ~Oct 2021 → 2022 correction — partly endogenous

## Method
- LPPLS (Filimonov–Sornette 3-nonlinear-parameter formulation) fit on rolling windows.
- DS-LPPLS **confidence indicator** at each "present" date t2: fraction of windows (varying length)
  whose fit passes the standard bubble filter (m∈[0.1,0.9], ω∈[2,25], B<0 for a positive bubble,
  Bothmer–Meister damping ≥ 0.8, tc near/after t2). Confidence ∈ [0,1].

## Decision rule under test (deploy-throttle only — NEVER auto-sell)
When confidence ≥ τ, route fresh-capital deployment to a cash buffer instead of buying; resume when
it falls below τ. τ is **not** tuned to the outcome — we report the full ROC/lead-time curve across τ.

## Success bar (fixed in advance)
The method is declared **useful** only if ALL hold on the reference set:
1. **Lead:** confidence crosses τ **≥ 4 weeks before** ≥2 of the 3 endogenous peaks.
2. **Precision:** in the calm stretches (no drawdown within 6 months), confidence is below τ **≥ 80%**
   of the time (i.e. ≤ ~1 sustained false alarm per ~2 years).
3. **Exogenous honesty:** stays below τ before the 2020 COVID peak (or if it fires, we document why).
4. **The money test (the real bar):** the deploy-throttle rule beats "always deploy" **net of
   Zerodha cost + capital-gains tax, walk-forward**, without materially worsening end wealth.

If any of 1–4 fails, the honest finding is recorded as such and the track is shelved or rescoped
(most likely outcome per the literature: detects bubbles with lead, but the *money test* is marginal
because acting on the sell side is tax-expensive — only the deploy throttle has a chance).

## Status
- [x] LPPLS implemented + unit-tested (recovers a known synthetic bubble tc to 4 dp)
- [x] Confidence indicator computed over Nifty history
- [x] Lead-time / false-positive scoring vs the reference set
- [~] The money test — **moot**: no usable signal (see below)

## Outcome (recorded honestly — see `reports/lppls_nifty_findings.md`)
**LPPLS does NOT clear the bar on the Nifty 50.** Criterion 1 (lead) failed — max confidence ever
≈0.33, only the 2021 ATH crossed 0.3 and only 5 days before the peak. Criteria 2 & 3 passed
(near-zero false positives; 0.00 before the exogenous COVID crash — correct). A robustness check
(6× optimizer starts) confirmed the low ceiling is genuine, not an artifact: **Nifty large-cap
2012–2026 simply did not have parabolic LPPLS-style bubbles.** Pivot → valuation/breadth + HMM
risk-state for the index; reserve LPPLS for midcap/smallcap & individual euphoric names.
