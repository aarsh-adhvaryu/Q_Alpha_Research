"""Tests for the forward hedge paper run (regime/hedge_paper.py)."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from qalpha_research.regime.hedge_paper import (
    forward_hedge_track,
    track_record_csv,
)

_FWD_START = date(2025, 6, 1)  # the panel below has ≥1y before this, so the gauge is live by then
_COLS = ["sp500", "us_vix", "move", "hyg", "lqd", "dxy", "usdinr", "sensex", "nifty", "india_vix"]


def _panel(seed: int = 0) -> pd.DataFrame:
    """A synthetic cross-asset panel spanning enough history for the gauge to emit (pct_min=252)."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-02", "2025-09-01")  # ~2.7y → gauge live well before _FWD_START
    data = {}
    for c in _COLS:
        steps = rng.normal(0.0003, 0.012, len(idx))
        data[c] = 100.0 * np.exp(np.cumsum(steps))
    df = pd.DataFrame(data, index=idx)
    df.index.name = "date"
    return df


def test_forward_track_is_restricted_to_the_forward_window() -> None:
    res = forward_hedge_track(_panel(), forward_start=_FWD_START, base="nifty")
    assert res.days > 0
    assert res.unhedged.index[0].date() >= _FWD_START  # nothing before the forward start leaks in
    # Both curves are normalised to ~1.0 at the start (paper books begin at par).
    assert abs(float(res.unhedged.iloc[0]) - 1.0) < 0.05
    assert 0.0 <= res.gauge_now <= 1.0
    assert isinstance(res.hedge_on, bool)
    assert len(res.gauge_history) > 1  # the ~2y gauge context series is populated for the chart


def test_never_hedging_equals_unhedged() -> None:
    # An unreachable threshold (gauge ≤ 1.0 < 2.0) → hedge never fires → hedged == unhedged, no cost/tax.
    res = forward_hedge_track(_panel(), forward_start=_FWD_START, tau=2.0)
    assert res.episodes == 0
    assert res.cost == 0.0 and res.tax == 0.0
    assert np.allclose(res.hedged.to_numpy(), res.unhedged.to_numpy())
    assert res.hedge_on is False
    assert res.level == "calm"


def test_track_record_csv_round_trips() -> None:
    res = forward_hedge_track(_panel(), forward_start=_FWD_START)
    csv = track_record_csv(res)
    lines = csv.strip().splitlines()
    assert lines[0] == "date,hedged,unhedged"
    assert len(lines) == res.days + 1  # header + one row per forward trading day
    first = lines[1].split(",")
    assert date.fromisoformat(first[0]) >= _FWD_START
