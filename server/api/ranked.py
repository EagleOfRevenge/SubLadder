# ═══════════════════════════════════════════════════════════════
# Sub Ladder v6.0 — Ranked API
# Ranked matchmaking, ELO progression, and leaderboards
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import pymysql
import sys
import os
import asyncio
import uuid
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from auth.dependencies import get_current_user
from game.multiplayer.ranked import (
    get_rank_display,
    get_progression_to_next_rank,
    new_ratings,
    is_valid_opponent,
    is_subject_to_decay,
    decay_days_needed,
    DEFAULT_ELO,
)

router = APIRouter(prefix="/ranked", tags=["ranked"])


class RankedQueueEntry:
    def __init__(self, profile_id: int, profile_name: str, elo: int, created_at: datetime):
        self.profile_id = profile_id
        self.profile_name = profile_name
        self.elo = elo
        self.created_at = created_at


_ranked_queue: List[RankedQueueEntry] = []
_ranked_queue_lock = asyncio.Lock()


async def _clean_ranked_queue() -> None:
    global _ranked_queue
    now = datetime.now()
    _ranked_queue = [entry for entry in _ranked_queue if now - entry.created_at < timedelta(seconds=90)]


async def _find_ranked_opponent(profile_id: int, elo: int, preferred_range: int, min_games_played: int) -> Optional[Dict[str, Any]]:
    await _clean_ranked_queue()
    async with _ranked_queue_lock:
        for index, entry in enumerate(_ranked_queue):
            if entry.profile_id == profile_id:
                continue
            if entry.elo < elo - preferred_range or entry.elo > elo + preferred_range:
                continue
            if min_games_played and 0 < min_games_played:
                pass
            _ranked_queue.pop(index)
            return {
                "profile_id": entry.profile_id,
                "profile_name": entry.profile_name,
                "elo": entry.elo,
                "rank": get_rank_display(entry.elo),
            }
    return None


async def _enqueue_ranked_player(profile_id: int, profile_name: str, elo: int) -> Dict[str, Any]:
    await _clean_ranked_queue()
    async with _ranked_queue_lock:
        for entry in _ranked_queue:
            if entry.profile_id == profile_id:
                return {"status": "queued", "position": 1, "message": "Already queued"}
        _ranked_queue.append(RankedQueueEntry(profile_id, profile_name, elo, datetime.now()))
        return {"status": "queued", "position": len(_ranked_queue), "message": "Waiting for an opponent"}


async def _dequeue_ranked_player(profile_id: int) -> None:
    async with _ranked_queue_lock:
        global _ranked_queue
        _ranked_queue = [entry for entry in _ranked_queue if entry.profile_id != profile_id]

# ══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════

class RankInfo(BaseModel):
    tier: str
    division: Optional[int]
    elo: int
    display: str
    icon: str

class RankProgression(BaseModel):
    current: str
    next: Optional[str]
    current_elo: int
    elo_to_next: Optional[int]
    progress_percent: float

class PlayerRankedStats(BaseModel):
    profile_name: str
    elo: int
    games_played: int
    games_won: int
    win_rate: float
    current_rank: RankInfo
    progression_to_next: RankProgression
    decay_days: Optional[int] = None
    is_decaying: bool = False

class RankedMatchResult(BaseModel):
    match_id: int
    winner_id: int
    loser_id: int
    winner_elo_before: int
    winner_elo_after: int
    loser_elo_before: int
    loser_elo_after: int
    elo_change_winner: int
    elo_change_loser: int

class SeasonRewardTier(BaseModel):
    tier: str
    min_elo: int
    max_elo: Optional[int]
    reward_name: str
    reward_description: str

class SeasonPlacementInfo(BaseModel):
    profile_name: str
    elo: int
    rank_position: int
    reward_category: Optional[str]
    reward_description: Optional[str]

class SeasonDetails(BaseModel):
    year: int
    name: str
    start_date: str
    end_date: str
    placements: List[SeasonPlacementInfo]

