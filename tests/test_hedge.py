"""Futures-hedge overlay sanity: no-look-ahead, degenerate cases, and it cuts a synthetic crash.

The look-ahead test is load-bearing (an earlier same-day version inflated the P2 result). h=0 and
an all-quiet gauge must reproduce the unhedged book exactly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qalpha_research.regime.hedge import apply_futures_hedge, hedge_active


def _series(n: int, vals: np.ndarray) -> pd.Series:
    return pd.Series(vals, index=pd.bdate_range("2000-01-03", periods=n))


def test_no_hedge_when_ratio_zero() -> None:
    n = 300
    rng = np.random.default_rng(0)
    ret = _series(n, rng.normal(0.0005, 0.01, n))
    active = _series(n, np.ones(n, dtype=bool))
    res = apply_futures_hedge(ret, ret, active, h=0.0, apply_costs=True)
    expected = (1.0 + ret.fillna(0.0)).cumprod()
    np.testing.assert_allclose(res.equity.to_numpy(), expected.to_numpy(), rtol=0, atol=1e-12)
    assert res.cost == 0.0 and res.tax == 0.0


def test_quiet_gauge_reproduces_unhedged() -> None:
    n = 300
    rng = np.random.default_rng(1)
    ret = _series(n, rng.normal(0.0004, 0.012, n))
    gauge = _series(n, np.full(n, 0.1))  # never crosses τ
    active = hedge_active(gauge, tau=0.7, persist=5)
    res = apply_futures_hedge(ret, ret, active, h=1.0)
    assert res.episodes == 0
    expected = (1.0 + ret.fillna(0.0)).cumprod()
    np.testing.assert_allclose(res.equity.to_numpy(), expected.to_numpy(), rtol=0, atol=1e-12)


def test_no_look_ahead() -> None:
    """Hedged equity at date t is invariant to data appended after t."""
    n = 600
    rng = np.random.default_rng(2)
    ret = _series(n, rng.normal(0.0003, 0.013, n))
    gauge = _series(n, rng.random(n))  # noisy gauge that crosses τ often
    cut = 450
    full = apply_futures_hedge(ret, ret, hedge_active(gauge, 0.7, 5), h=1.0)
    trunc = apply_futures_hedge(
        ret.iloc[:cut], ret.iloc[:cut], hedge_active(gauge.iloc[:cut], 0.7, 5), h=1.0
    )
    np.testing.assert_allclose(
        full.equity.iloc[:cut].to_numpy(), trunc.equity.to_numpy(), rtol=0, atol=1e-12
    )


def test_hedge_cuts_a_synthetic_crash() -> None:
    """A full hedge held through a sharp drawdown ends materially higher than the unhedged book."""
    n = 400
    ret = np.concatenate([np.full(200, 0.0005), np.full(40, -0.02), np.full(160, 0.0005)])
    rser = _series(n, ret)
    # gauge fires exactly over the crash leg (lagged execution still catches most of it)
    g = np.concatenate([np.full(200, 0.1), np.full(40, 0.9), np.full(160, 0.1)])
    active = hedge_active(_series(n, g), tau=0.7, persist=3)
    hedged = apply_futures_hedge(rser, rser, active, h=1.0, apply_costs=True).equity
    unhedged = (1.0 + rser).cumprod()
    assert hedged.iloc[-1] > unhedged.iloc[-1]  # the hedge paid through the crash
