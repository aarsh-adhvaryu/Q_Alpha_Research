"""Whole-system integration check — the one place that verifies the *entire* Q-Alpha system works
together, across both repos, without violating the "product never imports research" boundary.

Why this lives here: the product repo (``qalpha``) is the validated, real-money, resume-clean core —
it must have **no** code dependency on experimental research. But the research repo is *allowed* to
see both (it imports the validated ``qalpha`` engine as a dependency), so this is the natural — and
only correct — home for a whole-system view. The system integrates along two seams, and this module
checks both:

* **code seam** — the research overlays (hedge, …) run *on* the validated ``qalpha`` engine.
* **data seam** — the product's committed status artifact (``reports/paper_dashboard.md``) is
  consumed as *data*, never as a code import (the sanctioned integration path).

Each subsystem returns a :class:`SubsystemStatus`; :func:`run_all` collects them and :func:`render`
draws the health board. Pure/injectable (the network fetch and Telegram-config probe are seams) so it
unit-tests with no network. This is the automated "does the whole pipeline still hang together?" check
to run before the real-money GO — the answer to "we can't test just two repos in isolation".
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# Injectable seams: fetch a URL→text (network), and probe whether Telegram is configured (env).
Fetcher = Callable[[str], str]
ConfigProbe = Callable[[], bool]

PANEL_CSV = Path("data/fragility_panel.csv")
BRIEF_MD = Path("reports/ai_brief.md")
PRODUCT_DASHBOARD_URL = (
    "https://raw.githubusercontent.com/aarsh-adhvaryu/Q_Alpha/main/reports/paper_dashboard.md"
)


@dataclass(frozen=True)
class SubsystemStatus:
    """Health of one subsystem. ``critical`` ones must be green for the whole system to be healthy;
    non-critical ones (Telegram config, the network artifact fetch) are informational."""

    name: str
    ok: bool
    detail: str
    critical: bool = True

    @property
    def icon(self) -> str:
        return "🟢" if self.ok else ("🔴" if self.critical else "🟡")


def check_engine() -> SubsystemStatus:
    """The validated product engine is importable and computing (the accounting core runs)."""
    name = "Validated engine (qalpha)"
    try:
        from decimal import Decimal

        from qalpha.accounting.costs import compute_costs
        from qalpha.backtest.portfolio import Side
        from qalpha.config import CostConfig

        cost = compute_costs(Side.BUY, Decimal("10"), Decimal("100"), CostConfig())
        ok = cost.total > 0
        return SubsystemStatus(name, ok, f"accounting engine live — sample buy cost ₹{cost.total}")
    except Exception as exc:
        return SubsystemStatus(name, False, f"import/compute failed: {exc}")


def check_hedge_overlay(panel_path: Path = PANEL_CSV) -> SubsystemStatus:
    """The research hedge overlay runs FORWARD on the validated engine — the code integration seam."""
    name = "Hedge overlay (research → engine)"
    try:
        if not panel_path.exists():
            return SubsystemStatus(name, False, f"fragility panel missing at {panel_path}")
        import pandas as pd

        from qalpha_research.regime.hedge_paper import forward_hedge_track

        panel = pd.read_csv(panel_path, index_col="date", parse_dates=True)
        res = forward_hedge_track(panel)
        return SubsystemStatus(
            name, True, f"runs on the engine — gauge {res.gauge_now:.2f}, {res.days} forward days"
        )
    except Exception as exc:
        return SubsystemStatus(name, False, f"failed: {exc}")


def check_ai_brief() -> SubsystemStatus:
    """The AI-brief pipeline builds a prompt + formats a brief (contract holds, no network)."""
    name = "AI market brief"
    try:
        from qalpha_research.ai_brief import CONTEXT_PREAMBLE, generate_brief

        res = generate_brief(
            ["RELIANCE:ENERGY"],
            generate=lambda _m, _p: ("Sentiment 🟢.", {"input": 1, "output": 1}),
        )
        ok = res is not None and res.text.startswith(CONTEXT_PREAMBLE)
        return SubsystemStatus(name, ok, "prompt + format contract holds (context-only preamble)")
    except Exception as exc:
        return SubsystemStatus(name, False, f"failed: {exc}")


def check_telegram(configured: ConfigProbe | None = None) -> SubsystemStatus:
    """The Telegram spine is wired (env present). Informational — absence isn't a system failure."""
    name = "Telegram alerts"
    try:
        from qalpha_research.notify import telegram_configured

        is_conf = (configured or telegram_configured)()
        detail = (
            "configured" if is_conf else "not configured (TELEGRAM_* unset) — alerts would no-op"
        )
        return SubsystemStatus(name, is_conf, detail, critical=False)
    except Exception as exc:
        return SubsystemStatus(name, False, f"failed: {exc}", critical=False)


def check_product_artifact(
    url: str = PRODUCT_DASHBOARD_URL, *, fetch: Fetcher | None = None
) -> SubsystemStatus:
    """The product's committed status artifact is reachable — the DATA integration seam (not code)."""
    name = "Product status feed (committed data)"
    try:
        text = (fetch or _http_fetch)(url)
        ok = bool(text.strip())
        detail = f"paper_dashboard.md reachable ({len(text):,} chars)" if ok else "empty artifact"
        return SubsystemStatus(name, ok, detail, critical=False)
    except Exception as exc:
        return SubsystemStatus(name, False, f"unreachable: {exc}", critical=False)


def _http_fetch(url: str) -> str:
    import urllib.request

    with urllib.request.urlopen(url, timeout=10) as resp:
        return str(resp.read().decode("utf-8"))


def run_all(
    *, fetch: Fetcher | None = None, configured: ConfigProbe | None = None
) -> list[SubsystemStatus]:
    """Run every subsystem check and return the statuses (critical first, then informational)."""
    return [
        check_engine(),
        check_hedge_overlay(),
        check_ai_brief(),
        check_telegram(configured),
        check_product_artifact(fetch=fetch),
    ]


def all_healthy(statuses: list[SubsystemStatus]) -> bool:
    """True iff every *critical* subsystem is green (informational ones don't gate)."""
    return all(s.ok for s in statuses if s.critical)


def render(statuses: list[SubsystemStatus]) -> str:
    """The whole-system health board as markdown."""
    head = (
        "🟢 **Whole system: all core subsystems healthy**"
        if all_healthy(statuses)
        else "🔴 **Whole system: a core subsystem needs attention**"
    )
    lines = [head, ""]
    lines += [f"{s.icon} **{s.name}** — {s.detail}" for s in statuses]
    return "\n".join(lines)
