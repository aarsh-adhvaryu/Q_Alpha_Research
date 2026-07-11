"""Core of the A/B/C forward study (see ``reports/PREREGISTRATION_forward_study.md``).

Three fake-money books measure, forward, whether the validated strategy makes money and whether the
AI's insight helps: **A** strategy only · **B** strategy + AI nudge · **C** buy-and-hold. This module
is the pure, tested core — the AI signal, the fixed deploy-tilt rule, capital-flow-aware book
accounting, and the decision-and-outcome ledger. No I/O beyond JSON round-trips; the daily runner
(prices, the deploy engine, the cron) sits on top. Money is ``Decimal`` (project convention). The AI
signal is **unvalidated by construction** — measuring it is the whole point.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

# ---- the AI signal --------------------------------------------------------------------------------

_LEANS = {"up", "flat", "down"}
_CONF = {"low", "medium", "high"}
# Book B's fixed deploy tilt: 1.0 ± (direction × confidence weight), clamped. Pre-registered — not
# tuned to a result. up+high → deploy 1.4×; down+high → 0.6×; flat or absent → 1.0×.
_CONF_WEIGHT = {"low": 0.10, "medium": 0.25, "high": 0.40}
_TILT_MIN, _TILT_MAX = 0.5, 1.5
# The machine-readable line the AI brief appends, e.g. "SIGNAL: lean=up; band=0.4..0.9; confidence=medium"
_SIGNAL_RE = re.compile(
    r"SIGNAL:\s*lean=(?P<lean>up|flat|down)\s*;\s*band=(?P<lo>-?\d+(?:\.\d+)?)\.\.(?P<hi>-?\d+(?:\.\d+)?)\s*;\s*confidence=(?P<conf>low|medium|high)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AISignal:
    """A day's structured read, parsed from the brief. ``lean`` ∈ up/flat/down; ``confidence`` too."""

    as_of: str
    lean: str
    confidence: str
    band_lo: float
    band_hi: float

    def to_dict(self) -> dict[str, object]:
        return {
            "as_of": self.as_of,
            "lean": self.lean,
            "confidence": self.confidence,
            "band_lo": self.band_lo,
            "band_hi": self.band_hi,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> AISignal:
        return cls(
            as_of=str(d["as_of"]),
            lean=str(d["lean"]),
            confidence=str(d["confidence"]),
            band_lo=float(d["band_lo"]),  # type: ignore[arg-type]
            band_hi=float(d["band_hi"]),  # type: ignore[arg-type]
        )


def parse_ai_signal(brief_text: str, as_of: str) -> AISignal | None:
    """Extract the structured ``SIGNAL:`` line from a brief; ``None`` if absent/malformed (fail-soft
    → Book B then falls back to a neutral 1.0× tilt, so a missing signal can't break the study)."""
    m = _SIGNAL_RE.search(brief_text or "")
    if not m:
        return None
    lean, conf = m.group("lean").lower(), m.group("conf").lower()
    if lean not in _LEANS or conf not in _CONF:
        return None
    return AISignal(as_of, lean, conf, float(m.group("lo")), float(m.group("hi")))


def signal_tilt(signal: AISignal | None) -> float:
    """The fixed deploy-size multiplier Book B applies to the strategy's deploy amount. Neutral (1.0)
    when there is no signal or the lean is flat. Clamped to [0.5, 1.5]. Pre-registered, never tuned."""
    if signal is None or signal.lean == "flat":
        return 1.0
    direction = 1.0 if signal.lean == "up" else -1.0
    tilt = 1.0 + direction * _CONF_WEIGHT.get(signal.confidence, 0.0)
    return max(_TILT_MIN, min(_TILT_MAX, tilt))


# ---- capital-flow-aware book accounting -----------------------------------------------------------


def _int_map(v: object) -> dict[str, int]:
    """Parse a JSON object into a ``{str: int}`` map (empty if it isn't a dict) — typed for mypy."""
    if not isinstance(v, dict):
        return {}
    return {str(k): int(val) for k, val in v.items()}


@dataclass
class Book:
    """One fake-money book. ``net_contributions`` (fake cash put in) is tracked apart from value, so an
    injection is never mistaken for profit: ``profit = value − net_contributions``."""

    name: str
    cash: Decimal = Decimal("0")
    holdings: dict[str, int] = field(default_factory=dict)
    net_contributions: Decimal = Decimal("0")

    def inject(self, amount: Decimal) -> None:
        """Add fake cash (an external contribution, not a gain)."""
        self.cash += amount
        self.net_contributions += amount

    def buy(self, ticker: str, qty: int, price: Decimal) -> None:
        """Buy whole shares with cash (no tax on buys). Raises if it can't afford it."""
        cost = price * qty
        if cost > self.cash:
            raise ValueError(
                f"{self.name}: cannot afford {qty}×{ticker} @ {price} (cash {self.cash})"
            )
        self.cash -= cost
        self.holdings[ticker] = self.holdings.get(ticker, 0) + qty

    def value(self, prices: dict[str, Decimal]) -> Decimal:
        """Mark-to-market: cash + held shares valued at ``prices`` (missing price → that name skipped)."""
        held = sum(prices.get(t, Decimal("0")) * q for t, q in self.holdings.items())
        return self.cash + held

    def profit(self, prices: dict[str, Decimal]) -> Decimal:
        return self.value(prices) - self.net_contributions

    def return_pct(self, prices: dict[str, Decimal]) -> float:
        """Profit as a % of what was put in (money-weighted; fair across books with equal cash flows)."""
        if self.net_contributions <= 0:
            return 0.0
        return float(self.profit(prices) / self.net_contributions) * 100.0

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "cash": str(self.cash),
            "holdings": dict(self.holdings),
            "net_contributions": str(self.net_contributions),
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> Book:
        return cls(
            name=str(d["name"]),
            cash=Decimal(str(d["cash"])),
            holdings=_int_map(d.get("holdings")),
            net_contributions=Decimal(str(d["net_contributions"])),
        )


# ---- decision + outcome ledger --------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    """One logged deploy, with the model reason + AI insight at the time and its later outcome.

    Outcome fields are filled once ``resolve_on`` passes: the bought basket's realised return over the
    window vs Nifty → ``verdict`` (worked / didn't / flat)."""

    as_of: str
    book: str  # "A" | "B"
    amount: str  # Decimal deployed (as str)
    basket: dict[str, int]  # ticker -> qty bought
    model_rationale: str
    ai_insight: str  # e.g. "lean=up confidence=medium (tilt 1.25×)" — snapshot at decision time
    resolve_on: str  # date to score the outcome
    resolved: bool = False
    outcome_return_pct: float | None = None
    benchmark_return_pct: float | None = None
    verdict: str = ""  # "worked" | "didn't" | "flat" | ""

    def to_dict(self) -> dict[str, object]:
        return {
            "as_of": self.as_of,
            "book": self.book,
            "amount": self.amount,
            "basket": dict(self.basket),
            "model_rationale": self.model_rationale,
            "ai_insight": self.ai_insight,
            "resolve_on": self.resolve_on,
            "resolved": self.resolved,
            "outcome_return_pct": self.outcome_return_pct,
            "benchmark_return_pct": self.benchmark_return_pct,
            "verdict": self.verdict,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> Decision:
        return cls(
            as_of=str(d["as_of"]),
            book=str(d["book"]),
            amount=str(d["amount"]),
            basket=_int_map(d.get("basket")),
            model_rationale=str(d.get("model_rationale", "")),
            ai_insight=str(d.get("ai_insight", "")),
            resolve_on=str(d["resolve_on"]),
            resolved=bool(d.get("resolved", False)),
            outcome_return_pct=_opt_float(d.get("outcome_return_pct")),
            benchmark_return_pct=_opt_float(d.get("benchmark_return_pct")),
            verdict=str(d.get("verdict", "")),
        )


def _opt_float(v: object) -> float | None:
    return None if v is None else float(v)  # type: ignore[arg-type]


_WORK_TOL = 0.5  # a decision "worked" only if it beat Nifty by > 0.5 pt over its window (else flat)


def resolve_decision(
    decision: Decision, basket_return_pct: float, benchmark_return_pct: float
) -> Decision:
    """Fill in a due decision's outcome and verdict (pure — returns a new resolved ``Decision``)."""
    gap = basket_return_pct - benchmark_return_pct
    verdict = "worked" if gap > _WORK_TOL else ("didn't" if gap < -_WORK_TOL else "flat")
    return Decision(
        as_of=decision.as_of,
        book=decision.book,
        amount=decision.amount,
        basket=decision.basket,
        model_rationale=decision.model_rationale,
        ai_insight=decision.ai_insight,
        resolve_on=decision.resolve_on,
        resolved=True,
        outcome_return_pct=basket_return_pct,
        benchmark_return_pct=benchmark_return_pct,
        verdict=verdict,
    )


def ai_hit_rate(decisions: list[Decision]) -> tuple[int, int]:
    """Over resolved Book-B decisions, (times the deploy beat Nifty, total resolved) — the running
    'did acting on the AI work' tally. Returns (0, 0) when nothing has resolved yet."""
    resolved = [d for d in decisions if d.resolved and d.book == "B"]
    worked = sum(1 for d in resolved if d.verdict == "worked")
    return worked, len(resolved)


# ---- persistence ----------------------------------------------------------------------------------

LEDGER_PATH = Path("data/forward_study_ledger.json")


def load_ledger(path: Path = LEDGER_PATH) -> list[Decision]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return [Decision.from_dict(d) for d in json.loads(text)]


def save_ledger(decisions: list[Decision], path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([d.to_dict() for d in decisions], indent=2) + "\n", encoding="utf-8")
