"""Daily AI market brief CLI — the "macro analyst" that rides the hedge cron (Ops Layer PR-4).

**Context only, never a signal** (see :mod:`qalpha_research.ai_brief`). One web-searched Claude Haiku
call per trading day → archive to ``reports/ai_brief.md`` (committed) → push to Telegram via PR-3.

    ai_brief.py daily              # generate → write reports/ai_brief.md → send to Telegram
    ai_brief.py daily --dry-run    # generate + print only (no send, no file write)

Fail-soft, always exit 0 — a missing key / API error / empty response skips the brief and the cron
stays green.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from qalpha_research.ai_brief import generate_brief, load_watchlist_lines
from qalpha_research.notify import send_telegram

WATCHLIST_CSV = Path("data/nifty100_watchlist.csv")
BRIEF_MD = Path("reports/ai_brief.md")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_daily = sub.add_parser("daily", help="generate today's brief, archive it, send to Telegram")
    p_daily.add_argument(
        "--dry-run", action="store_true", help="print the brief without sending or writing"
    )
    args = parser.parse_args(argv)

    try:
        watchlist = load_watchlist_lines(str(WATCHLIST_CSV)) if WATCHLIST_CSV.exists() else []
        if not watchlist:
            print(f"[ai-brief] watchlist missing at {WATCHLIST_CSV} — skipping.")
            return 0
        result = generate_brief(watchlist)
    except Exception as exc:  # fail-soft: the cron must never go red on the brief
        print(f"[ai-brief] failed (non-fatal): {exc}")
        return 0

    if result is None:
        return 0  # already logged the reason

    footer = _usage_footer(result)
    print(f"[ai-brief]{footer.strip().lstrip('—').strip()}")
    if args.dry_run:
        print("\n--- brief (dry run, not sent) ---\n")
        print(result.text + footer)
        return 0

    BRIEF_MD.parent.mkdir(parents=True, exist_ok=True)
    BRIEF_MD.write_text(result.raw + footer + "\n", encoding="utf-8")
    ok = send_telegram(result.text + footer)
    print(f"[ai-brief] archived → {BRIEF_MD} · telegram: {'sent' if ok else 'NOT sent'}")
    return 0


def _usage_footer(result: object) -> str:
    """A compact token-usage line appended to the brief — so cost/completeness is visible on the
    phone and in the committed archive, without checking the Anthropic console."""
    usage = getattr(result, "usage", {}) or {}
    inp = usage.get("input", 0)
    out = usage.get("output", 0)
    model = getattr(result, "model", "?")
    note = " ⚠️ cut off (raise max_tokens)" if usage.get("truncated") else " ✓ complete"
    return f"\n\n— 🤖 {model} · {inp:,} in / {out:,} out tokens ·{note}"


if __name__ == "__main__":
    raise SystemExit(main())
