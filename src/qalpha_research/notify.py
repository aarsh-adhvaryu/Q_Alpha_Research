"""Telegram notification spine for the research repo (hedge-flip alerts, Ops Layer PR-3).

**Deliberate copy** of the product's ``qalpha/live/notify.py`` (~30 lines of stdlib). The two repos
stay decoupled on purpose — the product **never imports from research** and vice-versa — so this small
sender is duplicated rather than shared through a package boundary. Keep the two in sync by hand if the
Telegram wire ever changes.

**Fail-soft is the whole contract.** The hedge paper cron is a forward research track record; it must
never go red because Telegram hiccuped or a token rotated. Every path swallows its exception and
returns ``False`` — a missed alert is acceptable, a broken cron is not.

Configuration is two env vars (``TELEGRAM_BOT_TOKEN`` / ``TELEGRAM_CHAT_ID``); absent them the sender
is a no-op returning ``False``. The ``transport`` seam makes it unit-testable with no network.
"""

from __future__ import annotations

import os
import urllib.request
from collections.abc import Callable
from html import escape

# A transport takes (url, body_bytes) and returns the HTTP status code. Injectable so tests assert the
# request without a socket; the default hits api.telegram.org via urllib.
Transport = Callable[[str, bytes], int]

_API = "https://api.telegram.org/bot{token}/sendMessage"


def html_escape(text: str) -> str:
    """Escape a value for Telegram ``parse_mode=HTML`` (so a stray ``<`` / ``&`` can't break a send)."""
    return escape(text, quote=False)


def telegram_configured() -> bool:
    """True iff both Telegram env vars are present — lets callers skip work when alerts are off."""
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def _urllib_transport(url: str, body: bytes) -> int:
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return int(resp.status)


def send_telegram(
    text: str, *, parse_mode: str = "HTML", transport: Transport | None = None
) -> bool:
    """Send ``text`` to the configured Telegram chat; return whether it was delivered.

    **Never raises** — any missing config, malformed response, or transport error returns ``False``
    so the caller (the cron) stays green. Pass ``transport`` in tests to capture the request.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id):
        return False
    try:
        import json

        url = _API.format(token=token)
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        body = json.dumps(payload).encode("utf-8")
        send = transport or _urllib_transport
        status = send(url, body)
    except Exception:
        return False
    return 200 <= status < 300
