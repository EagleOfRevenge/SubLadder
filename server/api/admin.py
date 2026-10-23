# ═══════════════════════════════════════════════════════════════
# Sub Ladder v4.0 — Admin API
# Ban management, rank adjustments, moderation tools
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import pymysql
from datetime import datetime, timedelta
import sys
import os
import re
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from auth.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("sub_ladder.admin")

# ══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════

class BanRequest(BaseModel):
    profile_id: Optional[int] = Field(None, ge=1)
    user_id: Optional[int] = Field(None, ge=1)
    reason: str = Field(..., min_length=3, max_length=255)
    expires_at: Optional[str] = None  # ISO format datetime, None = permanent
    banned_by: str = Field("admin", min_length=3, max_length=64)

class UnbanRequest(BaseModel):
    ban_id: int = Field(..., ge=1)
    lift_reason: Optional[str] = Field(None, min_length=3, max_length=255)

class BanInfo(BaseModel):
    id: int
    user_id: Optional[int]
    profile_id: Optional[int]
    profile_name: Optional[str]
    reason: str
    banned_by: str
    created_at: str
    expires_at: Optional[str]
    active: bool
    lifted_at: Optional[str]
    lift_reason: Optional[str]

class AdjustRankRequest(BaseModel):
    profile_id: int = Field(..., ge=1)
    new_elo: int = Field(..., ge=0, le=5000)
    reason: str = Field(..., min_length=3, max_length=255)
    adjusted_by: str = Field("admin", min_length=3, max_length=64)

class RankHistoryEntry(BaseModel):
    id: int
    profile_id: int
    profile_name: str
    old_elo: int
    new_elo: int
    elo_change: int
    change_reason: str
    changed_by: str
    recorded_at: str

# ══════════════════════════════════════════════════════════════════
# HELPER FUNCTION
# ══════════════════════════════════════════════════════════════════

def verify_admin(user):
    """Verify admin access using a role claim from the authenticated JWT."""
    if not user or not user.get("user_id"):
        raise HTTPException(status_code=401, detail="Non authentifié")

    role = str(user.get("role") or "user")
    if role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé. Admin requis.")

# ══════════════════════════════════════════════════════════════════
# ENDPOINTS — BAN MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@router.post("/ban")
async def ban_profile(
    request: BanRequest,
    db: pymysql.Connection = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Ban a profile or user account.
    Can be temporary (expires_at) or permanent.
    """
    verify_admin(user)

    if request.profile_id is None and request.user_id is None:
        raise HTTPException(status_code=400, detail="profile_id ou user_id requis")

    if request.profile_id is not None and request.user_id is not None:
        raise HTTPException(status_code=400, detail="Fournir soit profile_id soit user_id, pas les deux")

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        expires_dt = None
        if request.expires_at:
            try:
                expires_dt = datetime.fromisoformat(request.expires_at)
            except ValueError:
                raise HTTPException(status_code=400, detail="expires_at format invalide (ISO 8601)")

        cursor.execute(
            """INSERT INTO bans 
               (user_id, profile_id, reason, banned_by, created_at, expires_at, active)
               VALUES (%s, %s, %s, %s, NOW(), %s, 1)""",
            (
                request.user_id,
                request.profile_id,
                request.reason,
                request.banned_by,
                expires_dt
            )
        )
        db.commit()
        ban_id = cursor.lastrowid
        logger.warning("Admin ban created", extra={"admin_user_id": user.get("user_id"), "target_profile_id": request.profile_id, "target_user_id": request.user_id, "reason": request.reason})

        return {
            "status": "banned",
            "ban_id": ban_id,
            "message": f"Ban créé (ID: {ban_id})",
            "expires_at": request.expires_at
        }


@router.post("/unban")
async def unban_profile(
    request: UnbanRequest,
    db: pymysql.Connection = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Lift a ban (mark as inactive).
    """
    verify_admin(user)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            """UPDATE bans 
               SET active = 0, lifted_at = NOW(), lift_reason = %s
               WHERE id = %s""",
            (request.lift_reason or "Removed by admin", request.ban_id)
        )
        db.commit()
        logger.warning("Admin ban removed", extra={"admin_user_id": user.get("user_id"), "ban_id": request.ban_id, "reason": request.lift_reason})

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ban non trouvé")

        return {
            "status": "unbanned",
            "ban_id": request.ban_id,
            "message": f"Ban levé (ID: {request.ban_id})"
        }


