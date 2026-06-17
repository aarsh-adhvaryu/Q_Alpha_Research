# Hedge robustness battery — A (surface) · B (lag) · D (cost), on the qalpha book

_Pre-registered: regime/PREREGISTRATION_robustness.md. Tax-free Nifty-futures hedge on the validated annual-shrink book, 2012–26, holdings never sold. Baselines: always-invested (Sharpe 1.08, maxDD -25.2%) and 1/N (Sharpe 1.02). 'Clears bar' = Sharpe ≥ always AND maxDD strictly better, still beating 1/N. The Sprint-2 point is h=0.5, τ=0.7, persist=5, lag=1._

## A — Parameter-robustness surface

| h | τ | persist | CAGR_% | Sharpe | maxDD_% | clears | beats_1/N |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.3 | 0.6 | 3 | 15.3 | 1.05 | -22.6 | ❌ | ✅ |
| 0.3 | 0.6 | 5 | 15.8 | 1.06 | -22.7 | ❌ | ✅ |
| 0.3 | 0.6 | 10 | 16.7 | 1.11 | -22.5 | ✅ | ✅ |
| 0.3 | 0.7 | 3 | 17.0 | 1.12 | -22.5 | ✅ | ✅ |
| 0.3 | 0.7 | 5 | 17.0 | 1.12 | -22.5 | ✅ | ✅ |
| 0.3 | 0.7 | 10 | 17.0 | 1.11 | -22.5 | ✅ | ✅ |
| 0.3 | 0.8 | 3 | 17.4 | 1.12 | -22.5 | ✅ | ✅ |
| 0.3 | 0.8 | 5 | 17.5 | 1.13 | -22.5 | ✅ | ✅ |
| 0.3 | 0.8 | 10 | 17.5 | 1.13 | -22.5 | ✅ | ✅ |
| 0.5 | 0.6 | 3 | 14.1 | 1.0 | -22.6 | ❌ | ❌ |
| 0.5 | 0.6 | 5 | 14.8 | 1.03 | -22.8 | ❌ | ✅ |
| 0.5 | 0.6 | 10 | 16.3 | 1.11 | -22.5 | ✅ | ✅ |
| 0.5 | 0.7 | 3 | 16.8 | 1.13 | -22.5 | ✅ | ✅ |
| 0.5 | 0.7 | 5 | 16.9 | 1.13 | -22.5 | ✅ | ✅ |
| 0.5 | 0.7 | 10 | 16.8 | 1.12 | -22.5 | ✅ | ✅ |
| 0.5 | 0.8 | 3 | 17.5 | 1.15 | -22.5 | ✅ | ✅ |
| 0.5 | 0.8 | 5 | 17.8 | 1.15 | -22.5 | ✅ | ✅ |
| 0.5 | 0.8 | 10 | 17.7 | 1.15 | -22.5 | ✅ | ✅ |
| 0.7 | 0.6 | 3 | 12.8 | 0.93 | -22.7 | ❌ | ❌ |
| 0.7 | 0.6 | 5 | 13.7 | 0.98 | -22.9 | ❌ | ❌ |
| 0.7 | 0.6 | 10 | 15.9 | 1.1 | -22.5 | ✅ | ✅ |
| 0.7 | 0.7 | 3 | 16.6 | 1.12 | -22.5 | ✅ | ✅ |
| 0.7 | 0.7 | 5 | 16.7 | 1.13 | -22.5 | ✅ | ✅ |
| 0.7 | 0.7 | 10 | 16.7 | 1.11 | -22.5 | ✅ | ✅ |
| 0.7 | 0.8 | 3 | 17.7 | 1.16 | -22.5 | ✅ | ✅ |
| 0.7 | 0.8 | 5 | 18.0 | 1.17 | -22.5 | ✅ | ✅ |
| 0.7 | 0.8 | 10 | 17.9 | 1.17 | -22.5 | ✅ | ✅ |
| 1.0 | 0.6 | 3 | 10.8 | 0.79 | -23.1 | ❌ | ❌ |
| 1.0 | 0.6 | 5 | 12.2 | 0.87 | -23.0 | ❌ | ❌ |
| 1.0 | 0.6 | 10 | 15.3 | 1.05 | -22.5 | ❌ | ✅ |
| 1.0 | 0.7 | 3 | 16.2 | 1.09 | -22.5 | ✅ | ✅ |
| 1.0 | 0.7 | 5 | 16.5 | 1.1 | -22.5 | ✅ | ✅ |
| 1.0 | 0.7 | 10 | 16.4 | 1.09 | -22.5 | ✅ | ✅ |
| 1.0 | 0.8 | 3 | 17.8 | 1.16 | -22.5 | ✅ | ✅ |
| 1.0 | 0.8 | 5 | 18.2 | 1.18 | -22.5 | ✅ | ✅ |
| 1.0 | 0.8 | 10 | 18.1 | 1.17 | -22.5 | ✅ | ✅ |

