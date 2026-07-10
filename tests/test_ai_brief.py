"""Tests for the daily AI market brief — pure prompt/format logic + fail-soft generation (PR-4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qalpha_research.ai_brief import (
    CONTEXT_PREAMBLE,
    build_prompt,
    format_for_telegram,
    generate_brief,
)


def test_build_prompt_includes_watchlist_and_context_preamble() -> None:
    prompt = build_prompt(["RELIANCE:ENERGY", "ITC:FMCG", "NTPC:POWER"])
    assert CONTEXT_PREAMBLE in prompt  # the disclaimer is baked into the instruction
    assert "RELIANCE:ENERGY" in prompt and "NTPC:POWER" in prompt
    assert "template only" in prompt.lower()
    assert "satellite sleeve" in prompt.lower()  # discretionary ideas are sleeve-framed


def test_format_prepends_preamble_when_missing() -> None:
    out = format_for_telegram("Markets rose today on strong earnings.")
    assert out.startswith(CONTEXT_PREAMBLE)


def test_format_keeps_existing_preamble_once() -> None:
    text = f"{CONTEXT_PREAMBLE}\n\nSentiment 🟢 — calm."
    out = format_for_telegram(text)
    assert out.count(CONTEXT_PREAMBLE) == 1


def test_format_truncates_over_limit_on_word_boundary() -> None:
    long = CONTEXT_PREAMBLE + "\n\n" + ("word " * 2000)
    out = format_for_telegram(long, limit=200)
    assert len(out) <= 200
    assert out.endswith("…")


def test_generate_brief_with_canned_client() -> None:
    def fake(model: str, prompt: str) -> tuple[str, dict[str, int]]:
        assert "RELIANCE:ENERGY" in prompt
        return "Sentiment 🟢 — steady.", {"input": 700, "output": 120, "total": 820}

    res = generate_brief(["RELIANCE:ENERGY"], generate=fake, model="gemini-2.5-flash")
    assert res is not None
    assert res.text.startswith(CONTEXT_PREAMBLE)  # preamble guaranteed even if the model omits it
    assert res.raw == "Sentiment 🟢 — steady."
    assert res.usage["input"] == 700
    assert res.model == "gemini-2.5-flash"


def test_generate_brief_empty_response_is_skipped() -> None:
    res = generate_brief(["X:Y"], generate=lambda m, p: ("   ", {}))
    assert res is None


def test_generate_brief_api_error_is_fail_soft() -> None:
    def boom(model: str, prompt: str) -> tuple[str, dict[str, int]]:
        raise RuntimeError("quota exceeded")

    assert generate_brief(["X:Y"], generate=boom) is None  # never raises


def test_generate_brief_missing_key_skips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # No injected generate + no key → skip (None), never attempts a network call.
    assert generate_brief(["X:Y"]) is None


def test_load_watchlist_lines(tmp_path: Path) -> None:
    from qalpha_research.ai_brief import load_watchlist_lines

    csv = tmp_path / "wl.csv"
    csv.write_text("ticker,sector\nRELIANCE.NS,ENERGY\nITC.NS,FMCG\n", encoding="utf-8")
    lines = load_watchlist_lines(str(csv))
    assert lines == ["RELIANCE:ENERGY", "ITC:FMCG"]  # .NS stripped, TICKER:SECTOR form