class MatchmakingRequest(BaseModel):
    """Request to find a ranked match."""
    preferred_elo_range: int = Field(
        200,
        ge=0,
        le=1000,
        description="Plage ELO autour du joueur pour trouver un adversaire"
    )
    min_games_played: int = Field(
        5,
        ge=0,
        description="Nombre minimum de parties classées jouées pour un adversaire"
    )

class MatchmakingQueue(BaseModel):
    message: str
    estimated_wait_seconds: Optional[int]
    queue_position: int

# ══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@router.get("/profile/{profile_name}/stats", response_model=PlayerRankedStats)
async def get_ranked_stats(
    profile_name: str,
    db: pymysql.Connection = Depends(get_db)
):
    """
    Get ranked statistics for a player.
    Returns current rank, ELO, win rate, progression info, and decay status.
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

        # Get or create ELO rating
        cursor.execute(
            "SELECT elo, games_played, games_won, decay_days FROM elo_ratings WHERE profile_id = %s",
            (profile_id,)
        )
        elo_record = cursor.fetchone()

        if not elo_record:
            # Create initial ELO record
            cursor.execute(
                """INSERT INTO elo_ratings 
                   (profile_id, elo, games_played, games_won, decay_days)
                   VALUES (%s, %s, 0, 0, 21)""",
                (profile_id, DEFAULT_ELO)
            )
            db.commit()
            elo = DEFAULT_ELO
            games_played = 0
            games_won = 0
            decay_days = 21
        else:
            elo = elo_record["elo"]
            games_played = elo_record["games_played"]
            games_won = elo_record["games_won"]
            decay_days = elo_record["decay_days"]

        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        is_decaying = is_subject_to_decay(elo)
        
        # Only show decay days for Champions and above
        display_decay_days = decay_days if is_decaying else None

        return PlayerRankedStats(
            profile_name=profile_name,
            elo=elo,
            games_played=games_played,
            games_won=games_won,
            win_rate=round(win_rate, 2),
            current_rank=RankInfo(**get_rank_display(elo)),
            progression_to_next=RankProgression(**get_progression_to_next_rank(elo)),
            decay_days=display_decay_days,
            is_decaying=is_decaying,
        )

@router.get("/leaderboard", tags=["leaderboards"])
async def get_ranked_leaderboard(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: pymysql.Connection = Depends(get_db)
):
    """
    Get global ranked leaderboard sorted by ELO rating.
    """
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Count total players
        cursor.execute("SELECT COUNT(*) as total FROM elo_ratings WHERE games_played > 0")
        total_result = cursor.fetchone()
        total = total_result["total"] if total_result else 0

        # Get top players
        cursor.execute(
            """SELECT
                p.game_name,
                u.discord_username,
                u.steam_id,
                er.elo,
                er.games_played,
                er.games_won,
                ROUND(er.games_won / er.games_played * 100, 2) as win_rate
            FROM elo_ratings er
            JOIN profiles p ON er.profile_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE er.games_played > 0
            ORDER BY er.elo DESC
            LIMIT %s OFFSET %s""",
            (limit, offset)
        )
        results = cursor.fetchall()

        # Add rank info to each player
        leaderboard = []
        for rank, player in enumerate(results, start=offset + 1):
            rank_info = get_rank_display(player["elo"])
            leaderboard.append({
                "rank": rank,
                **player,
                "rank_tier": rank_info["tier"],
                "rank_division": rank_info["division"],
                "rank_display": rank_info["display"],
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "leaderboard": leaderboard,
        }

@router.post("/match/result")
async def submit_match_result(
    winner_profile_id: int,
    loser_profile_id: int,
    db: pymysql.Connection = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Submit the result of a ranked match.
    Updates ELO ratings for both players and handles decay system.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié")

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Get current ELO ratings and decay info
        cursor.execute(
            "SELECT elo, decay_days FROM elo_ratings WHERE profile_id = %s",
            (winner_profile_id,)
        )
        winner_elo_record = cursor.fetchone()
        winner_elo_before = winner_elo_record["elo"] if winner_elo_record else DEFAULT_ELO
        winner_decay_before = winner_elo_record["decay_days"] if winner_elo_record else 21

        cursor.execute(
            "SELECT elo, decay_days FROM elo_ratings WHERE profile_id = %s",
            (loser_profile_id,)
        )
        loser_elo_record = cursor.fetchone()
        loser_elo_before = loser_elo_record["elo"] if loser_elo_record else DEFAULT_ELO
        loser_decay_before = loser_elo_record["decay_days"] if loser_elo_record else 21

        # Calculate new ratings
        winner_elo_after, loser_elo_after = new_ratings(winner_elo_before, loser_elo_before)
        elo_change_winner = winner_elo_after - winner_elo_before
        elo_change_loser = loser_elo_after - loser_elo_before

        # For both players, if they are subject to decay after the match, give +1 day (max 21)
        if is_subject_to_decay(winner_elo_after):
            if not is_subject_to_decay(winner_elo_before):
                # Just crossed into champion range
                winner_decay_after = 21
            else:
                winner_decay_after = min(winner_decay_before + 1, 21)
        else:
            winner_decay_after = 21

        if is_subject_to_decay(loser_elo_after):
            if not is_subject_to_decay(loser_elo_before):
                loser_decay_after = 21
            else:
                loser_decay_after = min(loser_decay_before + 1, 21)
        else:
            loser_decay_after = loser_decay_before

        now = datetime.now()

        # Update winner
        cursor.execute(
            """INSERT INTO elo_ratings 
               (profile_id, elo, games_played, games_won, decay_days, last_match_played)
               VALUES (%s, %s, 1, 1, %s, %s)
               ON DUPLICATE KEY UPDATE
                   elo = %s,
                   games_played = games_played + 1,
                   games_won = games_won + 1,
                   decay_days = %s,
                   last_match_played = %s""",
            (winner_profile_id, winner_elo_after, winner_decay_after, now,
             winner_elo_after, winner_decay_after, now)
        )

        # Update loser
        cursor.execute(
            """INSERT INTO elo_ratings 
               (profile_id, elo, games_played, games_won, decay_days, last_match_played)
               VALUES (%s, %s, 1, 0, %s, %s)
               ON DUPLICATE KEY UPDATE
                   elo = %s,
                   games_played = games_played + 1,
                   decay_days = %s,
                   last_match_played = %s""",
            (loser_profile_id, loser_elo_after, loser_decay_after, now,
             loser_elo_after, loser_decay_after, now)
        )

        # Record match result
        cursor.execute(
            """INSERT INTO matches (room_id, player1_id, player2_id, winner_profile_id, mode, status)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                f"ranked_{winner_profile_id}_{loser_profile_id}_{int(now.timestamp())}",
                winner_profile_id,
                loser_profile_id,
                winner_profile_id,
                "ranked",
                "finished"
            )
        )
        db.commit()
        match_id = cursor.lastrowid

        return RankedMatchResult(
            match_id=match_id,
            winner_id=winner_profile_id,
            loser_id=loser_profile_id,
            winner_elo_before=winner_elo_before,
            winner_elo_after=winner_elo_after,
            loser_elo_before=loser_elo_before,
            loser_elo_after=loser_elo_after,
            elo_change_winner=elo_change_winner,
            elo_change_loser=elo_change_loser,
        )

