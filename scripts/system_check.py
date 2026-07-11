"""Whole-system integration check (CLI) — run the entire Q-Alpha pipeline's contracts end-to-end.

    python scripts/system_check.py            # print the health board; exit 0 if all core green
    python scripts/system_check.py --offline  # skip the network product-artifact fetch

This is the "we can't validate two repos in isolation" answer: one command that verifies the validated
engine runs, the research overlay runs *on* it (code seam), the AI brief pipeline holds, Telegram is
wired, and the product's committed status feed is reachable (data seam). Exit 0 iff every *critical*
subsystem is green — run it before the real-money GO.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from qalpha_research.system_check import (
    all_healthy,
    check_ai_brief,
    check_engine,
    check_hedge_overlay,
    check_telegram,
    render,
    run_all,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline", action="store_true", help="skip the network product-artifact fetch"
    )
    args = parser.parse_args(argv)

    if args.offline:
        statuses = [check_engine(), check_hedge_overlay(), check_ai_brief(), check_telegram()]
    else:
        statuses = run_all()

    print(render(statuses))
    return 0 if all_healthy(statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
