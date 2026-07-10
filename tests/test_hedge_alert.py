"""Tests for the hedge-flip Telegram alert (transition logic + fail-soft sender), Ops Layer PR-3."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from hedge_paper import (
    _load_hedge_state,
    _should_alert,
    hedge_alert_message,
    maybe_send_hedge_alert,
)

from qalpha_research.notify import Transport, send_telegram
from qalpha_research.regime.hedge_paper import HedgePaperResult


@pytest.fixture
def _telegram_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TOK")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "CHAT")


def _res(hedge_on: bool, gauge: float = 0.74, tau: float = 0.7) -> HedgePaperResult:
    # A minimal stand-in — maybe_send_hedge_alert only reads hedge_on / gauge_now / tau.
    return cast("HedgePaperResult", SimpleNamespace(hedge_on=hedge_on, gauge_now=gauge, tau=tau))


def _recorder() -> tuple[list[bytes], Transport]:
    """A fake transport that records request bodies and returns HTTP 200."""
    bodies: list[bytes] = []

    def transport(url: str, body: bytes) -> int:
        bodies.append(body)
        return 200

    return bodies, transport


# --- pure transition logic ----------------------------------------------------------------------


def test_should_alert_only_on_transition() -> None:
    assert _should_alert(None, True) is False  # first observation = silent baseline
    assert _should_alert(None, False) is False
    assert _should_alert(True, True) is False
    assert _should_alert(False, False) is False
    assert _should_alert(False, True) is True  # OFF → ON
    assert _should_alert(True, False) is True  # ON → OFF


def test_hedge_alert_message_both_directions() -> None:
    on = hedge_alert_message(hedge_on=True, gauge_now=0.74, tau=0.7)
    assert "ON (paper)" in on and "0.74" in on and "0.7" in on and "Consider" in on
    off = hedge_alert_message(hedge_on=False, gauge_now=0.55, tau=0.7)
    assert "OFF (paper)" in off and "eased" in off


# --- composed send + state persistence ----------------------------------------------------------


def test_first_run_is_silent_baseline(tmp_path: Path, _telegram_env: None) -> None:
    bodies, transport = _recorder()
    state = tmp_path / "s.json"
    sent = maybe_send_hedge_alert(_res(True), state_path=state, transport=transport)
    assert sent is False  # no prior state → baseline, nothing sent
    assert bodies == []
    assert _load_hedge_state(state) is True  # but the state is now persisted


def test_transition_fires_and_persists(tmp_path: Path, _telegram_env: None) -> None:
    state = tmp_path / "s.json"
    state.write_text('{"hedge_on": false}', encoding="utf-8")
    bodies, transport = _recorder()
    sent = maybe_send_hedge_alert(_res(True), state_path=state, transport=transport)
    assert sent is True
    assert bodies and b"ON (paper)" in bodies[0]
    assert _load_hedge_state(state) is True


def test_no_transition_stays_silent(tmp_path: Path, _telegram_env: None) -> None:
    state = tmp_path / "s.json"
    state.write_text('{"hedge_on": true}', encoding="utf-8")
    bodies, transport = _recorder()
    sent = maybe_send_hedge_alert(_res(True), state_path=state, transport=transport)
    assert sent is False and bodies == []


# --- notify fail-soft contract ------------------------------------------------------------------


def test_send_telegram_fail_soft(_telegram_env: None) -> None:
    def boom(url: str, body: bytes) -> int:
        raise RuntimeError("down")

    assert send_telegram("x", transport=boom) is False  # never raises


def test_send_telegram_no_config_no_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    bodies, transport = _recorder()
    assert send_telegram("x", transport=transport) is False
    assert bodies == []