@router.post("/matchmaking/find")
async def find_ranked_match(
    request: Optional[MatchmakingRequest] = Body(default=None),
    db: pymysql.Connection = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Search for a ranked opponent.
    Returns either a match found immediately or a queue status.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié")

    profile_name = user.get("game_name", "default")
    preferred_range = request.preferred_elo_range if request else 200
    min_games_played = request.min_games_played if request else 5

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT id FROM profiles WHERE user_id = %s AND game_name = %s",
            (user["user_id"], profile_name)
        )
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")

        profile_id = profile["id"]

        cursor.execute(
            "SELECT elo FROM elo_ratings WHERE profile_id = %s",
            (profile_id,)
        )
        elo_record = cursor.fetchone()
        player_elo = elo_record["elo"] if elo_record else DEFAULT_ELO

    opponent = await _find_ranked_opponent(profile_id, player_elo, preferred_range, min_games_played)
    if opponent:
        return {
            "status": "match_found",
            "match_id": f"ranked_{uuid.uuid4().hex[:10]}",
            "opponent": {
                "profile_id": opponent["profile_id"],
                "profile_name": opponent["profile_name"],
                "elo": opponent["elo"],
                "rank": opponent["rank"],
            },
            "your_elo": player_elo,
            "your_rank": get_rank_display(player_elo),
        }

    queue_result = await _enqueue_ranked_player(profile_id, profile_name, player_elo)
    return {
        "status": "queued",
        "message": queue_result["message"],
        "position": queue_result["position"],
        "your_elo": player_elo,
        "your_rank": get_rank_display(player_elo),
        "elo_range": f"{player_elo - preferred_range} - {player_elo + preferred_range}",
    }


