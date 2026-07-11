"""mission_control_app.py — the ONE screen that shows the *entire* Q-Alpha system at a glance.

Q-Alpha spans two repos on purpose (the validated product stays clean; research is separate). This is
the read-only "mission control" that composes both into a single pane — because you can't judge the
final system by looking at two repos in isolation. It lives in the *research* repo since that's the
side allowed to see both: it imports the validated ``qalpha`` engine (code seam) and reads the
product's committed ``paper_dashboard.md`` over the public repo (data seam) — never a code import of
research into the product.

    uv run --extra dashboard streamlit run scripts/mission_control_app.py

Four panes: whole-system health · product paper book (fetched status) · research hedge overlay ·
today's AI market brief. Trades nothing; the product never imports from here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from qalpha_research.regime.hedge_paper import forward_hedge_track
from qalpha_research.regime.hedge_readout import hedge_gauge_read, hedge_plain_summary
from qalpha_research.system_check import (
    BRIEF_MD,
    PANEL_CSV,
    PRODUCT_DASHBOARD_URL,
    _http_fetch,
    render,
    run_all,
)


@st.cache_data(ttl=1800)
def _fetch_product_status() -> str:
    """The product's committed paper_dashboard.md (data seam) — fail-soft to a note if unreachable."""
    try:
        return _http_fetch(PRODUCT_DASHBOARD_URL)
    except Exception as exc:
        return (
            f"_Product status feed unreachable right now ({exc}). It updates on the product cron._"
        )


def main() -> None:
    st.set_page_config(page_title="Q-Alpha — Mission Control", page_icon="🛰️", layout="wide")
    st.title("🛰️ Q-Alpha — Mission Control")
    st.caption(
        "The whole system on one screen — validated product engine, research hedge overlay, and the "
        "AI brief. Read-only; it trades nothing. (The product repo stays clean — this research-side "
        "view is the only place allowed to see both halves.)"
    )

    # 1. Whole-system health board — is every subsystem wired and working right now?
    st.subheader("🩺 Whole-system health")
    st.markdown(render(run_all(fetch=lambda _u: _fetch_product_status())))
    st.divider()

    left, right = st.columns(2)

    # 2. Product paper book — the validated core's committed status (fetched as data, not imported).
    with left:
        st.subheader("📄 Product — paper book")
        st.markdown(_fetch_product_status())

    # 3. Research hedge overlay — running forward on the validated engine.
    with right:
        st.subheader("🛡️ Research — tax-free hedge (paper)")
        if PANEL_CSV.exists():
            panel = pd.read_csv(PANEL_CSV, index_col="date", parse_dates=True)
            res = forward_hedge_track(panel)
            st.info(
                hedge_plain_summary(
                    level=res.level,
                    gauge=res.gauge_now,
                    tau=res.tau,
                    hedge_on=res.hedge_on,
                    days=res.days,
                    episodes=res.episodes,
                )
            )
            st.caption(hedge_gauge_read(res.gauge_now, res.tau, res.level, hedge_on=res.hedge_on))
        else:
            st.info("Hedge panel not built yet — run `python scripts/hedge_paper.py daily`.")

    # 4. Today's AI market brief — news, sentiment, likely reaction (context only).
    st.divider()
    st.subheader("🧠 Today's AI market brief")
    if BRIEF_MD.exists() and "No brief generated yet" not in BRIEF_MD.read_text(encoding="utf-8"):
        st.markdown(BRIEF_MD.read_text(encoding="utf-8"))
        st.caption(
            "Context only, **not a signal** — an LLM's read for your judgement, never traded on."
        )
    else:
        st.info("No brief yet — the daily cron writes it after market close.")


if __name__ == "__main__":
    main()
