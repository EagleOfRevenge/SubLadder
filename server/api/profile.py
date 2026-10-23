# ═══════════════════════════════════════════════════════════════
# Sub Ladder v4.0 — User Profile API
# Endpoints: overview, stats (offline/online), match history, ranked
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import pymysql
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from auth.dependencies import get_current_user
from auth.jwt import _verify_jwt
from game.multiplayer.ranked import get_rank_display, get_progression_to_next_rank, DEFAULT_ELO

router = APIRouter(prefix="/profile", tags=["profile"])

security = HTTPBearer(auto_error=False)

# ══════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════

class RankInfo(BaseModel):
    tier: str
    division: Optional[int]
    elo: int
    display: str
    icon: str

class ProfileOverview(BaseModel):
    game_name: str
    account_created_at: str
    current_rank: RankInfo
    ranked_wins: int
    games_played: int
    win_rate: float

class OfflineStats(BaseModel):
    games_played: int
    games_won: int
    win_rate: float
    highest_level: int
    total_subs_collected: int
    average_response_time: Optional[float]

class OnlineStats(BaseModel):
    ranked_games_played: int
    ranked_games_won: int
    ranked_win_rate: float
    current_elo: int
    current_rank: RankInfo
    highest_elo_reached: int

class ProfileStats(BaseModel):
    offline: OfflineStats
    online: OnlineStats

class MatchHistoryItem(BaseModel):
    match_id: int
    opponent_name: str
    opponent_elo: int
    result: str  # "win" or "loss"
    elo_change: int
    match_date: str
    duration_seconds: Optional[int]

class RankedLeaderboardEntry(BaseModel):
    rank: int
    profile_name: str
    elo: int
    games_played: int
    win_rate: float
    rank_tier: str
    rank_division: Optional[int]
    rank_display: str

class RankedDetailResponse(BaseModel):
    player_rank: Optional[RankedLeaderboardEntry]
    grand_champions: List[RankedLeaderboardEntry]
    champions: List[RankedLeaderboardEntry]

# ══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@router.get("/{profile_name}/overview", response_model=ProfileOverview)
async def get_profile_overview(
    profile_name: str,
    db: pymysql.Connection = Depends(get_db)
):
    """
    Get profile overview with name, rank, and ranked wins.
    """
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Find the profile
        cursor.execute(
            "SELECT id, user_id, created_at FROM profiles WHERE game_name = %s",
            (profile_name,)
        )
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        profile_id = profile["id"]

        # Get ELO and ranked stats
        cursor.execute(
            """SELECT elo, games_played, games_won FROM elo_ratings 
               WHERE profile_id = %s""",
            (profile_id,)
        )
        elo_record = cursor.fetchone()

        if not elo_record:
            elo = DEFAULT_ELO
            games_played = 0
            games_won = 0
        else:
            elo = elo_record["elo"]
            games_played = elo_record["games_played"]
            games_won = elo_record["games_won"]

        win_rate = (games_won / games_played * 100) if games_played > 0 else 0

        return ProfileOverview(
            game_name=profile_name,
            account_created_at=profile["created_at"].isoformat(),
            current_rank=RankInfo(**get_rank_display(elo)),
            ranked_wins=games_won,
            games_played=games_played,
            win_rate=round(win_rate, 2)
        )


@router.get("/{profile_name}/stats", response_model=ProfileStats)
async def get_profile_stats(
    profile_name: str,
    db: pymysql.Connection = Depends(get_db)
):
    """
    Get offline and online statistics for a profile.
    """
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Find the profile
        cursor.execute(
            "SELECT id FROM profiles WHERE game_name = %s",
            (profile_name,)
        )
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        profile_id = profile["id"]

        # ── Offline Stats ──
        cursor.execute(
            """SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                MAX(level) as highest_level,
                SUM(subs) as total_subs,
                AVG(response_time_avg) as avg_response_time
            FROM scores WHERE profile_id = %s AND mode = 'normal'""",
            (profile_id,)
        )
        offline = cursor.fetchone()

        offline_games = offline["total_games"] or 0
        offline_wins = offline["wins"] or 0
        offline_win_rate = (offline_wins / offline_games * 100) if offline_games > 0 else 0

        # ── Online Stats (Ranked) ──
        cursor.execute(
            """SELECT elo, games_played, games_won FROM elo_ratings 
               WHERE profile_id = %s""",
            (profile_id,)
        )
        ranked = cursor.fetchone()

        if ranked:
            ranked_elo = ranked["elo"]
            ranked_games = ranked["games_played"]
            ranked_wins = ranked["games_won"]
        else:
            ranked_elo = DEFAULT_ELO
            ranked_games = 0
            ranked_wins = 0

        ranked_win_rate = (ranked_wins / ranked_games * 100) if ranked_games > 0 else 0

        return ProfileStats(
            offline=OfflineStats(
                games_played=offline_games,
                games_won=offline_wins,
                win_rate=round(offline_win_rate, 2),
                highest_level=offline["highest_level"] or 0,
                total_subs_collected=offline["total_subs"] or 0,
                average_response_time=offline["avg_response_time"]
            ),
            online=OnlineStats(
                ranked_games_played=ranked_games,
                ranked_games_won=ranked_wins,
                ranked_win_rate=round(ranked_win_rate, 2),
                current_elo=ranked_elo,
                current_rank=RankInfo(**get_rank_display(ranked_elo)),
                highest_elo_reached=ranked_elo  # TODO: track max_elo in DB
            )
        )