@router.post("/matchmaking/leave")
async def leave_ranked_matchmaking(user = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié")

    profile_name = user.get("game_name", "default")
    with get_db().__enter__().cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id FROM profiles WHERE user_id = %s AND game_name = %s", (user["user_id"], profile_name))
        profile = cursor.fetchone()
        if profile:
            await _dequeue_ranked_player(profile["id"])
    return {"status": "left"}

@router.get("/season/{year}/rewards", response_model=List[SeasonRewardTier])
async def get_season_reward_schedule(year: int):
    """Return the standard reward schedule for a ranked season."""
    return [
        SeasonRewardTier(tier="Grand Champion", min_elo=2500, max_elo=None, reward_name="Ruby Crown", reward_description="Top-tier season reward for Grand Champion placement."),
        SeasonRewardTier(tier="Champion", min_elo=2400, max_elo=2499, reward_name="Champion Emblem", reward_description="High-tier reward for Champion-ranked players."),
        SeasonRewardTier(tier="Diamond", min_elo=2100, max_elo=2399, reward_name="Diamond Banner", reward_description="Reward for Diamond-ranked players."),
        SeasonRewardTier(tier="Platinum", min_elo=1800, max_elo=2099, reward_name="Platinum Medal", reward_description="Reward for Platinum-ranked players."),
        SeasonRewardTier(tier="Gold", min_elo=1500, max_elo=1799, reward_name="Gold Trophy", reward_description="Reward for Gold-ranked players."),
        SeasonRewardTier(tier="Silver", min_elo=1200, max_elo=1499, reward_name="Silver Shield", reward_description="Reward for Silver-ranked players."),
        SeasonRewardTier(tier="Bronze", min_elo=0, max_elo=1199, reward_name="Bronze Badge", reward_description="Reward for Bronze-ranked players."),
    ]

@router.get("/season/{year}/placement/{profile_name}", response_model=SeasonDetails)
async def get_season_placement(year: int, profile_name: str, db: pymysql.Connection = Depends(get_db)):
    """Fetch season placement and reward info for a given profile."""
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id, name, start_date, end_date FROM seasons WHERE year = %s", (year,))
        season = cursor.fetchone()
        if not season:
            raise HTTPException(status_code=404, detail="Saison introuvable")

        cursor.execute("SELECT id FROM profiles WHERE game_name = %s", (profile_name,))
        profile = cursor.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil introuvable")

        cursor.execute(
            "SELECT elo, rank_position, reward_category, reward_description FROM season_placements WHERE season_id = %s AND profile_id = %s",
            (season["id"], profile["id"])
        )
        placement = cursor.fetchone()
        if not placement:
            raise HTTPException(status_code=404, detail="Placement de saison introuvable")

        return SeasonDetails(
            year=year,
            name=season["name"],
            start_date=str(season["start_date"]),
            end_date=str(season["end_date"]),
            placements=[SeasonPlacementInfo(
                profile_name=profile_name,
                elo=placement["elo"],
                rank_position=placement["rank_position"],
                reward_category=placement["reward_category"],
                reward_description=placement["reward_description"],
            )],
        )

@router.get("/season/current", response_model=SeasonDetails)
async def get_current_season(db: pymysql.Connection = Depends(get_db)):
    """Fetch the active ranked season details and top placements for the current year."""
    from datetime import datetime
    current_year = datetime.now().year

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id, name, start_date, end_date FROM seasons WHERE year = %s", (current_year,))
        season = cursor.fetchone()
        if not season:
            season_name = f"Saison {current_year}"
            start_date = f"{current_year}-01-01"
            end_date = f"{current_year}-12-31"
            cursor.execute(
                "INSERT INTO seasons (name, year, start_date, end_date) VALUES (%s, %s, %s, %s)",
                (season_name, current_year, start_date, end_date)
            )
            db.commit()
            season = {
                "id": cursor.lastrowid,
                "name": season_name,
                "start_date": start_date,
                "end_date": end_date,
            }

        cursor.execute(
            "SELECT sp.rank_position, sp.elo, sp.reward_category, sp.reward_description, p.game_name "
            "FROM season_placements sp "
            "JOIN profiles p ON sp.profile_id = p.id "
            "WHERE sp.season_id = %s "
            "ORDER BY sp.rank_position ASC "
            "LIMIT 100",
            (season["id"],)
        )
        placements = cursor.fetchall()

    return SeasonDetails(
        year=current_year,
        name=season["name"],
        start_date=str(season["start_date"]),
        end_date=str(season["end_date"]),
        placements=[
            SeasonPlacementInfo(
                profile_name=row["game_name"],
                elo=row["elo"],
                rank_position=row["rank_position"],
                reward_category=row["reward_category"],
                reward_description=row["reward_description"],
            )
            for row in placements
        ],
    )

@router.get("/top-100")
async def get_top_100_players(
    db: pymysql.Connection = Depends(get_db)
):
    """Get the top 100 ranked players globally."""
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            """SELECT
                ROW_NUMBER() OVER (ORDER BY er.elo DESC) as rank,
                p.game_name,
                u.discord_username,
                er.elo,
                er.games_played,
                er.games_won,
                ROUND(er.games_won / er.games_played * 100, 2) as win_rate
            FROM elo_ratings er
            JOIN profiles p ON er.profile_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE er.games_played > 0
            ORDER BY er.elo DESC
            LIMIT 100""",
        )
        results = cursor.fetchall()

        top_100 = []
        for player in results:
            rank_info = get_rank_display(player["elo"])
            top_100.append({
                **player,
                "rank_tier": rank_info["tier"],
                "rank_division": rank_info["division"],
                "rank_display": rank_info["display"],
            })

        return {"count": len(top_100), "players": top_100}

