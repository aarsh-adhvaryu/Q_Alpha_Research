# Deploy the hedge forward-paper dashboard (Streamlit Community Cloud)

The research hedge forward paper run (`scripts/hedge_dashboard_app.py`) deploys the same no-server way
as the product dashboard: straight from this public GitHub repo, free, with a `…streamlit.app` URL.

## One-time setup

1. Push this repo to GitHub (it already resolves the `qalpha` engine via `[tool.uv.sources]`).
2. Go to <https://share.streamlit.io> → **New app** → pick this repo / branch.
3. **Main file path:** `scripts/hedge_dashboard_app.py`
4. Deploy. Streamlit Cloud installs from the root `requirements.txt` (`-e .` + streamlit + yfinance).

That's it — no server, no SSH, no Docker.

## How it stays fresh

The **`Hedge paper daily` GitHub Action** (`.github/workflows/hedge_paper.yml`, weekdays 12:31 UTC)
refreshes the cross-asset panel from yfinance, recomputes the forward hedged-vs-unhedged curves, and
commits `data/hedge_paper_track.csv` + `reports/hedge_paper_dashboard.md`. Streamlit Cloud
auto-redeploys on every push, so the dashboard tracks the daily mark. The app also re-pulls the panel
itself (cached 1h) if the committed copy is stale.

## What it shows (and what it is not)

- The live systemic-stress gauge, the hedge ON/OFF state, and the forward paper hedged-vs-unhedged
  equity curves (indexed to 1.0 at the forward start).
- **No real derivatives are traded** — it tracks what the hedge *would* do (modelled F&O cost + tax).
- **Research only.** The product never imports from this repo; this is a separate, parallel forward
  run whose GO legitimately waits on a real stress event (the gauge is coincident).
