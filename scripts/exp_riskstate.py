"""exp_riskstate.py — the money test for the HMM risk-state deploy-throttle overlay.

Pre-registered in regime/PREREGISTRATION_riskstate.md. Runs:
  1. FIDELITY CHECK — the research-side runner with exposure≡1.0 vs qalpha's own run_backtest
     (must match; proves the overlay rides the exact validated engine, not a re-implementation).
  2. The overlay (deploy-throttle on filtered P(stress)) vs the always-invested baseline and 1/N,
     net of Zerodha cost + capital-gains tax, on the full window and on the 2020+ holdout.

Reuses qalpha as a dependency (loaders, engine, baselines); qalpha is never modified. Data is read
from the sibling product repo (default ../qalpha) so the validated panel/universe are identical.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path

import pandas as pd
from qalpha.backtest.baselines import equal_weight_pit
from qalpha.backtest.engine import run_backtest
from qalpha.backtest.metrics import compute_metrics
from qalpha.config import Config
from qalpha.data.ingest import load_parquet
from qalpha.data.universe import Universe

from qalpha_research.regime.overlay_backtest import (
    OverlayResult,
    run_overlay_backtest,
    threshold_exposure,
)
from qalpha_research.regime.risk_state import RiskStateConfig, fit_predict_walkforward


def _load_universe_csv(csv_path: Path) -> tuple[list[str], dict[str, str]]:
    df = pd.read_csv(csv_path)
    sector_of = {str(t): str(s) for t, s in zip(df["ticker"], df["sector"], strict=True)}
    return sorted(sector_of), sector_of


def _signal(close_csv: Path, cfg: RiskStateConfig) -> pd.Series:
    df = pd.read_csv(close_csv, parse_dates=["date"]).sort_values("date")
    res = fit_predict_walkforward(df["close"].to_numpy(dtype=float), cfg)
    return pd.Series(res.p_stress, index=pd.DatetimeIndex(df["date"]), name="p_stress")


def _metrics_row(
    label: str, equity: pd.Series, cost_tax: Decimal | None = None
) -> dict[str, object]:
    m = compute_metrics(equity, label)
    final = float(equity.iloc[-1])
    return {
        "strategy": label,
        "final_rs": round(final),
        "CAGR_%": round(m.cagr * 100, 1),
        "Sharpe": round(m.sharpe, 2),
        "maxDD_%": round(m.max_drawdown * 100, 1),
        "cost+tax_rs": int(cost_tax) if cost_tax is not None else "—",
    }


def _realised_cost_tax(result: OverlayResult) -> Decimal:
    return sum((t.cost + t.tax for t in result.trades), Decimal("0"))


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    head = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qalpha", default="../qalpha", help="path to the sibling product repo")
    ap.add_argument("--start", default="2012-01-01")
    ap.add_argument("--end", default="2026-06-12")
    ap.add_argument("--holdout-start", default="2020-01-01")
    ap.add_argument("--tau", type=float, default=0.5, help="stress threshold")
    ap.add_argument("--floor", type=float, default=0.0, help="exposure floor in stress")
    ap.add_argument("--out", default="reports/riskstate_nifty_findings.md")
    args = ap.parse_args()

    qroot = Path(args.qalpha)
    cfg = Config()
    prices = load_parquet(qroot / "data/historical/prices_pit_2026.parquet")
    universe = Universe.from_csv(str(qroot / "data/universes/nifty50_membership_2026.csv"))
    _, sector_of = _load_universe_csv(qroot / "data/universes/nifty50_membership_2026.csv")
    signal = _signal(Path("data/nifty50_nifbees_close.csv"), RiskStateConfig())

    common = {
        "start": args.start,
        "end": args.end,
        "tax_aware": True,
        "min_trade_fraction": 0.10,
        "weighting": "shrink",
        "force_refresh": True,
    }

    # 1) FIDELITY: overlay runner at exposure≡1.0 must equal qalpha.run_backtest
    print("Fidelity check: overlay(exposure≡1.0) vs qalpha.run_backtest ...")
    flat = run_overlay_backtest(
        prices,
        sector_of,
        universe,
        cfg,
        p_stress=signal,
        exposure_fn=threshold_exposure(
            tau=2.0, floor=1.0
        ),  # τ=2 ⇒ never stressed ⇒ always invested
        rebalance_freq="Y",
        **common,
    )
    ref = run_backtest(
        prices,
        sector_of,
        universe,
        cfg,
        rebalance_freq="Y",
        **common,
    )
    aligned = flat.equity.reindex(ref.equity.index)
    max_rel = float((aligned - ref.equity).abs().div(ref.equity).max())
    print(f"  max relative equity diff = {max_rel:.2e}  ->  {'PASS' if max_rel < 1e-6 else 'FAIL'}")

    # 2) THE OVERLAY — sweep (τ, floor); selection is on the 2012–2019 TRAIN window only.
    eq_index = pd.DatetimeIndex(ref.equity.index)
    one_over_n = equal_weight_pit(prices, universe, eq_index, cfg.capital.starting_capital)

    def _win(s: pd.Series, lo: str, hi: str) -> pd.Series:
        return s[(s.index >= pd.Timestamp(lo)) & (s.index < pd.Timestamp(hi))]

    windows = {
        "TRAIN 2012–2019": (args.start, args.holdout_start),
        "HOLDOUT 2020–26": (args.holdout_start, "2027-01-01"),
        "FULL 2012–26": (args.start, "2027-01-01"),
    }
    sweep = [(tau, floor) for floor in (0.0, 0.5) for tau in (0.5, 0.8)]

    def _ref_rows(win: tuple[str, str]) -> list[dict[str, object]]:
        return [
            _metrics_row("Always-invested (shrink)", _win(ref.equity, *win)),
            _metrics_row("1/N equal-weight", _win(one_over_n, *win)),
        ]

    print("\nSweeping overlay configs (each ≈ one backtest)...")
    overlays: dict[tuple[float, float], OverlayResult] = {}
    for tau, floor in sweep:
        overlays[(tau, floor)] = run_overlay_backtest(
            prices,
            sector_of,
            universe,
            cfg,
            p_stress=signal,
            exposure_fn=threshold_exposure(tau=tau, floor=floor),
            rebalance_freq="Y",
            **common,
        )

    lines: list[str] = [
        "# HMM risk-state deploy-throttle — money test (Nifty 50, net cost+tax)",
        "",
        f"_Pre-registered: regime/PREREGISTRATION_riskstate.md. Fidelity (overlay@exposure≡1.0 vs "
        f"qalpha.run_backtest): max rel equity diff **{max_rel:.1e}** → the overlay rides the exact "
        f"validated engine._",
        "",
    ]
    for name, win in windows.items():
        rows = [
            _metrics_row(
                f"Overlay τ={tau} floor={floor}",
                _win(overlays[(tau, floor)].equity, *win),
                _realised_cost_tax(overlays[(tau, floor)]) if name == "FULL 2012–26" else None,
            )
            for tau, floor in sweep
        ] + _ref_rows(win)
        df = pd.DataFrame(rows)
        print(f"\n=== {name} ===")
        print(df.to_string(index=False))
        lines += [f"## {name}", "", _md_table(df), ""]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines))
    print(f"\nfidelity max rel diff: {max_rel:.2e}  ·  wrote {args.out}")


if __name__ == "__main__":
    main()