@router.get("/{profile_name}/matches", response_model=List[MatchHistoryItem])
async def get_profile_match_history(
    profile_name: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Get ranked match history for a profile.
    """
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Find the profile
        cursor.execute(
            "SELECT id FROM profiles WHERE game_name = %s",
            (profile_name,)
        )
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        profile_id = profile["id"]

        # Get matches where this player participated
        cursor.execute(
            """SELECT 
                m.id,
                CASE 
                    WHEN m.winner_profile_id = %s THEN p2.game_name
                    ELSE p1.game_name
                END as opponent_name,
                CASE 
                    WHEN m.winner_profile_id = %s THEN er2.elo
                    ELSE er1.elo
                END as opponent_elo,
                CASE 
                    WHEN m.winner_profile_id = %s THEN 'win'
                    ELSE 'loss'
                END as result,
                CASE 
                    WHEN m.winner_profile_id = %s THEN 15
                    ELSE -15
                END as elo_change,
                m.created_at
            FROM matches m
            JOIN profiles p1 ON m.player1_id = p1.id
            JOIN profiles p2 ON m.player2_id = p2.id
            LEFT JOIN elo_ratings er1 ON p1.id = er1.profile_id
            LEFT JOIN elo_ratings er2 ON p2.id = er2.profile_id
            WHERE (m.player1_id = %s OR m.player2_id = %s)
            AND m.mode = 'ranked'
            ORDER BY m.created_at DESC
            LIMIT %s OFFSET %s""",
            (profile_id, profile_id, profile_id, profile_id, profile_id, profile_id, limit, offset)
        )
        matches = cursor.fetchall()

        return [
            MatchHistoryItem(
                match_id=m["id"],
                opponent_name=m["opponent_name"],
                opponent_elo=m["opponent_elo"] or DEFAULT_ELO,
                result=m["result"],
                elo_change=m["elo_change"],
                match_date=m["created_at"].isoformat(),
                duration_seconds=None
            )
            for m in matches
        ]


@router.get("/{profile_name}/ranked", response_model=RankedDetailResponse)
async def get_ranked_detail(
    profile_name: str,
    db: pymysql.Connection = Depends(get_db)
):
    """
    Get ranked leaderboard detail with focus on player, Grand-champions, and Champions.
    """
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Find the player's rank
        cursor.execute(
            """SELECT p.id, p.game_name, er.elo, er.games_played, er.games_won
            FROM profiles p
            JOIN elo_ratings er ON p.id = er.profile_id
            WHERE p.game_name = %s""",
            (profile_name,)
        )
        player = cursor.fetchone()

        player_rank = None
        if player:
            # Get rank position
            cursor.execute(
                "SELECT COUNT(*) as position FROM elo_ratings WHERE elo > %s",
                (player["elo"],)
            )
            position_result = cursor.fetchone()
            rank_pos = (position_result["position"] or 0) + 1

            win_rate = (player["games_won"] / player["games_played"] * 100) if player["games_played"] > 0 else 0
            rank_info = get_rank_display(player["elo"])

            player_rank = RankedLeaderboardEntry(
                rank=rank_pos,
                profile_name=profile_name,
                elo=player["elo"],
                games_played=player["games_played"],
                win_rate=round(win_rate, 2),
                rank_tier=rank_info["tier"],
                rank_division=rank_info["division"],
                rank_display=rank_info["display"]
            )

        # Get Grand-champions (highest ELO tier, top 5)
        cursor.execute(
            """SELECT ROW_NUMBER() OVER (ORDER BY er.elo DESC) as rank,
                p.game_name,
                er.elo,
                er.games_played,
                er.games_won
            FROM elo_ratings er
            JOIN profiles p ON er.profile_id = p.id
            WHERE er.elo >= 2400
            ORDER BY er.elo DESC
            LIMIT 5""",
        )
        grand_champs_raw = cursor.fetchall()

        grand_champs = []
        for g in grand_champs_raw:
            win_rate = (g["games_won"] / g["games_played"] * 100) if g["games_played"] > 0 else 0
            rank_info = get_rank_display(g["elo"])
            grand_champs.append(RankedLeaderboardEntry(
                rank=g["rank"],
                profile_name=g["game_name"],
                elo=g["elo"],
                games_played=g["games_played"],
                win_rate=round(win_rate, 2),
                rank_tier=rank_info["tier"],
                rank_division=rank_info["division"],
                rank_display=rank_info["display"]
            ))

        # Get Champions (tier, top 10)
        cursor.execute(
            """SELECT ROW_NUMBER() OVER (ORDER BY er.elo DESC) as rank,
                p.game_name,
                er.elo,
                er.games_played,
                er.games_won
            FROM elo_ratings er
            JOIN profiles p ON er.profile_id = p.id
            WHERE er.elo BETWEEN 2100 AND 2399
            ORDER BY er.elo DESC
            LIMIT 10""",
        )
        champs_raw = cursor.fetchall()

        champs = []
        for c in champs_raw:
            win_rate = (c["games_won"] / c["games_played"] * 100) if c["games_played"] > 0 else 0
            rank_info = get_rank_display(c["elo"])
            champs.append(RankedLeaderboardEntry(
                rank=c["rank"],
                profile_name=c["game_name"],
                elo=c["elo"],
                games_played=c["games_played"],
                win_rate=round(win_rate, 2),
                rank_tier=rank_info["tier"],
                rank_division=rank_info["division"],
                rank_display=rank_info["display"]
            ))

        return RankedDetailResponse(
            player_rank=player_rank,
            grand_champions=grand_champs,
            champions=champs
        )

