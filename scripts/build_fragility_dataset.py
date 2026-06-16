"""build_fragility_dataset.py — assemble the cross-asset panel for the systemic-fragility gauge.

Pre-registered in regime/PREREGISTRATION_systemic.md (Sprint 2, P1). Fetches a cause-agnostic
cross-asset panel from yfinance (free, deep history, reliable in this environment) and writes a
committed `data/fragility_panel.csv` so the gauge + validation are reproducible without re-fetching.

Each series is a raw daily level; the gauge (`regime/fragility.py`) derives *causal* stress features
from them. Series have different start dates (e.g. India VIX only from 2008); that is expected — the
composite uses whatever factors exist on each date (a factor with no history yet simply abstains).

Honest scope (P1): valuation stretch is proxied by *price extension* (no fundamentals here), credit
stress by the HYG/LQD high-yield-vs-investment-grade ratio (2007+). True index P/E (niftyindices) and
FII flows (NSDL) are documented later enhancements, not blockers for "does the gauge light up at the
right times".
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

# ticker -> column name. Grouped by the three pre-registered layers.
SERIES: dict[str, str] = {
    # --- global fragility (where the dry tinder is) ---
    "^GSPC": "sp500",  # global equity
    "^IXIC": "nasdaq",  # global tech (AI-bubble extension proxy)
    "^VIX": "us_vix",  # US equity vol
    "^MOVE": "move",  # US bond vol (2002+)
    "HYG": "hyg",  # high-yield credit ETF (2007+)  ─┐ HYG/LQD = credit-stress proxy
    "LQD": "lqd",  # investment-grade credit ETF (2002+) ─┘
    # --- transmission to India (the contagion pipes) ---
    "DX-Y.NYB": "dxy",  # dollar (EM funding stress)
    "^TNX": "us10y",  # US 10y yield
    "CL=F": "crude",  # crude (India import / CAD stress)
    "INR=X": "usdinr",  # USD-INR (2003+)
    # --- domestic (India) state ---
    "^BSESN": "sensex",  # India equity, long history (1997+)
    "^NSEI": "nifty",  # India equity (2007+), pairs with India VIX
    "^INDIAVIX": "india_vix",  # India equity vol (2008+)
}


def fetch_series(ticker: str, start: str) -> pd.Series | None:
    import yfinance as yf

    df = yf.download(ticker, start=start, progress=False, auto_adjust=True)
    if df is None or len(df) == 0:
        return None
    close = df["Close"]
    if isinstance(close, pd.DataFrame):  # yfinance sometimes returns a 1-col frame
        close = close.iloc[:, 0]
    return pd.Series(close.to_numpy(), index=pd.DatetimeIndex(df.index), name=ticker)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="1996-01-01")
    ap.add_argument("--out", default="data/fragility_panel.csv")
    args = ap.parse_args()

    cols: dict[str, pd.Series] = {}
    for ticker, name in SERIES.items():
        s = fetch_series(ticker, args.start)
        if s is None:
            print(f"  ! {name:10} ({ticker}) — no data, skipped")
            continue
        cols[name] = s
        print(
            f"  ✓ {name:10} ({ticker:9}) rows={len(s):5} {s.index[0].date()} → {s.index[-1].date()}"
        )

    panel = pd.DataFrame(cols).sort_index()
    panel.index.name = "date"
    # business-day grid + causal forward-fill (so a market closed on a foreign holiday carries its
    # last level; no future data used). Leading NaNs (before a series starts) are preserved.
    panel = panel.asfreq("B").ffill()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out)
    print(f"\nwrote {out}  shape={panel.shape}  {panel.index[0].date()} → {panel.index[-1].date()}")


if __name__ == "__main__":
    main()
