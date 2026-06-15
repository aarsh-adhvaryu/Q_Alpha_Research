"""Run the LPPLS confidence indicator over Nifty 50 history and score it against the pre-registered
reference drawdowns (lead time + false positives). Honest first-numbers pass — no tuning to outcome.

    PYTHONPATH=src python scripts/run_lppls_nifty.py [--cadence 15]

Writes the full confidence series to reports/lppls_nifty_confidence.csv and prints the scorecard.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from qalpha_research.regime.lppls import confidence_indicator

_ROOT = Path(__file__).resolve().parent.parent
_DATA = _ROOT / "data" / "nifty50_nifbees_close.csv"

# Pre-registered reference peaks (fixed before results). (label, peak month, endogenous?)
_REFERENCE = [
    ("2015-16 correction", "2015-03-01", True),
    ("2018 NBFC/IL&FS", "2018-09-01", True),
    ("2020 COVID crash", "2020-01-20", False),  # exogenous: LPPLS expected to stay quiet
    ("2021-22 correction", "2021-10-19", True),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cadence", type=int, default=15, help="evaluate confidence every N trading days")
    ap.add_argument("--min-window", type=int, default=60)
    ap.add_argument("--max-window", type=int, default=400)
    ap.add_argument("--step", type=int, default=40)
    ap.add_argument("--n-starts", type=int, default=2)
    args = ap.parse_args()

    df = pd.read_csv(_DATA, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    dates = df["date"].to_numpy()
    log_p = np.log(df["close"].to_numpy(dtype=np.float64))
    n = log_p.size

    rows = []
    start = args.max_window  # need a full longest-window of history before the first estimate
    for t2 in range(start, n, args.cadence):
        conf = confidence_indicator(
            log_p[: t2 + 1],
            min_window=args.min_window,
            max_window=args.max_window,
            step=args.step,
            n_starts=args.n_starts,
        )
        rows.append((pd.Timestamp(dates[t2]), float(df["close"].iloc[t2]), conf))

    out = pd.DataFrame(rows, columns=["date", "close", "confidence"]).set_index("date")
    rep = _ROOT / "reports"
    rep.mkdir(exist_ok=True)
    out.to_csv(rep / "lppls_nifty_confidence.csv")

    print(f"\nLPPLS confidence over Nifty 50 — {out.index[0].date()} → {out.index[-1].date()} "
          f"({len(out)} points, cadence {args.cadence}d)\n")

    # --- Scorecard vs the pre-registered reference peaks ---
    print("Reference peaks — max confidence & first crossings in the 6 months BEFORE the peak:")
    print(f"{'event':<22}{'endo?':<7}{'maxconf':>8}{'≥0.3 lead':>12}{'≥0.5 lead':>12}")
    for label, peak_s, endo in _REFERENCE:
        peak = pd.Timestamp(peak_s)
        pre = out[(out.index >= peak - pd.Timedelta(days=183)) & (out.index <= peak)]
        if pre.empty:
            print(f"{label:<22}{'Y' if endo else 'N':<7}{'(no data)':>8}")
            continue
        maxc = pre["confidence"].max()
        def lead(thr: float) -> str:
            hit = pre[pre["confidence"] >= thr]
            if hit.empty:
                return "—"
            return f"{(peak - hit.index[0]).days}d"
        print(f"{label:<22}{'Y' if endo else 'N':<7}{maxc:>8.2f}{lead(0.3):>12}{lead(0.5):>12}")

    # --- False-positive view: confidence in "calm" stretches (no reference peak within 6 months) ---
    peak_ts = [pd.Timestamp(p) for _, p, _ in _REFERENCE]
    def near_a_peak(d: pd.Timestamp) -> bool:
        return any(abs((d - p).days) <= 183 for p in peak_ts)
    calm = out[[not near_a_peak(d) for d in out.index]]
    print("\nCalm stretches (>6mo from any reference peak):")
    print(f"  points: {len(calm)} | mean conf {calm['confidence'].mean():.2f} | "
          f"% time ≥0.3: {(calm['confidence'] >= 0.3).mean()*100:.0f}% | "
          f"% time ≥0.5: {(calm['confidence'] >= 0.5).mean()*100:.0f}%")

    # --- Top elevated episodes overall (for eyeballing) ---
    print("\nMost elevated readings overall:")
    for d, r in out.sort_values("confidence", ascending=False).head(8).iterrows():
        print(f"  {d.date()}  conf={r['confidence']:.2f}  close={r['close']:.1f}")


if __name__ == "__main__":
    main()
