# ═══════════════════════════════════════════════════════════════
# Sub Ladder v4.0 — Score Submission API
# Server IP: 45.156.84.114
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
import pymysql
import json
import os
from datetime import datetime

from database import get_db
from auth.jwt import _verify_jwt
from cheat import (
    validate_score_submission,
    inspect_score_submission,
    log_suspicious_score,
)

router = APIRouter(prefix="/score", tags=["score"])
security = HTTPBearer(auto_error=False)


def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    try:
        payload = _verify_jwt(credentials.credentials)
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "profile_name": payload.get("profile_name"),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Request Model ──────────────────────────────────────────────

class ScoreSubmission(BaseModel):
    subs: int = Field(..., ge=0, le=1000000)
    level: int = Field(..., ge=0, le=15)
    won: bool = False
    walked: bool = False
    mode: str = Field("normal", pattern="^(easy|normal|hard)$")
    response_time_avg: Optional[float] = Field(None, ge=0, le=10000)
    correct_answers: Optional[int] = Field(None, ge=0, le=1000)


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/")
async def submit_score(
    data: ScoreSubmission,
    current_user: dict = Depends(get_current_user_from_token),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Submit a single-game score. Requires JWT authentication.
    
    The score is validated for anti-cheat, and if suspicious patterns are detected,
    the submission is logged but still accepted.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Non authentifié")

    # Validate score submission
    invalid_reasons = validate_score_submission(data)
    if invalid_reasons:
        raise HTTPException(status_code=422, detail={
            "message": "Score validation failed",
            "issues": invalid_reasons
        })

    # Check for suspicious patterns (but allow submission)
    suspicious_warnings = inspect_score_submission(data)

    user_id = current_user["id"]
    profile_name = current_user.get("profile_name", "default")

    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # Find the user's profile
            cursor.execute(
                "SELECT id FROM profiles WHERE user_id = %s AND game_name = %s",
                (user_id, profile_name)
            )
            profile = cursor.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="Profil non trouvé")

            profile_id = profile["id"]

            # Insert the score into database
            cursor.execute(
                """INSERT INTO scores
                   (profile_id, subs, level, won, walked, mode, response_time_avg, correct_answers, submitted_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    profile_id,
                    data.subs,
                    data.level,
                    int(data.won),
                    int(data.walked),
                    data.mode,
                    data.response_time_avg,
                    data.correct_answers,
                    datetime.now()
                )
            )

            db.commit()
            score_id = cursor.lastrowid

        # If suspicious, log it but still return success
        if suspicious_warnings:
            log_suspicious_score(
                user_id=user_id,
                profile_name=profile_name,
                warnings=suspicious_warnings,
                payload=data.dict(),
            )

        message = "Score soumis avec succès"
        if suspicious_warnings:
            message += " — Submission reviewed for anti-cheat verification"

        return {
            "message": message,
            "score_id": score_id,
            "subs": data.subs,
            "level": data.level,
            "won": data.won,
            "walked": data.walked,
            "mode": data.mode,
            "submitted_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement du score: {str(e)}")
