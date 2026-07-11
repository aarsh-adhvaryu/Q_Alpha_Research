"""Tests for the whole-system integration check — the cross-repo end-to-end health board."""

from __future__ import annotations

from qalpha_research.system_check import (
    all_healthy,
    check_ai_brief,
    check_engine,
    check_hedge_overlay,
    check_product_artifact,
    check_telegram,
    render,
    run_all,
)


def test_engine_check_runs_the_validated_accounting() -> None:
    s = check_engine()
    assert s.ok and s.critical  # the qalpha engine must import and compute
    assert "cost" in s.detail.lower()


def test_hedge_overlay_runs_on_the_engine() -> None:
    s = check_hedge_overlay()  # uses the committed fragility panel
    assert s.ok and s.critical
    assert "gauge" in s.detail.lower()


def test_ai_brief_contract_holds_without_network() -> None:
    s = check_ai_brief()  # injects a fake generate internally
    assert s.ok and s.critical


def test_telegram_is_informational_not_critical() -> None:
    on = check_telegram(lambda: True)
    off = check_telegram(lambda: False)
    assert on.ok and not on.critical
    assert not off.ok and not off.critical  # unset is fine — informational, doesn't gate health


def test_product_artifact_uses_injected_fetch() -> None:
    ok = check_product_artifact(fetch=lambda _u: "# paper dashboard\n...")
    assert ok.ok and not ok.critical
    bad = check_product_artifact(fetch=lambda _u: (_ for _ in ()).throw(RuntimeError("offline")))
    assert not bad.ok and not bad.critical  # network failure is informational, not a system failure


def test_run_all_and_health_gate() -> None:
    statuses = run_all(fetch=lambda _u: "ok", configured=lambda: False)
    names = [s.name for s in statuses]
    assert any("engine" in n.lower() for n in names)
    assert any("hedge" in n.lower() for n in names)
    # Telegram unset + a good fetch → still healthy, because only *critical* subsystems gate.
    assert all_healthy(statuses) is True
    md = render(statuses)
    assert "Whole system" in md


def test_health_gate_fails_when_a_critical_subsystem_is_red() -> None:
    from qalpha_research.system_check import SubsystemStatus

    statuses = [
        SubsystemStatus("engine", ok=False, detail="boom", critical=True),
        SubsystemStatus("telegram", ok=False, detail="unset", critical=False),
    ]
    assert all_healthy(statuses) is False
    assert "needs attention" in render(statuses)
