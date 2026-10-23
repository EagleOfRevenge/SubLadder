# ═══════════════════════════════════════════════════════════════
# Sub Ladder v4.0 — Leaderboard API
# Server IP: 45.156.84.114
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import pymysql
import os

from database import get_db

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/")
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=500),
    mode: Optional[str] = Query(None, pattern="^(easy|normal|hard|all)$"),
    offset: int = Query(0, ge=0),
    db: pymysql.Connection = Depends(get_db)
):
    """Get global leaderboard (top scores)."""
    query = """
        SELECT
            p.game_name AS profile_name,
            u.discord_username AS discord_name,
            u.steam_id,
            s.subs,
            s.level,
            s.won,
            s.walked,
            s.mode,
            s.correct_answers,
            s.response_time_avg,
            s.submitted_at
        FROM scores s
        JOIN profiles p ON s.profile_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE 1=1
    """
    params = []

    if mode and mode != "all":
        query += " AND s.mode = %s"
        params.append(mode)

    query += " ORDER BY s.subs DESC, s.level DESC, s.won DESC, s.submitted_at ASC"
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()

    return {
        "total": len(results),
        "limit": limit,
        "offset": offset,
        "mode": mode,
        "scores": results,
    }


@router.get("/profile/{profile_name}")
async def get_profile_leaderboard(
    profile_name: str,
    limit: int = Query(50, ge=1, le=500),
    db: pymysql.Connection = Depends(get_db)
):
    """Get scores for a specific game profile."""
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Find the profile
        cursor.execute(
            "SELECT id, game_name FROM profiles WHERE game_name = %s",
            (profile_name,)
        )
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        # Get scores
        cursor.execute(
            """SELECT subs, level, won, walked, mode, correct_answers,
                      response_time_avg, submitted_at
               FROM scores
               WHERE profile_id = %s
               ORDER BY submitted_at DESC
               LIMIT %s""",
            (profile["id"], limit)
        )
        scores = cursor.fetchall()

        # Get stats
        cursor.execute(
            """SELECT COUNT(*) as games_played,
                      SUM(won) as games_won,
                      MAX(level) as best_level,
                      MAX(subs) as best_subs,
                      AVG(response_time_avg) as avg_response_time
               FROM scores
               WHERE profile_id = %s""",
            (profile["id"],)
        )
        stats = cursor.fetchone()

    return {
        "profile": {
            "name": profile["game_name"],
            "discord_name": None,
            "stats": stats,
            "scores": scores,
        }
    }
