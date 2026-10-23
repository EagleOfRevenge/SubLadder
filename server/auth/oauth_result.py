"""
Temporary in-memory storage for OAuth results.

Used by the game client to poll for the outcome of a Discord/Steam login
after the browser redirects back to the server callback.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from threading import Lock

_OAUTH_RESULTS: dict[str, dict] = {}
_LOCK = Lock()
_DEFAULT_TTL_SECONDS = 300


def _cleanup_expired() -> None:
    now = datetime.now(timezone.utc)
    expired = [state for state, payload in _OAUTH_RESULTS.items() if payload.get("expires_at") and payload["expires_at"] <= now]
    for state in expired:
        _OAUTH_RESULTS.pop(state, None)


def store_oauth_result(state: str, result: dict, ttl_seconds: int = _DEFAULT_TTL_SECONDS) -> None:
    if not state:
        return

    with _LOCK:
        _cleanup_expired()
        _OAUTH_RESULTS[state] = {
            "result": result,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        }


def pop_oauth_result(state: str) -> dict | None:
    if not state:
        return None

    with _LOCK:
        _cleanup_expired()
        payload = _OAUTH_RESULTS.pop(state, None)
        if not payload:
            return None
        return payload.get("result")


def peek_oauth_result(state: str) -> dict | None:
    if not state:
        return None

    with _LOCK:
        _cleanup_expired()
        payload = _OAUTH_RESULTS.get(state)
        if not payload:
            return None
        return payload.get("result")