"""
Wrapper anti-cheat pour singleplayer — utilise les heuristiques centrales dans server/cheat.py
"""
from typing import Any, Dict, List
from cheat import validate_score_submission, inspect_score_submission, log_suspicious_score


def validate_singleplayer_submission(profile_id: int, profile_name: str, payload: Any) -> Dict[str, Any]:
    """Valide une soumission singleplayer et loggue les warnings si besoin.
    Retourne un dict {valid: bool, issues: [], warnings: []}
    """
    # Assume payload is pydantic-like with attrs used in validate_score_submission
    issues = validate_score_submission(payload)
    warnings = inspect_score_submission(payload)
    if warnings:
        log_suspicious_score(user_id=profile_id, profile_name=profile_name, warnings=warnings, payload=payload.__dict__ if hasattr(payload, '__dict__') else dict(payload))
    return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}
