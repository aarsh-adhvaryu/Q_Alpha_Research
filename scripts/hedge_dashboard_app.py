"""hedge_dashboard_app.py — the research hedge forward paper run, as a Streamlit dashboard.

A read-only window onto the tax-free futures hedge running forward in real time (regime/hedge_paper.py):
the live systemic-stress gauge, the hedge ON/OFF state, and the forward hedged-vs-unhedged paper curves.
Deploys to Streamlit Community Cloud straight from this repo (see deploy note + requirements.txt).

    uv run --extra dashboard streamlit run scripts/hedge_dashboard_app.py

It trades nothing and imports nothing from the product — it only watches the research overlay accrue.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from qalpha_research.regime.hedge_paper import (
    BACKTEST_CONTEXT,
    HedgePaperResult,
    forward_hedge_track,
)
from qalpha_research.regime.hedge_readout import (
    hedge_gauge_read,
    hedge_glossary,
    hedge_plain_summary,
)

PANEL_CSV = Path("data/fragility_panel.csv")
BRIEF_MD = Path("reports/ai_brief.md")


def _ai_brief_section() -> None:
    """Surface the daily AI market brief (committed by the cron) on the dashboard, if present."""
    if not BRIEF_MD.exists():
        return
    text = BRIEF_MD.read_text(encoding="utf-8").strip()
    if not text or "No brief generated yet" in text:
        return
    with st.expander(
        "🧠 Today's AI market brief — news, sentiment & the likely reaction", expanded=True
    ):
        st.markdown(text)
        st.caption(
            "Context only, **not a signal** — an LLM's read of today's news for your judgement "
            "(satellite sleeve), never a forecast the system trades on."
        )


@st.cache_data(ttl=3600)
def _load() -> HedgePaperResult:
    panel = pd.read_csv(PANEL_CSV, index_col="date", parse_dates=True)
    return forward_hedge_track(panel)


def main() -> None:
    st.set_page_config(page_title="Q-Alpha Hedge (research)", page_icon="🛡️", layout="wide")
    st.title("🛡️ Tax-Free Hedge — forward paper run (research)")
    if not PANEL_CSV.exists():
        st.error(
            f"No fragility panel at {PANEL_CSV}. Run `python scripts/hedge_paper.py daily` first."
        )
        return
    res = _load()

    # Plain-English summary + today's AI news brief first — everyday words before the technical panels.
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
    _ai_brief_section()

    badge = {"elevated": "🔴", "watch": "🟠", "calm": "🟢"}[res.level]
    st.caption(
        f"Gauge-triggered short-futures hedge on a passive {res.base.upper()} book, run forward from "
        f"{res.forward_start} — **no real derivatives traded**. Validated config τ={res.tau}, "
        f"persist={res.persist}, h={res.h}. As of {res.as_of}."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Systemic-stress gauge", f"{res.gauge_now:.2f}", res.level)
    c2.metric("Hedge state", "🛡️ ON" if res.hedge_on else "off")
    c3.metric("Forward paper days", res.days)
    c4.metric("Hedge episodes", res.episodes)
    st.caption(hedge_gauge_read(res.gauge_now, res.tau, res.level, hedge_on=res.hedge_on))

    st.subheader(f"{badge} Hedge {'ENGAGED' if res.hedge_on else 'standing by'}")

    # The systemic-stress gauge over ~2 years of real cross-asset data — informative every day, even
    # while the forward paper curve is flat (calm market → hedge off).
    if len(res.gauge_history) > 1:
        st.markdown("**Systemic-stress gauge — last ~2 years** (hedge fires above the τ line)")
        gh = res.gauge_history.rename("gauge").to_frame()
        gh["τ (fire threshold)"] = res.tau
        st.line_chart(gh)

    if res.days:
        chart = pd.DataFrame(
            {"Unhedged": res.unhedged, "Hedged (paper)": res.hedged.reindex(res.unhedged.index)}
        )
        st.line_chart(chart)
        d1, d2, d3 = st.columns(3)
        d1.metric("Unhedged return", f"{res.unhedged_return:+.2%}")
        d2.metric("Hedged return", f"{res.hedged_return:+.2%}")
        d3.metric("Hedge effect", f"{(res.hedged_return - res.unhedged_return) * 100:+.2f} pts")

    with st.expander(
        "📊 Validated backtest evidence (what this forward run is re-testing)", expanded=True
    ):
        st.caption(f"Window: {BACKTEST_CONTEXT['window']}")
        b1, b2 = st.columns(2)
        b1.markdown(f"**Full book** — {BACKTEST_CONTEXT['full_book']}")
        b1.markdown(f"**COVID 2020** — {BACKTEST_CONTEXT['covid_2020']}")
        b2.markdown(f"**Index 2008 + COVID** — {BACKTEST_CONTEXT['index_2008_covid']}")
        b2.markdown(f"**Robustness** — {BACKTEST_CONTEXT['robustness']}")

    st.info(
        "The gauge is **coincident** and severe crashes are rare → a calm window keeps the hedge OFF "
        "and the curves identical. That is expected: the hedge only proves itself through a real stress "
        "event, which can't be scheduled. If it holds through a live event over months, it is ready to "
        "integrate alongside the product's GO. Research only — the product never imports from here."
    )

    with st.expander("📖 Jargon, in plain English — look anything up"):
        st.markdown(hedge_glossary())


if __name__ == "__main__":
    main()
