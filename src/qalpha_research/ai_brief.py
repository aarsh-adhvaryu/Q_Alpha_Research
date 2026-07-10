"""Daily AI market brief — an LLM *narrative* layer (Ops Layer PR-4). **Context only, never a signal.**

**Honest framing (load-bearing, do not weaken):** this is a language-model *narrative* — market
context for a human to read, nothing more. It never computes a number, never feeds the deterministic
advisor/engine, and never changes an allocation (the repo's iron rule: no new alpha without
validation). Any discretionary idea it surfaces is explicitly for the existing **satellite sleeve**
(the container built for human judgment calls, ≤8% sleeve / ≤2.5% per name). Every brief opens with a
"context only, not a signal" line so it can never be mistaken for the validated system's output. It
lives in the *research* repo precisely so the product stays deterministic and LLM-free.

**Model:** Google Gemini (free tier) with built-in **Google Search grounding**, so the brief reflects
*today's* news without any RSS plumbing. The single networked call is isolated behind an injectable
:data:`GenerateFn` seam; everything else here (:func:`build_prompt`, :func:`format_for_telegram`,
parsing) is pure and unit-tested with no network and no SDK installed.

**Fail-soft everywhere:** a missing ``GEMINI_API_KEY``, an API/quota error, or an empty response →
skip (return ``None``) with a log line. The cron must never go red because the brief hiccuped.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field

# The opening line every brief must carry — the whole point is that this can never read as a signal.
CONTEXT_PREAMBLE = "🧠 AI market brief — context only, not a signal."
_DEFAULT_MODEL = "gemini-3.5-flash"  # current free-tier flash (2026); override via GEMINI_MODEL
_MAX_OUTPUT_TOKENS = 1500  # a hard ceiling on output cost (the brief is ~500 tokens)
_MAX_SEARCHES = 4  # grounding: "why Nifty moved today" + 1–3 driver follow-ups
_TELEGRAM_LIMIT = 3900  # Telegram hard-caps a message at 4096 chars; leave headroom

# A GenerateFn takes (model, prompt) → (text, usage). Injectable so tests supply a canned response
# with no network and no google-genai installed; the default wires the grounded Gemini call.
GenerateFn = Callable[[str, str], tuple[str, dict[str, int]]]


@dataclass(frozen=True)
class BriefResult:
    """A generated brief: the Telegram-ready text, the raw model markdown, and token usage."""

    text: str  # formatted for Telegram (preamble guaranteed, truncated to the limit)
    raw: str  # the model's raw markdown (archived to reports/ai_brief.md)
    model: str
    usage: dict[str, int] = field(default_factory=dict)


def build_prompt(watchlist_lines: list[str]) -> str:
    """Build the (short, stable) prompt: a fixed markdown template request + the watchlist as context.

    Pure and deterministic. The watchlist is passed as a compact ``TICKER:SECTOR`` line list (~96
    names ≈ ~700 tokens), not a table dump, to keep input spend down.
    """
    watchlist = ", ".join(watchlist_lines)
    return (
        "You are a market-context assistant for an Indian-equity (NSE) investor. Use Google Search "
        "to read today's Indian market news, then write a SHORT brief. No preamble, template only.\n\n"
        f"Open with exactly this line: {CONTEXT_PREAMBLE}\n\n"
        "Then, in ≤1800 characters of Telegram-friendly markdown:\n"
        "1. **Sentiment**: 🟢/🟠/🔴 + one sentence on the day.\n"
        "2. **Drivers**: the top 2–3, each with the *why* (e.g. 'crude +4% on X → OMC margins "
        "compress, aviation/paint input costs rise').\n"
        "3. **Watchlist names affected**: from the list below, name the few most touched by the "
        "drivers.\n"
        "4. **Discretionary ideas** (0–2, optional): tag each 'satellite sleeve rules apply'. Omit if "
        "nothing stands out.\n"
        "5. **Risk note**: one line.\n\n"
        "This is CONTEXT for a human, NOT a trade signal; never imply certainty or a recommendation "
        "the system will act on.\n\n"
        f"Watchlist (TICKER:SECTOR): {watchlist}"
    )


def format_for_telegram(text: str, *, limit: int = _TELEGRAM_LIMIT) -> str:
    """Guarantee the context-only preamble and fit within Telegram's length cap.

    If the model dropped the preamble, prepend it (the disclaimer is non-negotiable). Then truncate
    on a whitespace boundary with an ellipsis if over ``limit``.
    """
    body = text.strip()
    if CONTEXT_PREAMBLE not in body.splitlines()[0:1] and not body.startswith(CONTEXT_PREAMBLE):
        body = f"{CONTEXT_PREAMBLE}\n\n{body}"
    if len(body) <= limit:
        return body
    cut = body.rfind(" ", 0, limit - 1)
    if cut <= 0:
        cut = limit - 1
    return body[:cut].rstrip() + "…"


def load_watchlist_lines(csv_path: str) -> list[str]:
    """Read the vendored Nifty-100 watchlist CSV into compact ``TICKER:SECTOR`` lines (pure I/O)."""
    import csv

    lines: list[str] = []
    with open(csv_path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ticker = (row.get("ticker") or "").strip()
            sector = (row.get("sector") or "").strip()
            if ticker:
                lines.append(f"{ticker.removesuffix('.NS')}:{sector}")
    return lines


def _default_generate(api_key: str, model: str) -> GenerateFn:
    """Wire the real grounded Gemini call. Lazy-imports google-genai so the module (and the pure
    tests) load without the ``ai`` extra installed."""

    def generate(model_id: str, prompt: str) -> tuple[str, dict[str, int]]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                max_output_tokens=_MAX_OUTPUT_TOKENS,
                temperature=0.4,
            ),
        )
        text = resp.text or ""
        usage: dict[str, int] = {}
        meta = getattr(resp, "usage_metadata", None)
        if meta is not None:
            usage = {
                "input": int(getattr(meta, "prompt_token_count", 0) or 0),
                "output": int(getattr(meta, "candidates_token_count", 0) or 0),
                "total": int(getattr(meta, "total_token_count", 0) or 0),
            }
        return text, usage

    return generate


def generate_brief(
    watchlist_lines: list[str],
    *,
    generate: GenerateFn | None = None,
    model: str | None = None,
) -> BriefResult | None:
    """Produce today's brief, or ``None`` if it can't (fail-soft — the caller stays green).

    ``generate`` is injected in tests (a canned response). In production it defaults to the grounded
    Gemini call, which needs ``GEMINI_API_KEY`` — absent it, this returns ``None`` (skip).
    """
    model = model or os.environ.get("GEMINI_MODEL") or _DEFAULT_MODEL
    if generate is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("[ai-brief] GEMINI_API_KEY not set — skipping the brief.")
            return None
        generate = _default_generate(api_key, model)
    try:
        raw, usage = generate(model, build_prompt(watchlist_lines))
    except Exception as exc:  # fail-soft: never break the cron on an API/quota/parse error
        print(f"[ai-brief] generation failed (non-fatal): {exc}")
        return None
    if not raw.strip():
        print("[ai-brief] empty response — skipping.")
        return None
    return BriefResult(text=format_for_telegram(raw), raw=raw.strip(), model=model, usage=usage)
