# Pre-registration — the A/B/C forward study: "does it work, and does the AI help?"

**Registered before running (the repo's iron rule).** This fixes the question, the method, and the
bar *before* any book accrues, so the answer can't be rationalised after the fact.

## The question (user's words, 2026-07-11)
*"Say the model provided recommendations and the AI provided the insight, and the system did the
investment — did it work? Was it working? Did I lose money?"* — measured forward, on fake money, as a
**new parameter in the complete-system test** while we still wait on the GO signal.

## Design — three fake books, identical cash flows
Run forward from a fixed start with the **same** (fake) cash injections applied to all three, so a
value comparison is fair:

| Book | Rule |
|---|---|
| **A — strategy only** | The validated deterministic `advise_deploy_into_weakness` deploys a **tranche of the idle wallet** into the most out-of-favour names (₹0-tax buys). No AI. |
| **B — strategy + AI** | Identical, but the day's AI **signal** (`lean` × `confidence`) tilts the deploy size by a fixed, pre-registered rule (`signal_tilt`, clamped ×0.5–×1.5). Nothing discretionary. |
| **C — buy-and-hold** | Every injection buys NIFTYBEES immediately and holds. The dumb baseline. |

**Deploy schedule — always opportunistic, more on dips (fixed, not tuned).** The wallet is never
fully idle: even a calm market gets a modest base deployment into the individual names most pulled
back from their *own* 1-year high (the engine's per-name cheapness tilt — the real edge, since obvious
broad dips are already crowded by funds/optimisers). The **tranche of the wallet** scales with broad
weakness: `normal 0.25 · elevated 0.50 · deep 1.00`. Deploys are paced (on a cadence + on each
injection + when weakness escalates) so a tranche never drains the wallet in one day. **"Opportunistic"
= the validated deterministic engine; there is no learning/prediction model — the study *measures*
whether the opportunism pays, forward. Nothing is claimed in advance.**

Money is `Decimal`. Each book tracks **net contributions** separately from value, so an injection is
never counted as profit (`profit = value − net_contributions`).

## The AI signal (unvalidated by construction — that's the point)
The daily brief emits one machine-readable line: `SIGNAL: lean=<up|flat|down>; band=<lo>..<hi>;
confidence=<low|medium|high>`. Book B consumes it **deterministically** via `signal_tilt` — the AI
*supplies* the signal, a fixed rule *acts* on it. The AI never computes money and never touches Book A.

## What "worked" means — pre-committed, per decision and overall
- **Per decision:** each deploy is logged with the model rationale + the AI insight at that moment;
  ~20 trading days later its realised return is compared to Nifty over the same window →
  `worked` (beat Nifty by >0.5pt) / `didn't` (lagged by >0.5pt) / `flat`.
- **Overall (the verdict):** after ≥3 months and ≥1 volatility event, compare final **profit** of
  A vs B vs C. Claims, in order of what would be interesting:
  1. **A > C** — the strategy's deploy-into-weakness beats blindly holding (the core value).
  2. **B > A** — the AI insight *adds* value (would be a genuine, surprising positive — held to the
     repo's usual bar: it must beat A net, not just once, before it's believed).
  3. **B < A** — the AI insight *hurts* (a valid, publishable negative — likely, and fine).
- **AI accuracy (separate):** each `SIGNAL.lean` is scored against the actual next-window Nifty move
  → a running hit-rate. Low hit-rate ⇒ the AI's "read" is narrative, not signal (the expected result).

## Honesty guards
- **Fake money only.** The product's clean ₹2L GO paper run is untouched; this never trades or feeds
  the engine. Real Zerodha stays 100% manual.
- **No tuning to a result.** `signal_tilt` weights are fixed here and not changed to flatter B.
- **Negatives are published.** "The AI didn't help" is a valid, expected outcome — the point is to
  *measure*, not to make the AI look good.
- **Low power early.** Months of data + a real stress event are needed before any claim; until then
  the dashboard shows the accruing numbers, not a verdict.