@router.get("/bans", response_model=List[BanInfo])
async def list_bans(
    active_only: bool = Query(True, description="Afficher seulement les bans actifs"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: pymysql.Connection = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    List all bans (active or all history).
    """
    verify_admin(user)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        query = """
            SELECT 
                b.id,
                b.user_id,
                b.profile_id,
                p.game_name,
                b.reason,
                b.banned_by,
                b.created_at,
                b.expires_at,
                b.active,
                b.lifted_at,
                b.lift_reason
            FROM bans b
            LEFT JOIN profiles p ON b.profile_id = p.id
        """
        
        params = []
        
        if active_only:
            query += " WHERE b.active = 1"
        
        query += " ORDER BY b.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        bans = cursor.fetchall()

        return [
            BanInfo(
                id=b["id"],
                user_id=b["user_id"],
                profile_id=b["profile_id"],
                profile_name=b["game_name"],
                reason=b["reason"],
                banned_by=b["banned_by"],
                created_at=b["created_at"].isoformat(),
                expires_at=b["expires_at"].isoformat() if b["expires_at"] else None,
                active=bool(b["active"]),
                lifted_at=b["lifted_at"].isoformat() if b["lifted_at"] else None,
                lift_reason=b["lift_reason"]
            )
            for b in bans
        ]


# ══════════════════════════════════════════════════════════════════
# ENDPOINTS — RANK MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@router.post("/adjust-rank")
async def adjust_rank(
    request: AdjustRankRequest,
    db: pymysql.Connection = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Manually adjust a player's ELO rating.
    Records the change in rank_history for audit trail.
    """
    verify_admin(user)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Get current ELO
        cursor.execute(
            "SELECT elo FROM elo_ratings WHERE profile_id = %s",
            (request.profile_id,)
        )
        elo_record = cursor.fetchone()
        
        if not elo_record:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        old_elo = elo_record["elo"]
        elo_change = request.new_elo - old_elo

        # Update ELO
        cursor.execute(
            """UPDATE elo_ratings 
               SET elo = %s, updated_at = NOW()
               WHERE profile_id = %s""",
            (request.new_elo, request.profile_id)
        )

        # Record in rank_history
        cursor.execute(
            """INSERT INTO rank_history 
               (profile_id, old_elo, new_elo, change_reason, changed_by, recorded_at)
               VALUES (%s, %s, %s, %s, %s, NOW())""",
            (
                request.profile_id,
                old_elo,
                request.new_elo,
                request.reason,
                request.adjusted_by
            )
        )
        
        db.commit()
        logger.warning("Admin rank adjusted", extra={"admin_user_id": user.get("user_id"), "profile_id": request.profile_id, "new_elo": request.new_elo, "reason": request.reason})

        return {
            "status": "adjusted",
            "profile_id": request.profile_id,
            "old_elo": old_elo,
            "new_elo": request.new_elo,
            "elo_change": elo_change,
            "reason": request.reason,
            "adjusted_by": request.adjusted_by
        }


@router.get("/rank-history/{profile_id}", response_model=List[RankHistoryEntry])
async def get_rank_history(
    profile_id: int,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: pymysql.Connection = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Get rank adjustment history for a profile (admin view).
    """
    verify_admin(user)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Verify profile exists
        cursor.execute(
            "SELECT game_name FROM profiles WHERE id = %s",
            (profile_id,)
        )
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        # Get rank history
        cursor.execute(
            """SELECT 
                rh.id,
                rh.profile_id,
                p.game_name,
                rh.old_elo,
                rh.new_elo,
                (rh.new_elo - rh.old_elo) as elo_change,
                rh.change_reason,
                rh.changed_by,
                rh.recorded_at
            FROM rank_history rh
            JOIN profiles p ON rh.profile_id = p.id
            WHERE rh.profile_id = %s
            ORDER BY rh.recorded_at DESC
            LIMIT %s OFFSET %s""",
            (profile_id, limit, offset)
        )
        entries = cursor.fetchall()

        return [
            RankHistoryEntry(
                id=e["id"],
                profile_id=e["profile_id"],
                profile_name=e["game_name"],
                old_elo=e["old_elo"],
                new_elo=e["new_elo"],
                elo_change=e["elo_change"],
                change_reason=e["change_reason"],
                changed_by=e["changed_by"],
                recorded_at=e["recorded_at"].isoformat()
            )
            for e in entries
        ]


@router.get("/rank-history-global", response_model=List[RankHistoryEntry])
async def get_rank_history_global(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: pymysql.Connection = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Get all rank adjustments across all profiles (admin audit log).
    """
    verify_admin(user)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            """SELECT 
                rh.id,
                rh.profile_id,
                p.game_name,
                rh.old_elo,
                rh.new_elo,
                (rh.new_elo - rh.old_elo) as elo_change,
                rh.change_reason,
                rh.changed_by,
                rh.recorded_at
            FROM rank_history rh
            JOIN profiles p ON rh.profile_id = p.id
            ORDER BY rh.recorded_at DESC
            LIMIT %s OFFSET %s""",
            (limit, offset)
        )
        entries = cursor.fetchall()

        return [
            RankHistoryEntry(
                id=e["id"],
                profile_id=e["profile_id"],
                profile_name=e["game_name"],
                old_elo=e["old_elo"],
                new_elo=e["new_elo"],
                elo_change=e["elo_change"],
                change_reason=e["change_reason"],
                changed_by=e["changed_by"],
                recorded_at=e["recorded_at"].isoformat()
            )
            for e in entries
        ]
