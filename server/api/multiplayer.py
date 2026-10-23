"""
server/api/multiplayer.py — Sub Ladder v4.0
Casual multiplayer matchmaking endpoints and WebSocket handler
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import json
import sys
import os
import asyncio
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from auth.dependencies import get_current_user
from websocket.matchmaking import (
    MatchmakingManager,
    get_matchmaking_manager,
    Player,
    MAX_ROOM_PLAYERS,
)
from game.multiplayer.ranked import new_ratings

router = APIRouter(tags=["multiplayer"])

# ══════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════

class RoomInfo(BaseModel):
    room_id: str
    creator_name: str
    room_name: str
    is_private: bool
    player_count: int
    max_players: int
    created_at: str


class PlayerStats(BaseModel):
    profile_id: int
    game_name: str
    elo: int


# ══════════════════════════════════════════════════════════════════
# REST ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@router.get("/api/multiplayer/queue-status", response_model=dict)
async def get_queue_status(manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())):
    """
    Get current matchmaking queue statistics.
    """
    return await manager.get_queue_status()


@router.get("/api/multiplayer/rooms", response_model=List[dict])
async def list_public_rooms(manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())):
    """
    Get list of public multiplayer rooms that aren't full.
    """
    rooms = await manager.get_public_rooms()
    return [room.to_dict() for room in rooms]


@router.get("/api/multiplayer/room/{room_id}", response_model=dict)
async def get_room_info(
    room_id: str,
    manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())
):
    """
    Get detailed info about a specific room.
    """
    room = await manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room.to_dict()


# ──────────────────────────────────────────────────────────────
# NORMAL MODE ENDPOINTS (distinct from casual rooms)
# ──────────────────────────────────────────────────────────────

class NormalTableCreate(BaseModel):
    table_name: str
    host_player: str
    password: Optional[str] = None
    max_players: int = 2


class NormalTableJoin(BaseModel):
    table_id: str
    player_name: str
    password: Optional[str] = None


class NormalTableRemove(BaseModel):
    table_id: str


class NormalTableStart(BaseModel):
    starter_player: str


class NormalTableReady(BaseModel):
    table_id: str
    player_name: str
    ready: bool = True


class NormalTableLeave(BaseModel):
    player_name: str


# In-memory store for Normal mode tables
_normal_tables: Dict[str, Dict[str, Any]] = {}
_normal_tables_lock = asyncio.Lock()


async def _normal_tables_snapshot() -> List[Dict[str, Any]]:
    async with _normal_tables_lock:
        return [dict(t) for t in _normal_tables.values()]


def _profile_id_from_name(player_name: str) -> int:
    """Create a stable pseudo profile id from player name for normal mode REST flows."""
    normalized = (player_name or "player").strip().lower().encode("utf-8")
    digest = hashlib.sha256(normalized).hexdigest()
    return int(digest[:12], 16)


@router.get("/api/multiplayer/normal-rooms", response_model=List[dict])
async def list_normal_rooms(manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())):
    """
    Get list of public Normal mode tables.
    Reuses the existing casual rooms endpoint for compatibility.
    """
    rooms = await manager.get_rooms_for_mode("normal", include_started=False)
    return [room.to_dict() for room in rooms]


@router.get("/api/multiplayer/normal-rooms/{table_id}", response_model=dict)
async def get_normal_room(
    table_id: str,
    manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())
):
    """Get details for one normal-mode room/table."""
    room = await manager.get_room(table_id)
    if not room or room.mode != "normal":
        raise HTTPException(status_code=404, detail="Room not found")
    return room.to_dict()


@router.post("/api/multiplayer/normal-rooms", response_model=dict)
async def create_normal_room(
    body: NormalTableCreate,
    manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())
):
    """
    Create a new Normal mode room (table).
    Mirrors NormalLobby.create_table on the client side.
    """
    if body.max_players not in (2, 3, 4):
        raise HTTPException(status_code=400, detail="max_players must be 2, 3, or 4")

    from datetime import datetime
    player = Player(
        profile_id=_profile_id_from_name(body.host_player),
        game_name=body.host_player,
        elo=1000,
        websocket=None,
        joined_at=datetime.now(),
    )
    try:
        room = await manager.create_room(
            player=player,
            room_name=body.table_name,
            is_private=bool(body.password),
            password=body.password,
            max_players=body.max_players,
            mode="normal",
        )
        return room.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/multiplayer/normal-rooms/{table_id}/join", response_model=dict)
async def join_normal_room(
    table_id: str,
    body: NormalTableJoin,
    manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())
):
    """
    Join an existing Normal mode room (table).
    Mirrors NormalLobby.join_table on the client side.
    """
    from datetime import datetime
    player = Player(
        profile_id=_profile_id_from_name(body.player_name),
        game_name=body.player_name,
        elo=1000,
        websocket=None,
        joined_at=datetime.now(),
    )
    try:
        room = await manager.join_room(player, table_id, body.password)
        if room.mode != "normal":
            raise HTTPException(status_code=400, detail="Room is not a normal table")
        return room.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/multiplayer/normal-rooms/{table_id}/start", response_model=dict)
async def start_normal_room(
    table_id: str,
    body: NormalTableStart,
    manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())
):
    """Start a normal-mode room when creator is ready."""
    starter_id = _profile_id_from_name(body.starter_player)
    try:
        room = await manager.start_room(table_id, starter_id)
        if room.mode != "normal":
            raise HTTPException(status_code=400, detail="Room is not a normal table")
        return room.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/multiplayer/normal-rooms/{table_id}/ready", response_model=dict)
async def set_normal_room_ready(
    table_id: str,
    body: NormalTableReady,
    manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())
):
    """Mark a player as ready or not ready in a normal-mode room."""
    profile_id = _profile_id_from_name(body.player_name)
    try:
        room = await manager.set_room_ready(table_id, profile_id, body.ready)
        if room.mode != "normal":
            raise HTTPException(status_code=400, detail="Room is not a normal table")
        return room.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/multiplayer/normal-rooms/{table_id}/leave", response_model=dict)
async def leave_normal_room(
    table_id: str,
    body: NormalTableLeave,
    manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())
):
    """Leave a normal-mode room without deleting it entirely."""
    room = await manager.get_room(table_id)
    if not room or room.mode != "normal":
        raise HTTPException(status_code=404, detail="Room not found")

    profile_id = _profile_id_from_name(body.player_name)
    await manager.leave_room(profile_id)

    updated = await manager.get_room(table_id)
    if not updated:
        return {"status": "removed", "table_id": table_id}
    return updated.to_dict()


@router.delete("/api/multiplayer/normal-rooms/{table_id}", response_model=dict)
async def remove_normal_room(
    table_id: str,
    manager: MatchmakingManager = Depends(lambda: get_matchmaking_manager())
):
    """Remove a Normal mode room (table)."""
    removed = await manager.remove_room(table_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"status": "removed", "table_id": table_id}


# ══════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINT
# ══════════════════════════════════════════════════════════════════

@router.websocket("/api/multiplayer/ws")
async def websocket_multiplayer(
    websocket: WebSocket,
    profile_id: int = Query(...),
    game_name: str = Query(...),
    elo: int = Query(1000),
    db = Depends(get_db)
):
    """
    WebSocket endpoint for casual multiplayer matchmaking.
    
    Query parameters:
    - profile_id: Player's profile ID
    - game_name: Player's game name
    - elo: Player's current ELO rating (default: 1000)
    """
    await websocket.accept()
    
    manager = get_matchmaking_manager()
    player = Player(
        profile_id=profile_id,
        game_name=game_name,
        elo=elo,
        websocket=websocket,
        joined_at=None
    )
    
    from datetime import datetime
    player.joined_at = datetime.now()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")
            
            # ──────────────────────────────────────────────────────
            # 1. JOIN RANDOM QUEUE (1v1)
            # ──────────────────────────────────────────────────────
            if action == "join_queue":
                try:
                    result = await manager.join_random_queue(player)
                    
                    if result["status"] == "match_found":
                        # Send to both players (need to handle via separate websockets)
                        await websocket.send_json({
                            "event": "match_found",
                            "match_id": result["match_id"],
                            "opponent": result["opponent"],
                            "created_at": result["created_at"],
                        })
                    else:
                        await websocket.send_json({
                            "event": "queue_joined",
                            "position": result.get("position", 1),
                            "estimated_wait_seconds": result.get("estimated_wait_seconds", 30),
                        })
                except Exception as e:
                    await websocket.send_json({"event": "error", "message": str(e)})
            
            # ──────────────────────────────────────────────────────
            # 2. LEAVE RANDOM QUEUE
            # ──────────────────────────────────────────────────────
            elif action == "leave_queue":
                try:
                    await manager.leave_random_queue(player.profile_id)
                    await websocket.send_json({"event": "queue_left"})
                except Exception as e:
                    await websocket.send_json({"event": "error", "message": str(e)})
            
            # ──────────────────────────────────────────────────────
            # 3. CREATE CUSTOM ROOM
            # ──────────────────────────────────────────────────────
            elif action == "create_room":
                try:
                    room_name = message.get("room_name", "Unnamed Room")
                    is_private = message.get("is_private", False)
                    password = message.get("password")
                    
                    if not room_name.strip():
                        await websocket.send_json({"event": "error", "message": "Room name cannot be empty"})
                        continue
                    
                    if is_private and not password:
                        await websocket.send_json({"event": "error", "message": "Private rooms must have a password"})
                        continue
                    
                    room = await manager.create_room(player, room_name, is_private, password)
                    await websocket.send_json({
                        "event": "room_created",
                        "room": room.to_dict(),
                    })
                except Exception as e:
                    await websocket.send_json({"event": "error", "message": str(e)})
            
            # ──────────────────────────────────────────────────────
            # 4. JOIN CUSTOM ROOM
            # ──────────────────────────────────────────────────────
            elif action == "join_room":
                try:
                    room_id = message.get("room_id")
                    password = message.get("password")
                    
                    if not room_id:
                        await websocket.send_json({"event": "error", "message": "room_id is required"})
                        continue
                    
                    room = await manager.join_room(player, room_id, password)
                    await websocket.send_json({
                        "event": "room_joined",
                        "room": room.to_dict(),
                    })
                except Exception as e:
                    await websocket.send_json({"event": "error", "message": str(e)})
            
            # ──────────────────────────────────────────────────────
            # 5. LEAVE CUSTOM ROOM
            # ──────────────────────────────────────────────────────
            elif action == "leave_room":
                try:
                    room_id = await manager.leave_room(player.profile_id)
                    await websocket.send_json({"event": "room_left"})
                except Exception as e:
                    await websocket.send_json({"event": "error", "message": str(e)})
            
            # ──────────────────────────────────────────────────────
            # 6. LIST PUBLIC ROOMS
            # ──────────────────────────────────────────────────────
            elif action == "list_rooms":
                try:
                    rooms = await manager.get_public_rooms()
                    await websocket.send_json({
                        "event": "rooms_list",
                        "rooms": [room.to_dict() for room in rooms],
                    })
                except Exception as e:
                    await websocket.send_json({"event": "error", "message": str(e)})
            
            # ──────────────────────────────────────────────────────
            # 7. GET QUEUE STATUS
            # ──────────────────────────────────────────────────────
            elif action == "queue_status":
                try:
                    status = await manager.get_queue_status()
                    await websocket.send_json({
                        "event": "queue_status",
                        **status,
                    })
                except Exception as e:
                    await websocket.send_json({"event": "error", "message": str(e)})
            
            # Unknown action
            else:
                await websocket.send_json({"event": "error", "message": f"Unknown action: {action}"})

            # START MATCH (triggered by one of the players once both ready)
            if action == "start_match":
                match_id = message.get("match_id")
                if not match_id:
                    await websocket.send_json({"event": "error", "message": "match_id is required for start_match"})
                    continue
                try:
                    await manager.start_match(match_id)
                except Exception as e:
                    await websocket.send_json({"event": "error", "message": str(e)})

            # SUBMIT MATCH RESULT
            if action == "submit_match_result":
                # Expected payload: {match_id, winner_profile_id, loser_profile_id, mode}
                match_id = message.get("match_id")
                winner_profile_id = message.get("winner_profile_id")
                loser_profile_id = message.get("loser_profile_id")
                mode = message.get("mode", "casual")

                if not match_id or not winner_profile_id or not loser_profile_id:
                    await websocket.send_json({"event": "error", "message": "match_id, winner_profile_id and loser_profile_id are required"})
                    continue

                # Broadcast match end to both players if we have the active match
                active = manager.active_matches.get(match_id)
                if active:
                    for p in active.get("players", []):
                        try:
                            await p.websocket.send_json({
                                "event": "match_ended",
                                "match_id": match_id,
                                "winner_profile_id": winner_profile_id,
                                "loser_profile_id": loser_profile_id,
                                "mode": mode,
                            })
                        except Exception:
                            pass

                # Persist result for ranked mode: update elo_ratings and insert match record
                if mode == "ranked":
                    try:
                        from datetime import datetime
                        now = datetime.now()
                        with db.cursor(pymysql.cursors.DictCursor) as cursor:
                            # Get current ELOs
                            cursor.execute("SELECT elo FROM elo_ratings WHERE profile_id = %s", (winner_profile_id,))
                            w_rec = cursor.fetchone()
                            winner_elo_before = w_rec["elo"] if w_rec else 1000

                            cursor.execute("SELECT elo FROM elo_ratings WHERE profile_id = %s", (loser_profile_id,))
                            l_rec = cursor.fetchone()
                            loser_elo_before = l_rec["elo"] if l_rec else 1000

                            winner_elo_after, loser_elo_after = new_ratings(winner_elo_before, loser_elo_before)

                            # Update winner record
                            cursor.execute(
                                """INSERT INTO elo_ratings (profile_id, elo, games_played, games_won, last_match_played) VALUES (%s, %s, 1, 1, %s)
                                   ON DUPLICATE KEY UPDATE elo = %s, games_played = games_played + 1, games_won = games_won + 1, last_match_played = %s""",
                                (winner_profile_id, winner_elo_after, now, winner_elo_after, now)
                            )

                            # Update loser record
                            cursor.execute(
                                """INSERT INTO elo_ratings (profile_id, elo, games_played, games_won, last_match_played) VALUES (%s, %s, 1, 0, %s)
                                   ON DUPLICATE KEY UPDATE elo = %s, games_played = games_played + 1, last_match_played = %s""",
                                (loser_profile_id, loser_elo_after, now, loser_elo_after, now)
                            )

                            # Record match
                            cursor.execute(
                                """INSERT INTO matches (room_id, player1_id, player2_id, winner_profile_id, mode, status, created_at)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                (match_id, winner_profile_id, loser_profile_id, winner_profile_id, "ranked", "finished", now)
                            )
                            db.commit()

                        await websocket.send_json({"event": "result_recorded", "match_id": match_id})
                    except Exception as e:
                        try:
                            db.rollback()
                        except:
                            pass
                        await websocket.send_json({"event": "error", "message": f"Failed to record ranked result: {e}"})
                else:
                    # Casual mode: record match simple entry
                    try:
                        from datetime import datetime
                        now = datetime.now()
                        with db.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO matches (room_id, player1_id, player2_id, winner_profile_id, mode, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                (match_id, winner_profile_id, loser_profile_id, winner_profile_id, "casual", "finished", now)
                            )
                            db.commit()
                        await websocket.send_json({"event": "result_recorded", "match_id": match_id})
                    except Exception as e:
                        try:
                            db.rollback()
                        except:
                            pass
                        await websocket.send_json({"event": "error", "message": f"Failed to record casual result: {e}"})
    
    except WebSocketDisconnect:
        # Clean up when player disconnects
        try:
            # Remove from queue if in queue
            await manager.leave_random_queue(player.profile_id)
            # Remove from room if in room
            await manager.leave_room(player.profile_id)
        except:
            pass
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        try:
            await websocket.send_json({"event": "error", "message": "Connection error"})
        except:
            pass
