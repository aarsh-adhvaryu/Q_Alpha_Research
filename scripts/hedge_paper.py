"""hedge_paper.py — daily forward paper run of the tax-free futures hedge (research criterion-6).

Runs the validated gauge → hedge machinery FORWARD on a passive Nifty book, accumulating a live paper
track record (no real derivatives traded). The cron entry point is ``daily``: refresh the cross-asset
panel from yfinance, recompute the forward hedged-vs-unhedged curves from the fixed forward start, and
write the committable track record + dashboard report.

    python scripts/hedge_paper.py daily     # refresh panel + recompute + write CSV/MD (for cron)
    python scripts/hedge_paper.py status     # print the current gauge + hedge state

Stateless: the panel is the state (see regime/hedge_paper.py), so a daily recompute can't drift.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pandas as pd
from build_fragility_dataset import SERIES, fetch_series

from qalpha_research.notify import Transport, send_telegram
from qalpha_research.regime.hedge_paper import (
    BACKTEST_CONTEXT,
    HedgePaperResult,
    forward_hedge_track,
    track_record_csv,
)

PANEL_CSV = Path("data/fragility_panel.csv")
TRACK_CSV = Path("data/hedge_paper_track.csv")
DASHBOARD_MD = Path("reports/hedge_paper_dashboard.md")
HEDGE_ALERT_STATE = Path("data/hedge_alert_state.json")


def _should_alert(prev: bool | None, curr: bool) -> bool:
    """Alert only on a genuine hedge-state *transition*; the first-ever observation is a silent
    baseline (like the product's GO-flip rule) so a fresh checkout doesn't fire a spurious ping."""
    return prev is not None and prev != curr


def hedge_alert_message(*, hedge_on: bool, gauge_now: float, tau: float) -> str:
    """The Telegram body for a hedge-state flip — informational only, the user decides (never trades)."""
    if hedge_on:
        return (
            f"🛡 <b>Fragility gauge {gauge_now:.2f} ≥ τ {tau:.2g} → hedge overlay ON (paper).</b>\n"
            "Consider the tax-free short-futures hedge — informational, you decide."
        )
    return (
        f"🛡 <b>Fragility gauge {gauge_now:.2f} &lt; τ {tau:.2g} → hedge overlay OFF (paper).</b>\n"
        "The systemic-stress signal has eased — informational only."
    )


def _load_hedge_state(path: Path = HEDGE_ALERT_STATE) -> bool | None:
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    v = d.get("hedge_on")
    return None if v is None else bool(v)


def _save_hedge_state(hedge_on: bool, path: Path = HEDGE_ALERT_STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"hedge_on": hedge_on}) + "\n", encoding="utf-8")


def maybe_send_hedge_alert(
    res: HedgePaperResult,
    *,
    state_path: Path = HEDGE_ALERT_STATE,
    transport: Transport | None = None,
) -> bool:
    """On a hedge-state flip (both directions) send one Telegram alert, then persist the new state.

    Fail-soft: ``send_telegram`` never raises, so the cron stays green. Returns whether an alert was
    actually sent.
    """
    prev = _load_hedge_state(state_path)
    sent = False
    if _should_alert(prev, res.hedge_on):
        sent = send_telegram(
            hedge_alert_message(hedge_on=res.hedge_on, gauge_now=res.gauge_now, tau=res.tau),
            transport=transport,
        )
        print(f"[hedge-alert] transition {prev} → {res.hedge_on}: {'sent' if sent else 'NOT sent'}")
    else:
        print(f"[hedge-alert] no transition (state {prev} → {res.hedge_on}) — silent.")
    _save_hedge_state(res.hedge_on, state_path)
    return sent


def _refresh_panel(start: str = "1996-01-01") -> pd.DataFrame:
    """Re-pull every cross-asset series from yfinance and rebuild the committed panel (like build_*)."""
    cols: dict[str, pd.Series] = {}
    for ticker, name in SERIES.items():
        s = fetch_series(ticker, start)
        if s is not None:
            cols[name] = s
    panel = pd.DataFrame(cols).sort_index()
    panel.index.name = "date"
    panel = panel.asfreq("B").ffill()  # causal: a foreign holiday carries its last level
    PANEL_CSV.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(PANEL_CSV)
    return panel


def _load_panel() -> pd.DataFrame:
    return pd.read_csv(PANEL_CSV, index_col="date", parse_dates=True)


def _render_markdown(res: HedgePaperResult) -> str:
    badge = {"elevated": "🔴", "watch": "🟠", "calm": "🟢"}[res.level]
    hedge_state = "🛡️ HEDGE ON" if res.hedge_on else "— hedge off"
    diff = (res.hedged_return - res.unhedged_return) * 100
    lines = [
        "# Q-Alpha Research — Tax-Free Hedge (forward paper run)",
        "",
        f"_Forward paper overlay of the Sprint-2 gauge-triggered short-futures hedge on a passive "
        f"{res.base.upper()} book — **no real derivatives traded**. Validated config: τ={res.tau}, "
        f"persist={res.persist}, h={res.h}. As of **{res.as_of}** (started {res.forward_start})._",
        "",
        "## Gauge & hedge state now",
        "",
        "| | |",
        "|---|---|",
        f"| Systemic-stress gauge | {badge} **{res.gauge_now:.2f}** ({res.level}) |",
        f"| Hedge state | **{hedge_state}** |",
        f"| Forward paper days | {res.days} |",
        f"| Hedge episodes so far | {res.episodes} |",
        "",
        "## Forward paper performance (indexed to 1.0 at start)",
        "",
        "| Book | Return | Final |",
        "|---|---|---|",
        f"| Unhedged {res.base.upper()} | {res.unhedged_return:+.2%} | {res.unhedged.iloc[-1]:.4f} |"
        if res.days
        else "| Unhedged | — | — |",
        f"| Hedged (paper) | {res.hedged_return:+.2%} | {res.hedged.iloc[-1]:.4f} |"
        if res.days
        else "| Hedged | — | — |",
        "",
        f"Hedge effect to date: **{diff:+.2f} pts** "
        f"(F&O cost {res.cost * 100:.2f}% + tax {res.tax * 100:.2f}% of book, both modelled).",
        "",
        "## Validated backtest evidence (what this forward run re-tests)",
        "",
        f"_{BACKTEST_CONTEXT['window']}._",
        "",
        f"- **Full book:** {BACKTEST_CONTEXT['full_book']}",
        f"- **COVID 2020:** {BACKTEST_CONTEXT['covid_2020']}",
        f"- **Index 2008 + COVID:** {BACKTEST_CONTEXT['index_2008_covid']}",
        f"- **Robustness:** {BACKTEST_CONTEXT['robustness']}",
        "",
        "## Honest read",
        "",
        "- The gauge is **coincident** and severe crashes are rare → a calm window keeps the hedge "
        "OFF and the two curves identical. That is *expected_*; the hedge only earns its keep through a "
        "real stress event, which can't be scheduled. Absence of an event is **not disproof**.",
        "- This is **research, forward in real time** — if it holds through a live event over months it "
        "is ready to integrate alongside the product's GO. It trades nothing; the product never imports "
        "from here.",
        "",
        "---",
        "_Regenerated daily by the cron (`scripts/hedge_paper.py daily`); not by hand._",
    ]
    return "\n".join(lines) + "\n"


def _print_status(res: HedgePaperResult) -> None:
    print(f"\n=== Forward hedge paper run (as of {res.as_of}) ===")
    print(f"gauge        : {res.gauge_now:.2f} ({res.level})")
    print(f"hedge state  : {'ON' if res.hedge_on else 'off'}")
    print(f"forward days : {res.days}  ·  episodes {res.episodes}")
    if res.days:
        print(f"hedged       : {res.hedged_return:+.2%}   unhedged: {res.unhedged_return:+.2%}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "daily", help="refresh the panel + recompute + write the track record (for cron)"
    )
    sub.add_parser("status", help="print the current gauge + hedge state")
    sub.add_parser(
        "dashboard", help="recompute from the committed panel + write the report (no fetch)"
    )
    sub.add_parser("test-alert", help="send a test Telegram alert and exit")
    p_fail = sub.add_parser("pipeline-failed", help="send a pipeline-failure alert (failure step)")
    p_fail.add_argument("message", help="failure detail (e.g. the run URL)")
    args = parser.parse_args(argv)

    # These two never touch the panel (the failure step may run in a broken environment).
    if args.cmd == "test-alert":
        ok = send_telegram("🛡 <b>Q-Alpha Research test alert</b> — hedge-flip alerts are wired.")
        print(f"[hedge-alert] test: {'sent' if ok else 'NOT sent'}")
        return 0
    if args.cmd == "pipeline-failed":
        ok = send_telegram(f"🚨 <b>Hedge paper pipeline failed</b>\n{args.message}")
        print(f"[hedge-alert] pipeline-failed: {'sent' if ok else 'NOT sent'}")
        return 0

    panel = _refresh_panel() if args.cmd == "daily" else _load_panel()
    res = forward_hedge_track(panel)

    if args.cmd == "status":
        _print_status(res)
        return 0

    TRACK_CSV.parent.mkdir(parents=True, exist_ok=True)
    TRACK_CSV.write_text(track_record_csv(res))
    DASHBOARD_MD.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_MD.write_text(_render_markdown(res))
    print(f"✓ Track → {TRACK_CSV} · dashboard → {DASHBOARD_MD} (as of {res.as_of})")
    # The cron path emits a Telegram alert on a hedge-state flip (both directions), then persists it.
    if args.cmd == "daily":
        maybe_send_hedge_alert(res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
