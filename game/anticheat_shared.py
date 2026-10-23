"""
anticheat_shared.py — Shared anti-cheat helpers for Sub Ladder.
"""

import hashlib
import json
import os
import time

from constants import (
    ANSWER_LABELS, GAME_MODES, PRIZE_VALUES, SAFE_HAVENS,
    player_level_from_xp,
)
from utils import USER_DATA_DIR

LOG_FILE = os.path.join(USER_DATA_DIR, "anticheat_log.json")
VALID_SAFE_PRIZES = {0, 5, 10}
VALID_ANSWER_LABELS = set(ANSWER_LABELS)
VALID_SUB_VALUES = set(PRIZE_VALUES) | {0}
MAX_LEVEL = 15
MIN_RESPONSE_TIME = 0.1
MAX_RESPONSE_TIME = 60.0


def _save_checksum(save: dict) -> str:
    """Generate a checksum from the deterministic parts of a save."""
    key_fields = {
        "mode":              save.get("mode", "normal"),
        "level":             save.get("level", 1),
        "safe_prize":        save.get("safe_prize", 0),
        "question_id":       save.get("question_id", ""),
        "lifelines":         json.dumps(save.get("lifelines", {}), sort_keys=True),
        "correct_this_game": save.get("correct_this_game", 0),
        "used_ids":          json.dumps(sorted(save.get("used_ids", [])), sort_keys=True),
        "displayed":         json.dumps(save.get("displayed", {}), sort_keys=True),
    }
    raw = json.dumps(key_fields, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def sign_save(save: dict) -> dict:
    """Attach a checksum to a save dict before writing to disk."""
    save = dict(save)
    save["_checksum"] = _save_checksum(save)
    return save


def _ensure_log_file() -> list:
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _write_log(entries: list):
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def log_suspicious_activity(category: str, details: dict = None,
                            save: dict = None, profile: str = None,
                            severity: str = "warning") -> dict:
    """Append a suspicious activity entry to the local anti-cheat log."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "severity": severity,
        "category": category,
        "profile": profile,
        "details": details or {},
    }
    if save is not None:
        entry["save_summary"] = {
            "mode": save.get("mode"),
            "level": save.get("level"),
            "safe_prize": save.get("safe_prize"),
            "correct_this_game": save.get("correct_this_game"),
            "question_id": save.get("question_id"),
            "has_checksum": "_checksum" in save,
        }
    entries = _ensure_log_file()
    entries.append(entry)
    _write_log(entries)
    return entry


def validate_game_state(save: dict, all_questions: list = None) -> list:
    """Return warnings for broken or tampered save state."""
    warnings = []

    if not isinstance(save, dict):
        return ["Save state is not a dictionary."]

    mode = save.get("mode")
    if mode not in GAME_MODES:
        warnings.append(f"Invalid game mode '{mode}'.")

    level = save.get("level")
    if not isinstance(level, int) or not (1 <= level <= MAX_LEVEL):
        warnings.append(f"Invalid level {level}. Expected integer between 1 and {MAX_LEVEL}.")

    safe_prize = save.get("safe_prize", 0)
    if safe_prize not in VALID_SAFE_PRIZES:
        warnings.append(f"Invalid safe_prize {safe_prize}. Expected one of {sorted(VALID_SAFE_PRIZES)}.")
    elif isinstance(level, int) and safe_prize >= level:
        warnings.append(f"safe_prize ({safe_prize}) cannot be greater than or equal to current level ({level}).")
    elif isinstance(level, int) and safe_prize not in (0, 5) and level <= 10:
        warnings.append(f"safe_prize {safe_prize} is inconsistent with current level {level}.")

    correct = save.get("correct_this_game", 0)
    if not isinstance(correct, int) or correct < 0:
        warnings.append(f"Invalid correct_this_game value: {correct}.")
    elif isinstance(level, int) and correct > max(0, level - 1):
        warnings.append(
            f"correct_this_game ({correct}) cannot exceed the number of completed levels ({max(0, level - 1)})."
        )

    lifelines = save.get("lifelines")
    if not isinstance(lifelines, dict):
        warnings.append("lifelines must be a dictionary.")
    else:
        missing = [k for k in ("fifty", "vote", "switch") if k not in lifelines]
        if missing:
            warnings.append(f"Missing lifeline keys: {missing}.")
        for key, value in lifelines.items():
            if key not in ("fifty", "vote", "switch"):
                warnings.append(f"Unexpected lifeline key '{key}'.")
            if not isinstance(value, bool):
                warnings.append(f"lifelines['{key}'] must be boolean.")

    used_ids = save.get("used_ids")
    if not isinstance(used_ids, list):
        warnings.append("used_ids must be a list.")
    else:
        if len(set(used_ids)) != len(used_ids):
            warnings.append("used_ids contains duplicate question ids.")
        if isinstance(level, int) and len(used_ids) != level:
            warnings.append(
                f"used_ids length ({len(used_ids)}) must match the current level ({level})."
            )

    question_id = save.get("question_id")
    if not question_id:
        warnings.append("question_id is missing.")
    elif isinstance(used_ids, list) and question_id not in used_ids:
        warnings.append("question_id must be included in used_ids.")

    displayed = save.get("displayed")
    if not isinstance(displayed, dict):
        warnings.append("displayed must be a dictionary.")
    else:
        answers = displayed.get("answers")
        correct_label = displayed.get("correct")
        if not isinstance(answers, dict):
            warnings.append("displayed.answers must be a dictionary.")
        else:
            missing_labels = [lbl for lbl in ANSWER_LABELS if lbl not in answers]
            if missing_labels:
                warnings.append(f"displayed.answers missing labels: {missing_labels}.")
        if correct_label not in VALID_ANSWER_LABELS:
            warnings.append(f"displayed.correct must be one of {ANSWER_LABELS}. Got {correct_label}.")
        elif isinstance(answers, dict) and correct_label not in answers:
            warnings.append(f"displayed.correct label '{correct_label}' is not present in displayed.answers.")

    if all_questions is not None and question_id and isinstance(displayed, dict):
        candidate = next((q for q in all_questions if q.get("id") == question_id), None)
        if candidate is None:
            warnings.append(f"question_id '{question_id}' does not exist in the current question pool.")
        else:
            correct_label = displayed.get("correct")
            answers = displayed.get("answers", {})
            if correct_label in answers:
                actual_correct = answers.get(correct_label)
                expected = candidate.get("right_answer")
                if actual_correct != expected:
                    warnings.append(
                        "Displayed correct answer does not match the question's right_answer."
                    )

    return warnings


def verify_save(save: dict, all_questions: list = None) -> bool:
    """Return True if the save has not been tampered with."""
    if not isinstance(save, dict) or "_checksum" not in save:
        return False
    stored = save.get("_checksum", "")
    expected = _save_checksum(save)
    if stored != expected:
        log_suspicious_activity(
            "checksum_mismatch",
            details={"stored": stored, "expected": expected},
            save=save
        )
        return False
    warnings = validate_game_state(save, all_questions=all_questions)
    if warnings:
        log_suspicious_activity(
            "invalid_save_state",
            details={"warnings": warnings},
            save=save,
        )
        return False
    return True


def validate_profile(p: dict) -> list:
    """Check a profile dict for suspicious values."""
    warnings = []

    games = p.get("games_played", 0)
    total = p.get("total_subs", 0)
    best = p.get("best_game", 0)
    xp = p.get("total_xp", 0)
    level = p.get("player_level", 1)

    if games < 0:
        warnings.append(f"games_played is negative ({games}).")
    if total < 0:
        warnings.append(f"total_subs is negative ({total}).")
    if best < 0:
        warnings.append(f"best_game is negative ({best}).")
    if xp < 0:
        warnings.append(f"total_xp is negative ({xp}).")

    max_per_game = PRIZE_VALUES[-1]
    if best > max_per_game:
        warnings.append(f"best_game ({best}) exceeds maximum possible ({max_per_game}).")
    if games > 0 and total > max_per_game * games:
        warnings.append(f"total_subs ({total}) exceeds max possible for {games} games.")

    computed_level, _, _ = player_level_from_xp(max(xp, 0))
    if abs(computed_level - level) > 1:
        warnings.append(
            f"player_level ({level}) inconsistent with total_xp ({xp}) — expected ~{computed_level}."
        )
    if xp > 1_000_000:
        warnings.append(f"total_xp ({xp}) is unusually high.")

    for i, sc in enumerate(p.get("scores", [])):
        if sc.get("mode") and sc["mode"] not in GAME_MODES:
            warnings.append(f"scores[{i}] has unknown mode '{sc['mode']}'.")
        subs = sc.get("subs", 0)
        if subs not in VALID_SUB_VALUES:
            warnings.append(f"scores[{i}] subs ({subs}) is not a valid prize value.")
        if sc.get("subs", 0) > max_per_game:
            warnings.append(f"scores[{i}] subs ({subs}) exceeds maximum.")

    return warnings


def validate_data(data: dict) -> dict:
    """Validate all profiles in the data dict."""
    issues = {}
    for name, profile in data.get("profiles", {}).items():
        w = validate_profile(profile)
        if w:
            issues[name] = w
    return issues


def flag_profile(data: dict, profile_name: str, reason: str, manual: bool = False) -> bool:
    """Attach a manual or automated anti-cheat flag to a profile."""
    if not isinstance(data, dict):
        return False
    profiles = data.setdefault("profiles", {})
    profile = profiles.get(profile_name)
    if not profile:
        return False

    flag_list = profile.setdefault("anticheat_flags", [])
    flag_list.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "manual": bool(manual),
        "reason": reason,
    })
    return True


def get_profile_flags(data: dict, profile_name: str) -> list:
    """Return anti-cheat flags for a profile."""
    profile = data.get("profiles", {}).get(profile_name, {})
    return profile.get("anticheat_flags", [])
