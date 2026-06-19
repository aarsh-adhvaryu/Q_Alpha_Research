"""hedge_paper.py — the tax-free futures hedge run FORWARD as a live paper overlay.

Sprint 2 proved the gauge-triggered short-futures hedge clears the bar *in backtest*. This runs the
**same** validated machinery (`fragility.compute_fragility` → `hedge.hedge_active` →
`hedge.apply_futures_hedge`) **forward in real time** on a passive Nifty book, accumulating a live
paper track record — the hedge's analogue of the product's criterion-6 paper run. No real derivatives
are traded: it tracks what the hedge *would* do (modelled F&O cost + 30% business-income tax), so if
it holds up live over months it is ready to integrate alongside the product's GO.

**Stateless by design:** the cross-asset panel IS the state. Each daily run recomputes the forward
curve from a fixed :data:`FORWARD_START` to today off the (refreshed) panel — there are no lots to
persist (a passive overlay), so recomputation can't drift. The gauge uses the panel's full history for
its *causal* percentile ranks (no look-ahead); only the equity curve is restricted to the forward
window.

**Honest caveat (unchanged):** the gauge is *coincident* and severe crashes are rare, so a forward
window may contain no stress event — the hedge then just sits OFF and you get "not disproven", not
"proven in live fire". Its GO legitimately waits on a real event.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from qalpha_research.regime.fragility import compute_fragility
from qalpha_research.regime.hedge import apply_futures_hedge, hedge_active

# The forward paper run begins here (the validated operating point: τ≥0.7, persist 5, h=0.5).
FORWARD_START = date(2026, 6, 19)
DEFAULT_TAU = 0.7
DEFAULT_PERSIST = 5
DEFAULT_H = 0.5


@dataclass(frozen=True)
class HedgePaperResult:
    """A snapshot of the forward hedge paper run: state now + the forward hedged/unhedged curves."""

    forward_start: date
    as_of: date
    base: str
    tau: float
    persist: int
    h: float
    gauge_now: float
    hedge_on: bool
    hedged: pd.Series  # forward paper equity of the hedged book (starts at 1.0 on forward_start)
    unhedged: pd.Series  # forward paper equity of the unhedged book (starts at 1.0)
    episodes: int
    cost: float  # cumulative hedge transaction + roll cost (book-value units)
    tax: float  # cumulative F&O business-income tax on hedge gains

    @property
    def days(self) -> int:
        return len(self.unhedged)

    @property
    def hedged_return(self) -> float:
        return float(self.hedged.iloc[-1] - 1.0) if self.days else 0.0

    @property
    def unhedged_return(self) -> float:
        return float(self.unhedged.iloc[-1] - 1.0) if self.days else 0.0

    @property
    def level(self) -> str:
        """A traffic-light reading of the current gauge (display only)."""
        if self.gauge_now >= self.tau:
            return "elevated"
        if self.gauge_now >= self.tau - 0.15:
            return "watch"
        return "calm"


def forward_hedge_track(
    panel: pd.DataFrame,
    *,
    forward_start: date = FORWARD_START,
    base: str = "nifty",
    tau: float = DEFAULT_TAU,
    persist: int = DEFAULT_PERSIST,
    h: float = DEFAULT_H,
) -> HedgePaperResult:
    """Compute the forward hedge paper run from ``forward_start`` to the panel's last date.

    ``panel`` is the cross-asset fragility panel (``data/fragility_panel.csv``). The gauge and the
    hedge state machine run over the panel's *full* causal history; the hedged/unhedged equity curves
    are then accumulated only over the forward window (normalised to 1.0 at the start).
    """
    gauge = compute_fragility(panel).composite
    base_ret = panel[base].dropna().pct_change().dropna()
    g = gauge.reindex(base_ret.index, method="ffill")
    active = hedge_active(
        g, tau, persist
    )  # full-history state (correct persistence at the boundary)

    fwd_ret = base_ret[base_ret.index >= pd.Timestamp(forward_start)]
    active_fwd = active.reindex(fwd_ret.index).fillna(False).astype(bool)
    res = apply_futures_hedge(fwd_ret, fwd_ret, active_fwd, h=h, apply_costs=True)
    unhedged = (1.0 + fwd_ret).cumprod()

    as_of = base_ret.index[-1].date() if len(base_ret) else forward_start
    gauge_now = float(g.dropna().iloc[-1]) if len(g.dropna()) else 0.0
    hedge_on = bool(active.iloc[-1]) if len(active) else False
    return HedgePaperResult(
        forward_start=forward_start,
        as_of=as_of,
        base=base,
        tau=tau,
        persist=persist,
        h=h,
        gauge_now=gauge_now,
        hedge_on=hedge_on,
        hedged=res.equity,
        unhedged=unhedged,
        episodes=res.episodes,
        cost=res.cost,
        tax=res.tax,
    )


def track_record_csv(result: HedgePaperResult) -> str:
    """The forward paper curves as committable CSV: date, hedged, unhedged (both indexed to 1.0)."""
    rows = ["date,hedged,unhedged"]
    unhedged = result.unhedged
    hedged = result.hedged.reindex(unhedged.index)
    dates = pd.DatetimeIndex(unhedged.index).strftime("%Y-%m-%d")
    for d, h, u in zip(dates, hedged.to_numpy(), unhedged.to_numpy(), strict=True):
        rows.append(f"{d},{float(h):.6f},{float(u):.6f}")
    return "\n".join(rows) + "\n"
