# Q-Alpha Research

**The frontier / exploratory track for [Q-Alpha](https://github.com/aarsh-adhvaryu/Q_Alpha) — where
ideas are tested honestly against a hard bar, and most of them are *rejected*.**

If you read one paragraph: this repo is the R&D lab. It asks "can we beat the validated product
strategy with something fancier — quantum optimization, crash prediction, a hedging overlay?" The
answer is usually **no, and here's the evidence why** — which is exactly the point. A research track
that only ever produces positive results is lying. This one publishes its negatives, and the **one
thing that did work** (a tax-free hedge) is all the more credible for it.

Crucially, this repo **imports the validated `qalpha` engine** rather than copying it — so every
performance number here is run through the *exact same* tax-aware FIFO/cost code that trades. **The
product never imports from this repo.** That one-way dependency is what keeps the product clean and
audit-ready while the research stays free to experiment.

> **The honest scoreboard:** Quantum selection — near-miss (tax-throttled). Crash prediction (LPPLS) —
> negative. Sell-in-a-downturn overlay — negative (the tax kills it). **Tax-free futures hedge —
> positive** (cuts COVID drawdown from −25% to −10% with no return given up). It's now running forward
> in real time to see if it holds up live.

---

## 1. The one rule everything obeys (the "iron rule")

A performance claim must beat its baseline (equal-weight 1/N, or the existing rule) **walk-forward, net
of Zerodha cost + capital-gains tax, on the survivorship-free universe** — and the bar is
**pre-registered before the experiment runs** so we can't move the goalposts. No in-sample tuning. **A
negative result, written down honestly, is a valid and valuable outcome.** Most of this repo is exactly
that.

---

## 2. The research arc, in plain words (then the findings)

The whole regime/crash-detection effort tells one coherent story, and you can follow it without any math:

1. **"Can we predict crashes and get out first?"** We tried the famous physics model for bubbles
   (LPPLS — it looks for the accelerating, oscillating price pattern that precedes a crash). On Indian
   large-caps, **it found nothing useful** — there simply weren't parabolic bubbles to detect, and it
   was (correctly) silent before COVID, which was an *external* shock, not a bubble bursting.

2. **"Fine, can we at least de-risk when a statistical model says danger?"** We built a regime detector
   (a Hidden Markov Model) that flips to "risky" and *sells* down equity. It **lost money** — not
   because the signal was useless, but because **selling appreciated stock to dodge a recoverable dip
   realizes a 20% tax that costs more than the drawdown it avoids.** The tax was the killer.

3. **"So don't sell — *hedge*."** Keep the shares (no tax), and when a cross-asset stress gauge lights
   up, overlay a short index-futures position to cancel the market exposure. **This worked.** It cut the
   COVID drawdown from −25% to −10% on the strategy book with essentially no return given up. This is
   the track's first and only positive — and the lesson is the same one the product is built on: **the
   tax is always the thing; hedge, don't sell.**

That arc — *predict (no) → sell (no, tax) → hedge (yes)* — is the headline.

---

## 3. The findings in detail (with the math)

### Quantum portfolio selection — honest near-miss
**Idea:** phrase "pick the best 20 of 100 stocks" as a **QUBO** (Quadratic Unconstrained Binary
Optimization) — a math form a quantum computer *could* solve:

```
minimize   xᵀ Σ x  −  q · μᵀ x        subject to  Σ xᵢ = k       (x ∈ {0,1})
            └ risk ┘   └ return ┘                  └ pick exactly k ┘
```

- We solve it classically (simulated annealing) at full scale, and reproduce the **exact optimum** with
  **QAOA** (a quantum algorithm) on a smaller real instance to prove the formulation.
- **Result:** risk-competitive (Sharpe ties 1/N) but it **doesn't beat the bar** — full annual
  reselection realizes ₹2.7L of tax (the tax-first thesis, again). And there's a **hard wall:** a
  100-stock quantum problem needs 2¹⁰⁰ states — infeasible on any simulator (the wall is already at ~10
  stocks). So quantum is a *showcase*, not a production tool, and we say so.
- **The pre-registered follow-up CLOSED the question (2026-07-12,
  `reports/qubo_lowturnover_findings.md`):** a **low-turnover QUBO** (incumbency switching-cost
  `μ_eff = μ + c·held`, c = 2%/yr derived from real round-trip friction, not tuned) on the **clean
  point-in-time Nifty-50** — where a real verdict is possible. **It failed decisively: 11.5% CAGR /
  Sharpe 0.87 vs 1/N's 17.3% / 1.06 (−5.8pt).** Two lessons: the earlier "near-miss" was
  **survivorship flattery** (the plain-QUBO control also lost, −5.0pt, on the clean universe), and tax
  wasn't even the binding drag this time (₹26k vs ₹2.7L) — **trailing-year μ estimates are too noisy
  for subset selection** (the book still swapped ~11/20 names a year despite the switching penalty).
  That is the classic estimation-error result, and exactly why the product's validated core *anchors
  to 1/N* (shrinkage) instead of trusting sample mean-variance. QUBO's final status: a validated
  quantum-formulation showcase + two published honest negatives.

### Crash prediction (LPPLS) — negative
Fitted the Sornette **Log-Periodic Power-Law Singularity** model (the math of a bubble accelerating
toward a critical time `t_c`). Max confidence ~0.33, no useful lead on Indian peaks. The fitter is
validated (it recovers a synthetic `t_c` to 4 decimals — so the *negative* is real, not a bug).
**Conclusion: Nifty large-cap had no parabolic LPPLS bubbles 2012–2026.**

### Sell-overlay (HMM regime switch) — negative, and instructive
A walk-forward filtered Gaussian HMM drives a defensive *sell*. Best case 14.5% CAGR vs 17.2%
always-invested — it **trails**, paying ₹94k–₹128k in realized tax to avoid recoverable dips.
**Mechanism understood:** the tax to exit costs more than the drawdown saved. This is the negative that
*motivated* the hedge.

### Tax-free futures hedge — the positive (clears the pre-registered bar)
- **The gauge:** a cause-agnostic, no-look-ahead **systemic-stress composite** from 13 cross-asset
  series (US & India equity vol, bond vol, credit spreads, the dollar, USD-INR, drawdown,
  India↔global correlation). It's *coincident* (it spikes *with* a crash, not before) — so it's a
  hedge **trigger**, not a forecast, and we're explicit about that.
- **The action:** when the gauge holds above a threshold, short index futures sized at half the book.
  The shares are never sold (**no capital-gains tax**); the only cost is futures transaction + roll +
  **30% F&O business-income tax** on hedge gains (the correct Indian treatment).
- **The result:** on the strategy book 2012–26, Sharpe 1.08→1.13, **COVID drawdown −25%→−10%**, CAGR
  flat, still beats 1/N. On the index 1997–2026 it cut **both** the 2008 and COVID crashes. Futures beat
  puts (the selective gauge fires too rarely for the put's convexity to pay off). It survives a
  realistic 2–3-day execution delay and ≫10× cost stress.

### Running it forward, live
The hedge is now a **forward paper run** (`regime/hedge_paper.py`) with its own daily cron and Streamlit
dashboard — the same machinery applied forward in real time on a passive Nifty book, **trading no real
derivatives**. If it holds through a real live stress event over months, it's a candidate to integrate
alongside the product's go-live. Honestly: it may sit idle for a long time, because crashes are rare and
the gauge is coincident — and that's fine.

---

## 4. Math & methods glossary (for the curious interviewer)

| Term | Plain meaning |
|---|---|
| **QUBO** | Writing a yes/no selection problem as one quadratic equation to minimize — the form quantum/annealing solvers eat. |
| **QAOA** | A quantum algorithm that approximates a QUBO's answer; we use it to *prove* the formulation on small real data. |
| **LPPLS** | The physics model for a bubble: price accelerating with faster-and-faster oscillations toward a critical date. |
| **HMM (Hidden Markov Model)** | A model that infers a hidden "calm vs risky" state from noisy returns. |
| **Coincident vs leading** | A *leading* signal warns before; a *coincident* one fires *during*. Ours is coincident — useful for hedging, useless for forecasting. We never pretend otherwise. |
| **F&O business-income tax** | In India, futures/options P&L is taxed as business income (~30% slab), *not* capital gains — modelled explicitly in the hedge. |
| **Walk-forward, pre-registered** | Test only on unseen data, and write down the success bar *before* running, so a negative can't be quietly reframed as a positive. |

---

## 5. Explicit biases & deliberate decisions (the honesty section)

- **Most results here are negative — by design and reported as such.** That's research integrity, not
  failure. The value is knowing what *doesn't* work (and *why*: almost always the tax).
- **The hedge gauge is coincident, single-market, and tested on few severe crashes** (really only 2008
  and COVID in the windows). We label every one of these caveats; the forward paper run exists precisely
  because backtested crash evidence is thin.
- **F&O tax is modelled simply** (a flat 30% on episode gains). Real slab/setoff nuances would move it
  slightly; the edge survives ≫10× cost/tax stress, so the conclusion is robust to this simplification.
- **The price index isn't a total-return index** for some hedge backtests — dividends would lift both
  the hedged and unhedged legs equally, so it doesn't change the *relative* result, but it's stated.
- **Quantum is a showcase, not production.** The honest scaling wall (2¹⁰⁰) means the real selection is
  always solved classically; we don't pretend a quantum advantage exists here today.
- **Survivorship contamination is called out, not hidden.** The QUBO-on-Nifty-100 result is "directional,
  not a GO" *because* its 1/N baseline sits on a survivorship-biased universe — we refuse to claim a win
  off a contaminated benchmark.
- **Iron rule, again:** bars are pre-registered; nothing is tuned in-sample to manufacture a finding.

---

## 6. Setup & layout

```bash
uv sync --extra dev                  # core + dev tooling (pulls the qalpha engine)
uv sync --extra dev --extra quantum  # + the quantum stack (qiskit) for QAOA
uv sync --extra dev --extra dashboard # + the hedge forward-paper dashboard
PYTHONPATH=src uv run pytest          # 28 tests; QAOA needs --extra quantum
```

`qalpha` resolves from the GitHub product repo by default (`[tool.uv.sources]`); for local co-dev with
both repos checked out as siblings, override to `{ path = "../qalpha", editable = true }`.

```
src/qalpha_research/
  quantum/   QUBO formulation + QAOA / exact-enumeration / simulated-annealing solvers
  regime/    fragility gauge · futures hedge · forward hedge paper run · LPPLS · HMM risk-state · options(puts)
scripts/     experiments (each writes a findings report) + the hedge paper cron + its dashboard
reports/     every experiment's honest write-up (positives AND negatives) + pre-registrations
deploy/      Streamlit Cloud deploy note for the hedge dashboard
```

Findings reports in `reports/` are the detailed evidence for everything above — read them alongside the
pre-registration files (`*PREREGISTRATION*.md`) to see the bar was set before the result was known.
