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
from qalpha_research.regime.hedge_paper import HedgePaperResult, forward_hedge_track

PANEL_CSV = Path("data/fragility_panel.csv")


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

    st.subheader(f"{badge} Hedge {'ENGAGED' if res.hedge_on else 'standing by'}")

    if res.days:
        chart = pd.DataFrame(
            {"Unhedged": res.unhedged, "Hedged (paper)": res.hedged.reindex(res.unhedged.index)}
        )
        st.line_chart(chart)
        d1, d2, d3 = st.columns(3)
        d1.metric("Unhedged return", f"{res.unhedged_return:+.2%}")
        d2.metric("Hedged return", f"{res.hedged_return:+.2%}")
        d3.metric("Hedge effect", f"{(res.hedged_return - res.unhedged_return) * 100:+.2f} pts")

    st.info(
        "The gauge is **coincident** and severe crashes are rare → a calm window keeps the hedge OFF "
        "and the curves identical. That is expected: the hedge only proves itself through a real stress "
        "event, which can't be scheduled. If it holds through a live event over months, it is ready to "
        "integrate alongside the product's GO. Research only — the product never imports from here."
    )


if __name__ == "__main__":
    main()
