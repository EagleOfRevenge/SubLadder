"""
cheat.py — Server-side suspicious activity detection and logging.
"""

import json
import os
import time

VALID_SUB_VALUES = {0, 1, 2, 3, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100}
MAX_RESPONSE_TIME = 60.0
MIN_RESPONSE_TIME = 0.1
MAX_CORRECT_ANSWERS = 15
MAX_LEVEL = 15

CHEAT_LOG_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "cheat_log.json")
)


def _ensure_log_file() -> list:
    os.makedirs(os.path.dirname(CHEAT_LOG_FILE), exist_ok=True)
    if not os.path.exists(CHEAT_LOG_FILE):
        with open(CHEAT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
    try:
        with open(CHEAT_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _write_log(entries: list):
    os.makedirs(os.path.dirname(CHEAT_LOG_FILE), exist_ok=True)
    with open(CHEAT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def validate_score_submission(data) -> list:
    """Return a list of invalid fields or incoherent score submission values."""
    issues = []

    if data.won and data.walked:
        issues.append("A score cannot be both won and walked away.")

    if data.subs not in VALID_SUB_VALUES:
        issues.append(f"subs ({data.subs}) is not a valid score value.")

    if not isinstance(data.level, int) or data.level < 0 or data.level > MAX_LEVEL:
        issues.append(f"level ({data.level}) must be between 0 and {MAX_LEVEL}.")

    if data.correct_answers is not None:
        if not isinstance(data.correct_answers, int):
            issues.append("correct_answers must be an integer.")
        elif data.correct_answers < 0 or data.correct_answers > MAX_CORRECT_ANSWERS:
            issues.append(
                f"correct_answers ({data.correct_answers}) must be between 0 and {MAX_CORRECT_ANSWERS}."
            )

    if data.response_time_avg is not None:
        if not isinstance(data.response_time_avg, (int, float)):
            issues.append("response_time_avg must be a number.")
        elif data.response_time_avg < MIN_RESPONSE_TIME or data.response_time_avg > MAX_RESPONSE_TIME:
            issues.append(
                f"response_time_avg ({data.response_time_avg}) is outside realistic bounds."
            )

    if data.won and (data.subs != 100 or data.level != 15):
        issues.append("A winning game must report 100 subs and level 15.")

    if data.walked and data.subs == 100:
        issues.append("A walked-away game cannot award the full 100 subs prize.")

    if not data.won and not data.walked and data.subs == 100:
        issues.append("A score of 100 subs must be marked as won.")

    return issues


def inspect_score_submission(data) -> list:
    """Return heuristic warnings for suspicious but not necessarily invalid scores."""
    warnings = []

    if data.correct_answers is not None and data.response_time_avg is not None:
        if data.correct_answers >= 10 and data.response_time_avg < 0.8:
            warnings.append(
                "Very low average response time for a high number of correct answers."
            )
        if data.correct_answers >= 12 and data.response_time_avg < 0.6:
            warnings.append(
                "Extremely fast responses for a near-perfect game."
            )

    if data.subs == 100 and data.response_time_avg is not None and data.response_time_avg < 0.5:
        warnings.append(
            "Perfect score with an unusually low average response time."
        )

    if data.mode == "hard" and data.correct_answers is not None and data.correct_answers >= 12:
        if data.response_time_avg is not None and data.response_time_avg < 1.0:
            warnings.append(
                "High correct count on hard mode with very fast response times."
            )

    return warnings


def log_suspicious_score(user_id: int, profile_name: str,
                         warnings: list, payload: dict) -> dict:
    """Write a suspicious score submission to the server cheat log."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user_id": user_id,
        "profile_name": profile_name,
        "warnings": warnings,
        "payload": payload,
    }
    entries = _ensure_log_file()
    entries.append(entry)
    _write_log(entries)
    return entry


def load_cheat_log(user_id: int = None) -> list:
    """Return cheat log entries optionally filtered by user."""
    entries = _ensure_log_file()
    if user_id is not None:
        return [entry for entry in entries if entry.get("user_id") == user_id]
    return entries
