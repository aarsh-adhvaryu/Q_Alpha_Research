"""forward_study.py — the daily runner for the A/B/C forward study.

Runs three fake-money books forward (see ``reports/PREREGISTRATION_forward_study.md``): **A** the
validated deploy-into-weakness engine only, **B** the same but its deploy size tilted by the day's AI
signal, **C** buy-and-hold NIFTYBEES. Same cash flows into all three, so a value comparison is fair.

    python scripts/forward_study.py daily                 # inject + deploy + resolve + write (for cron)
    python scripts/forward_study.py status                # print the current standings
    python scripts/forward_study.py inject 50000 --reason "XYZ IPO"   # discretionary manual top-up (all 3 books)

The pure logic (signal tilt, tranche sizing, book accounting, decision ledger, cash-flow schedule) is
the tested ``qalpha_research.forward_study`` core; this script is the thin I/O shell — prices from
yfinance, the deploy basket from the validated ``qalpha`` engine (this repo imports qalpha; the product
never imports from here), and the committable track record. **No real money and no real orders — ever.**
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
from qalpha.backtest.portfolio import Portfolio
from qalpha.config import CostConfig, TaxConfig
from qalpha.data.prices import PriceData
from qalpha.live.deploy import advise_deploy_into_weakness, market_weakness

from qalpha_research.forward_study import (
    Book,
    Decision,
    ai_hit_rate,
    basket_value,
    book_deploy_amount,
    load_ledger,
    parse_ai_signal,
    pct_return,
    resolve_decision,
    save_ledger,
    scheduled_injection,
    signal_tilt,
)

FORWARD_START = (
    "2026-07-06"  # fixed study start (first trading session on/after this seeds the books)
)
# Fetch a long price history (NOT from FORWARD_START) so the deploy engine has the ~1-year lookback it
# needs for market-weakness + per-name cheapness; only the *books* start accruing at FORWARD_START.
PRICE_HISTORY_START = "2024-06-01"
RESOLVE_CALENDAR_DAYS = 28  # ≈20 trading days — the window each decision is scored over vs Nifty

WATCHLIST_CSV = Path("data/nifty100_watchlist.csv")
NIFBEES = "NIFTYBEES.NS"

BOOKS_JSON = Path("data/forward_study_books.json")
STATE_JSON = Path("data/forward_study_state.json")
MANUAL_LOG = Path("data/forward_study_manual_injections.json")
PRICES_PARQUET = Path("data/forward_study_prices.parquet")
BRIEF_MD = Path("reports/ai_brief.md")
TRACK_CSV = Path("data/forward_study_track.csv")
DASHBOARD_MD = Path("reports/forward_study_dashboard.md")

BOOK_NAMES = ("A", "B", "C")


# ---- watchlist + prices ---------------------------------------------------------------------------


def _load_watchlist() -> tuple[list[str], dict[str, str]]:
    """The Nifty-100 watchlist (ticker → sector) the deploy engine picks from."""
    df = pd.read_csv(WATCHLIST_CSV)
    tickers = [str(t) for t in df["ticker"].tolist()]
    sector_of = {str(r.ticker): str(r.sector) for r in df.itertuples(index=False)}
    return tickers, sector_of


def _fetch_panel(tickers: list[str], start: str) -> tuple[PriceData, pd.Series]:
    """Download adjusted closes + volume for the watchlist and NIFTYBEES from yfinance, build a
    ``PriceData``, and return it with the NIFTYBEES close series (the study's Nifty benchmark)."""
    import yfinance as yf

    universe = sorted(set(tickers) | {NIFBEES})
    raw = yf.download(universe, start=start, progress=False, auto_adjust=True)
    close = raw["Close"].copy()
    volume = raw["Volume"].copy()
    if isinstance(close, pd.Series):  # single-ticker safety
        close = close.to_frame()
        volume = volume.to_frame()
    close = close.dropna(how="all").ffill()
    volume = volume.reindex(close.index).fillna(0.0)
    prices = PriceData(adj_close=close, close_raw=close, volume=volume)
    prices.adj_close.to_parquet(PRICES_PARQUET)  # cache for reproducibility/audit
    nifbees = close[NIFBEES].dropna()
    return prices, nifbees


def _price_on(series: pd.Series, as_of: str) -> Decimal | None:
    """Last available price on/before ``as_of`` (``None`` if the series starts later)."""
    sub = series.loc[: pd.Timestamp(as_of)].dropna()
    return Decimal(str(float(sub.iloc[-1]))) if not sub.empty else None


def _last_prices(prices: PriceData, tickers: list[str], as_of: str) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for t in set(tickers) | {NIFBEES}:
        if t in prices.adj_close.columns:
            p = _price_on(prices.adj_close[t], as_of)
            if p is not None:
                out[t] = p
    return out


# ---- persisted study state ------------------------------------------------------------------------


def _load_books() -> dict[str, Book]:
    if BOOKS_JSON.exists():
        data = json.loads(BOOKS_JSON.read_text(encoding="utf-8"))
        return {n: Book.from_dict(data[n]) for n in BOOK_NAMES}
    return {n: Book(name=n) for n in BOOK_NAMES}


def _save_books(books: dict[str, Book]) -> None:
    BOOKS_JSON.parent.mkdir(parents=True, exist_ok=True)
    BOOKS_JSON.write_text(
        json.dumps({n: books[n].to_dict() for n in BOOK_NAMES}, indent=2) + "\n", encoding="utf-8"
    )


def _load_state() -> dict[str, object]:
    if STATE_JSON.exists():
        data: dict[str, object] = json.loads(STATE_JSON.read_text(encoding="utf-8"))
        return data
    return {"seeded": False, "last_deposit_month": None}


def _save_state(state: dict[str, object]) -> None:
    STATE_JSON.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _inject_all(books: dict[str, Book], amount: Decimal) -> None:
    for n in BOOK_NAMES:
        books[n].inject(amount)


# ---- deploy (via the validated qalpha engine) -----------------------------------------------------


def _portfolio_reflecting(book: Book, last_prices: dict[str, Decimal], as_of: date) -> Portfolio:
    """A qalpha ``Portfolio`` mirroring the book's held shares, so the deploy engine fills genuine
    underweights (diversifies) rather than doubling down. Cash is set high enough to admit the buys;
    the deploy budget is passed separately as ``amount`` and is independent of this cash."""
    held_value = basket_value(book.holdings, last_prices)
    p = Portfolio(CostConfig(), TaxConfig(), cash=held_value + Decimal("1"))
    for t, q in sorted(book.holdings.items()):
        px = last_prices.get(t)
        if px is not None and q > 0:
            p.buy(as_of, t, Decimal(q), px)
    return p


def _deploy(
    book: Book,
    amount: Decimal,
    watchlist: list[str],
    sector_of: dict[str, str],
    prices: PriceData,
    nifbees: pd.Series,
    as_of: date,
) -> tuple[dict[str, int], str, list[tuple[str, float]]]:
    """Run the deploy engine for ``amount`` and *execute* the recommended buys on ``book``.

    Returns ``(basket, rationale, cheapest)`` — the shares actually bought (ticker → qty), a one-line
    model rationale, and the top out-of-favour names at decision time."""
    if amount <= 0:
        return {}, "no deploy (calm/no idle wallet tranche due)", []
    port = _portfolio_reflecting(book, _last_prices(prices, watchlist, as_of.isoformat()), as_of)
    advice = advise_deploy_into_weakness(
        port, amount, watchlist, sector_of, prices, nifbees, as_of, max_names=15
    )
    basket: dict[str, int] = {}
    for order in advice.deploy.buy_orders:
        qty = int(order.quantity)
        price = Decimal(str(order.price))
        if qty > 0 and price * qty <= book.cash:
            book.buy(order.ticker, qty, price)
            basket[order.ticker] = basket.get(order.ticker, 0) + qty
    lvl = advice.weakness.level
    cheapest = advice.cheapest
    top = ", ".join(f"{t} (−{p * 100:.0f}%)" for t, p in cheapest[:3])
    rationale = f"weakness={lvl}; deployed ₹{sum((Decimal(str(o.price)) * int(o.quantity)) for o in advice.deploy.buy_orders):.0f} into: {top}"
    return basket, rationale, cheapest


def _buy_and_hold(book: Book, price: Decimal) -> None:
    """Book C: sink all idle cash into NIFTYBEES immediately (the dumb baseline)."""
    qty = int(book.cash / price)
    if qty > 0:
        book.buy(NIFBEES, qty, price)


# ---- decision resolution --------------------------------------------------------------------------


def _resolve_due(ledger: list[Decision], prices: PriceData, nifbees: pd.Series, as_of: str) -> int:
    """Score every decision whose window has closed: basket return vs Nifty over the window. Returns
    how many were resolved this run."""
    resolved = 0
    for i, d in enumerate(ledger):
        if d.resolved or d.resolve_on > as_of:
            continue
        now_prices = _last_prices(prices, list(d.basket), as_of)
        exit_val = basket_value(d.basket, now_prices)
        basket_ret = pct_return(Decimal(d.amount), exit_val)
        entry_idx = _price_on(nifbees, d.as_of)
        exit_idx = _price_on(nifbees, as_of)
        bench_ret = (
            pct_return(entry_idx, exit_idx)
            if entry_idx is not None and exit_idx is not None
            else 0.0
        )
        ledger[i] = resolve_decision(d, basket_ret, bench_ret)
        resolved += 1
    return resolved


# ---- dashboard ------------------------------------------------------------------------------------


def _standings(
    books: dict[str, Book], last_prices: dict[str, Decimal]
) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for n in BOOK_NAMES:
        b = books[n]
        out[n] = {
            "value": float(b.value(last_prices)),
            "contributed": float(b.net_contributions),
            "profit": float(b.profit(last_prices)),
            "return_pct": b.return_pct(last_prices),
        }
    return out


def _track_row(as_of: str, standings: dict[str, dict[str, float]]) -> dict[str, object]:
    row: dict[str, object] = {"date": as_of}
    for n in BOOK_NAMES:
        row[f"{n}_value"] = round(standings[n]["value"], 2)
        row[f"{n}_profit"] = round(standings[n]["profit"], 2)
        row[f"{n}_return_pct"] = round(standings[n]["return_pct"], 3)
    return row


def _append_track(row: dict[str, object]) -> pd.DataFrame:
    if TRACK_CSV.exists():
        df = pd.read_csv(TRACK_CSV)
        df = df[df["date"] != row["date"]]  # idempotent: replace today's row on a re-run
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(TRACK_CSV, index=False)
    return df


def _render_dashboard(
    as_of: str,
    standings: dict[str, dict[str, float]],
    ledger: list[Decision],
    level: str,
    signal_desc: str,
) -> str:
    worked, total = ai_hit_rate(ledger)
    n_days = 0
    if TRACK_CSV.exists():
        n_days = len(pd.read_csv(TRACK_CSV))
    lines = [
        "# Forward study — did the system make money, and did the AI help?",
        "",
        f"_As of **{as_of}** · {n_days} marks · market weakness: **{level}** · "
        "**fake money, no real orders** (see `reports/PREREGISTRATION_forward_study.md`)._",
        "",
        "| Book | What it does | Value | Contributed | Profit | Return |",
        "|---|---|---:|---:|---:|---:|",
    ]
    labels = {
        "A": "Strategy only (deploy into weakness)",
        "B": "Strategy + AI nudge",
        "C": "Buy-and-hold NIFTYBEES",
    }
    for n in BOOK_NAMES:
        s = standings[n]
        lines.append(
            f"| **{n}** | {labels[n]} | ₹{s['value']:,.0f} | ₹{s['contributed']:,.0f} | "
            f"₹{s['profit']:,.0f} | {s['return_pct']:+.2f}% |"
        )
    a_vs_c = standings["A"]["profit"] - standings["C"]["profit"]
    b_vs_a = standings["B"]["profit"] - standings["A"]["profit"]
    lines += [
        "",
        f"- **A − C** (does the strategy beat buy-and-hold?): **₹{a_vs_c:,.0f}**",
        f"- **B − A** (does the AI insight add value?): **₹{b_vs_a:,.0f}**",
        f"- **AI decision hit-rate** (Book-B deploys that beat Nifty): **{worked}/{total}**",
        f"- Today's AI signal: {signal_desc}",
        "",
        "> **Low power early — this is not a verdict.** The claims need ≥3 months and a real "
        "volatility event before they mean anything; until then these are just the accruing numbers.",
        "",
        "## Recent resolved decisions",
        "",
        "| Date | Book | Basket return | Nifty | Verdict | AI insight |",
        "|---|---|---:|---:|---|---|",
    ]
    for d in [d for d in ledger if d.resolved][-10:][::-1]:
        lines.append(
            f"| {d.as_of} | {d.book} | {d.outcome_return_pct:+.1f}% | "
            f"{d.benchmark_return_pct:+.1f}% | {d.verdict} | {d.ai_insight} |"
        )
    return "\n".join(lines) + "\n"


# ---- commands -------------------------------------------------------------------------------------


def _as_of_today(nifbees: pd.Series) -> str:
    """The mark date = the latest session we have a NIFTYBEES price for (never the future)."""
    return str(nifbees.index[-1].date())


def cmd_daily() -> int:
    watchlist, sector_of = _load_watchlist()
    prices, nifbees = _fetch_panel(watchlist, start=PRICE_HISTORY_START)
    if nifbees.empty:
        print("[forward-study] no NIFTYBEES prices yet — nothing to mark.")
        return 0
    as_of_str = _as_of_today(nifbees)
    if as_of_str < FORWARD_START:
        print(f"[forward-study] latest session {as_of_str} precedes the study start — waiting.")
        return 0
    as_of = date.fromisoformat(as_of_str)

    books = _load_books()
    ledger = load_ledger()
    state = _load_state()

    amount, new_month = scheduled_injection(
        as_of_str,
        seeded=bool(state.get("seeded")),
        last_deposit_month=state.get("last_deposit_month"),  # type: ignore[arg-type]
    )
    if amount > 0:
        _inject_all(books, amount)
        print(f"[forward-study] scheduled injection ₹{amount:,.0f} into all three books.")
    state["seeded"] = True
    state["last_deposit_month"] = new_month

    level = market_weakness(nifbees, as_of).level
    signal = (
        parse_ai_signal(BRIEF_MD.read_text(encoding="utf-8"), as_of_str)
        if BRIEF_MD.exists()
        else None
    )
    tilt = signal_tilt(signal)
    signal_desc = (
        f"lean={signal.lean} confidence={signal.confidence} (tilt {tilt:.2f}×)"
        if signal is not None
        else "none (neutral 1.00× tilt)"
    )
    resolve_on = (as_of + timedelta(days=RESOLVE_CALENDAR_DAYS)).isoformat()

    # Book A — strategy only.
    amt_a = book_deploy_amount(books["A"].cash, level, None, ai=False)
    basket_a, rat_a, _ = _deploy(books["A"], amt_a, watchlist, sector_of, prices, nifbees, as_of)
    if basket_a:
        ledger.append(
            Decision(as_of_str, "A", str(amt_a), basket_a, rat_a, "n/a (no AI)", resolve_on)
        )
    # Book B — strategy + AI nudge.
    amt_b = book_deploy_amount(books["B"].cash, level, signal, ai=True)
    basket_b, rat_b, _ = _deploy(books["B"], amt_b, watchlist, sector_of, prices, nifbees, as_of)
    if basket_b:
        ledger.append(
            Decision(as_of_str, "B", str(amt_b), basket_b, rat_b, signal_desc, resolve_on)
        )
    # Book C — buy-and-hold NIFTYBEES.
    nif_px = _price_on(nifbees, as_of_str)
    if nif_px is not None:
        _buy_and_hold(books["C"], nif_px)

    n_resolved = _resolve_due(ledger, prices, nifbees, as_of_str)
    if n_resolved:
        print(f"[forward-study] resolved {n_resolved} decision(s).")

    last_prices = _last_prices(prices, watchlist, as_of_str)
    standings = _standings(books, last_prices)
    _append_track(_track_row(as_of_str, standings))
    DASHBOARD_MD.write_text(
        _render_dashboard(as_of_str, standings, ledger, level, signal_desc), encoding="utf-8"
    )
    _save_books(books)
    save_ledger(ledger)
    _save_state(state)
    print(
        f"[forward-study] marked {as_of_str}: "
        + " · ".join(
            f"{n} ₹{standings[n]['value']:,.0f} ({standings[n]['return_pct']:+.2f}%)"
            for n in BOOK_NAMES
        )
    )
    return 0


def cmd_status() -> int:
    if not TRACK_CSV.exists():
        print("[forward-study] no track record yet — run `daily` first.")
        return 0
    df = pd.read_csv(TRACK_CSV)
    print(df.tail(10).to_string(index=False))
    return 0


def cmd_inject(amount: Decimal, reason: str) -> int:
    """A discretionary manual top-up — deposits the SAME amount into all three books (so it cannot
    bias the relative A/B/C verdict) and logs the user's stated reason for honesty. It is deployed on
    the next `daily` run."""
    books = _load_books()
    _inject_all(books, amount)
    _save_books(books)
    log = json.loads(MANUAL_LOG.read_text(encoding="utf-8")) if MANUAL_LOG.exists() else []
    log.append(
        {
            "at": datetime.now().isoformat(timespec="seconds"),
            "amount": str(amount),
            "reason": reason,
        }
    )
    MANUAL_LOG.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    print(
        f"[forward-study] manually injected ₹{amount:,.0f} into all three books — reason: {reason}"
    )
    print(
        "             (deploys on the next `daily` run; logged, applied equally so the verdict stays fair.)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("daily", help="inject (scheduled) + deploy the three books + resolve + write")
    sub.add_parser("status", help="print the recent track record")
    p_inj = sub.add_parser("inject", help="discretionary manual top-up into all three books")
    p_inj.add_argument("amount", type=Decimal)
    p_inj.add_argument(
        "--reason", default="(unspecified)", help="why (an IPO, a tip, a news catalyst)"
    )
    args = parser.parse_args(argv)

    if args.cmd == "daily":
        return cmd_daily()
    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "inject":
        return cmd_inject(args.amount, args.reason)
    return 1


if __name__ == "__main__":
    sys.exit(main())