@router.get("/comparison/{profile_name_1}/{profile_name_2}")
async def compare_players(
    profile_name_1: str,
    profile_name_2: str,
    db: pymysql.Connection = Depends(get_db),
):
    """Compare two players' ranked stats."""
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Get both players' stats
        comparison = {}
        
        for profile_name in [profile_name_1, profile_name_2]:
            cursor.execute(
                "SELECT id FROM profiles WHERE game_name = %s",
                (profile_name,)
            )
            profile = cursor.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail=f"Profil {profile_name} non trouvé")

            cursor.execute(
                "SELECT elo, games_played, games_won FROM elo_ratings WHERE profile_id = %s",
                (profile["id"],)
            )
            elo_record = cursor.fetchone()
            
            if elo_record:
                elo = elo_record["elo"]
                games_played = elo_record["games_played"]
                games_won = elo_record["games_won"]
            else:
                elo = DEFAULT_ELO
                games_played = 0
                games_won = 0

            win_rate = (games_won / games_played * 100) if games_played > 0 else 0
            
            comparison[profile_name] = {
                "elo": elo,
                "games_played": games_played,
                "games_won": games_won,
                "win_rate": round(win_rate, 2),
                "rank": get_rank_display(elo),
            }

        return {
            "player_1": profile_name_1,
            "player_2": profile_name_2,
            "stats": comparison,
            "elo_difference": abs(comparison[profile_name_1]["elo"] - comparison[profile_name_2]["elo"]),
        }