- Configs clearing the bar (Sharpe ≥ always **and** maxDD better): **27/36** (75%; bar ≥70%).
- Configs beating 1/N on Sharpe: **31/36** (bar = all).
- Clear-rate by threshold τ (out of 12 each): τ=0.6 → 3/12, τ=0.7 → 12/12, τ=0.8 → 12/12.
- Sprint-2 point (h=0.5, τ=0.7, persist=5) in the **interior** (it + all six immediate neighbours clear): **no** — the failing neighbour(s): [(0.5, 0.6, 5)].
- **A verdict: PARTIAL** — **the result is robust for τ∈[0.7, 0.8] (every h and persist clears there), but τ=0.6 is fragile** — a low threshold hedges too eagerly and a *coincident* gauge bleeds CAGR/Sharpe when it fires on stress that doesn't deepen. The Sprint-2 point (τ=0.7) clears but sits on the *lower edge* of the robust region (its τ=0.6 neighbour fails the strict interior test). **Honest read: the hedge is robust across h and persist, but only above a τ floor — the safe operating envelope is τ≥0.7; do not run it eager (τ=0.6).** This narrows the envelope; it does not kill the idea (per the pre-registered decision rule — A/D failing alone narrows, B/C are decisive).

## B — Execution-lag stress (the decisive test for a coincident gauge)

| lag_days | CAGR_% | Sharpe | maxDD_% | clears |
| --- | --- | --- | --- | --- |
| — | 17.2 | 1.08 | -25.2 | (always-invested) |
| 1 | 16.9 | 1.13 | -22.5 | ✅ |
| 2 | 16.9 | 1.13 | -22.5 | ✅ |
| 3 | 16.6 | 1.11 | -22.5 | ✅ |
| 5 | 16.6 | 1.11 | -22.5 | ✅ |

- **B verdict: PASS** — bar = still cuts maxDD and keeps Sharpe ≥ always-invested at lag = 2 **and** 3 trading days (a realistic manual delay). lag = 5 is the stress extreme (informational).

## D — Cost / slippage stress

| cost_× | F&O_tax | CAGR_% | Sharpe | maxDD_% | clears |
| --- | --- | --- | --- | --- | --- |
| 1.0 | 30% | 16.9 | 1.13 | -22.5 | ✅ |
| 1.0 | 40% | 16.8 | 1.12 | -22.5 | ✅ |
| 2.0 | 30% | 16.8 | 1.13 | -22.5 | ✅ |
| 2.0 | 40% | 16.7 | 1.12 | -22.5 | ✅ |
| 3.0 | 30% | 16.8 | 1.12 | -22.5 | ✅ |
| 3.0 | 40% | 16.7 | 1.12 | -22.5 | ✅ |

- Breakeven cost multiple (edge disappears beyond): **>10** the modelled F&O cost.
- **D verdict: PASS** — bar = clears at 2× costs.

## Verdict (A · B · D)

- A (robust neighbourhood): **PARTIAL — robust for τ≥0.7**
- B (survives execution lag): **PASS** _(decisive)_
- D (survives 2× costs): **PASS**

**On-book robustness: PASS (with a narrowed envelope: operate at τ≥0.7).** The decisive lag test passes — protection survives a 2–3 day manual-execution delay — and the edge holds at 2× costs. A only narrows the operating envelope (τ≥0.7), it does not disqualify. Multi-crash generalisation (experiment C) is in `hedge_crashes_findings.md`.
