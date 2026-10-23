"""
server/websocket/matchmaking.py — Sub Ladder v4.0
Casual multiplayer matchmaking with two modes:
1. Random 1v1 mode with a waitlist
2. Custom room creation/joining (up to 4 players)
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════

MAX_ROOM_PLAYERS = 4  # Maximum players per custom room
ROOM_INACTIVITY_TIMEOUT = 300  # 5 minutes
WAITLIST_TIMEOUT = 600  # 10 minutes


# ══════════════════════════════════════════════════════════════════
# DATA MODELS
# ══════════════════════════════════════════════════════════════════

@dataclass
class Player:
    """Represents a player in the matchmaking system."""
    profile_id: int
    game_name: str
    elo: int
    websocket: Any
    joined_at: datetime
    
    def to_dict(self):
        return {
            "profile_id": self.profile_id,
            "game_name": self.game_name,
            "elo": self.elo,
        }


@dataclass
class Room:
    """Represents a custom multiplayer room."""
    room_id: str
    creator_id: int
    creator_name: str
    room_name: str
    is_private: bool
    password: Optional[str]
    players: List[Player]
    created_at: datetime
    max_players: int = MAX_ROOM_PLAYERS
    mode: str = "casual"  # "casual" for custom rooms
    status: str = "waiting"  # waiting -> started
    started_at: Optional[datetime] = None
    ready_players: Set[int] = field(default_factory=set)
    
    def is_full(self) -> bool:
        return len(self.players) >= self.max_players
    
    def is_expired(self) -> bool:
        return datetime.now() - self.created_at > timedelta(seconds=ROOM_INACTIVITY_TIMEOUT)
    
    def to_dict(self):
        return {
            "room_id": self.room_id,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "room_name": self.room_name,
            "is_private": self.is_private,
            "requires_password": self.is_private,
            "is_full": self.is_full(),
            "player_count": len(self.players),
            "max_players": self.max_players,
            "players": [p.to_dict() for p in self.players],
            "ready_player_ids": sorted(self.ready_players),
            "all_ready": bool(self.players) and all(p.profile_id in self.ready_players for p in self.players),
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "mode": self.mode,
        }


@dataclass
class WaitlistEntry:
    """Represents a player in the random 1v1 waitlist."""
    player: Player
    joined_at: datetime
    
    def is_expired(self) -> bool:
        return datetime.now() - self.joined_at > timedelta(seconds=WAITLIST_TIMEOUT)


# ══════════════════════════════════════════════════════════════════
# MATCHMAKING MANAGER
# ══════════════════════════════════════════════════════════════════

class MatchmakingManager:
    """Manages casual multiplayer matchmaking (random 1v1 and custom rooms)."""
    
    def __init__(self):
        # Random 1v1 waitlist
        self.waitlist: List[WaitlistEntry] = []
        
        # Custom rooms (room_id -> Room)
        self.rooms: Dict[str, Room] = {}
        
        # Player tracking (profile_id -> current activity)
        self.player_state: Dict[int, Dict[str, Any]] = {}
        # Active matches mapping: match_id -> {players: [Player, Player], created_at, status}
        self.active_matches: Dict[str, Dict[str, Any]] = {}
        
        self._lock = asyncio.Lock()

    def _player_room_id(self, profile_id: int) -> Optional[str]:
        state = self.player_state.get(profile_id)
        if state and state.get("mode") == "room":
            room_id = state.get("room_id")
            if room_id:
                return room_id
        return None
    
    async def join_random_queue(self, player: Player) -> Dict[str, Any]:
        """
        Add player to random 1v1 waitlist.
        Returns match info if pairing found, or queue status.
        """
        async with self._lock:
            # Check if player already in queue
            for entry in self.waitlist:
                if entry.player.profile_id == player.profile_id:
                    return {"status": "already_in_queue", "position": len(self.waitlist)}
            
            # Clean expired entries
            self.waitlist = [e for e in self.waitlist if not e.is_expired()]
            
            # Add player to waitlist
            entry = WaitlistEntry(player=player, joined_at=datetime.now())
            self.waitlist.append(entry)
            
            # Track player state
            self.player_state[player.profile_id] = {
                "mode": "random_queue",
                "joined_at": datetime.now(),
            }
            
            # Check if we can make a pair (2+ players in queue)
            if len(self.waitlist) >= 2:
                player1_entry = self.waitlist.pop(0)
                player2_entry = self.waitlist.pop(0)

                # Create temporary match room
                match_id = f"match_{uuid.uuid4().hex[:12]}"

                # Register active match
                self.active_matches[match_id] = {
                    "players": [player1_entry.player, player2_entry.player],
                    "created_at": datetime.now(),
                    "status": "waiting",  # waiting -> active -> finished
                }

                # Notify both players (if websocket still connected)
                try:
                    await player1_entry.player.websocket.send_json({
                        "event": "match_found",
                        "match_id": match_id,
                        "opponent": player2_entry.player.to_dict(),
                        "created_at": datetime.now().isoformat(),
                    })
                except Exception:
                    pass

                try:
                    await player2_entry.player.websocket.send_json({
                        "event": "match_found",
                        "match_id": match_id,
                        "opponent": player1_entry.player.to_dict(),
                        "created_at": datetime.now().isoformat(),
                    })
                except Exception:
                    pass

                return {
                    "status": "match_found",
                    "match_id": match_id,
                    "opponent": player2_entry.player.to_dict(),
                    "player1_id": player1_entry.player.profile_id,
                    "player2_id": player2_entry.player.profile_id,
                    "created_at": datetime.now().isoformat(),
                }
            
            return {
                "status": "queued",
                "position": len(self.waitlist),
                "estimated_wait_seconds": 30,
            }
    
    async def leave_random_queue(self, profile_id: int) -> bool:
        """Remove player from random 1v1 waitlist."""
        async with self._lock:
            self.waitlist = [e for e in self.waitlist if e.player.profile_id != profile_id]
            if profile_id in self.player_state:
                del self.player_state[profile_id]
            return True
    
    async def create_room(
        self,
        player: Player,
        room_name: str,
        is_private: bool = False,
        password: Optional[str] = None,
        max_players: int = MAX_ROOM_PLAYERS,
        mode: str = "casual",
    ) -> Room:
        """Create a new custom room."""
        async with self._lock:
            if self._player_room_id(player.profile_id):
                raise ValueError("Player already in another room")

            room_id = f"room_{uuid.uuid4().hex[:12]}"

            if max_players not in (2, 3, 4):
                raise ValueError("max_players must be 2, 3, or 4")
            
            # Validate private room has password
            if is_private and not password:
                raise ValueError("Private rooms must have a password")
            
            room = Room(
                room_id=room_id,
                creator_id=player.profile_id,
                creator_name=player.game_name,
                room_name=room_name,
                is_private=is_private,
                password=password,
                players=[player],
                created_at=datetime.now(),
                max_players=max_players,
                mode=mode,
            )
            
            self.rooms[room_id] = room
            
            # Track player state
            self.player_state[player.profile_id] = {
                "mode": "room",
                "room_id": room_id,
                "joined_at": datetime.now(),
            }
            
            return room
    
    async def join_room(
        self,
        player: Player,
        room_id: str,
        password: Optional[str] = None
    ) -> Room:
        """Join an existing custom room."""
        async with self._lock:
            if room_id not in self.rooms:
                raise ValueError(f"Room {room_id} not found")
            
            room = self.rooms[room_id]

            if room.status != "waiting":
                raise ValueError("Room already started")
            
            # Check if room is full
            if room.is_full():
                raise ValueError("Room is full")
            
            # Check password if room is private
            if room.is_private and password != room.password:
                raise ValueError("Invalid password")

            if self._player_room_id(player.profile_id):
                raise ValueError("Player already in another room")
            
            # Check if player is not already in a room
            
            # Add player to room
            room.players.append(player)
            
            # Track player state
            self.player_state[player.profile_id] = {
                "mode": "room",
                "room_id": room_id,
                "joined_at": datetime.now(),
            }
            
            return room

    async def set_room_ready(self, room_id: str, profile_id: int, ready: bool = True) -> Room:
        """Toggle a player's ready state in a room and auto-start when everyone is ready."""
        async with self._lock:
            if room_id not in self.rooms:
                raise ValueError("Room not found")

            room = self.rooms[room_id]
            if room.status != "waiting":
                raise ValueError("Room already started")

            player_ids = {player.profile_id for player in room.players}
            if profile_id not in player_ids:
                raise ValueError("Player is not in this room")

            if ready:
                room.ready_players.add(profile_id)
            else:
                room.ready_players.discard(profile_id)

            if len(room.players) >= 2 and player_ids.issubset(room.ready_players):
                room.status = "started"
                room.started_at = datetime.now()

            return room

    async def start_room(self, room_id: str, starter_profile_id: int) -> Room:
        """Mark a custom room as started when creator launches the game."""
        async with self._lock:
            if room_id not in self.rooms:
                raise ValueError("Room not found")

            room = self.rooms[room_id]

            if room.creator_id != starter_profile_id:
                raise ValueError("Only the room creator can start this table")

            if room.status != "waiting":
                raise ValueError("Room already started")

            if len(room.players) < 2:
                raise ValueError("At least 2 players are required to start")

            player_ids = {player.profile_id for player in room.players}
            if not player_ids.issubset(room.ready_players):
                raise ValueError("All players must be ready")

            room.status = "started"
            room.started_at = datetime.now()
            return room
    
    async def leave_room(self, profile_id: int) -> Optional[str]:
        """
        Remove player from custom room.
        Returns room_id if room still exists, None if room was deleted.
        """
        async with self._lock:
            if profile_id not in self.player_state:
                return None
            
            state = self.player_state[profile_id]
            if state.get("mode") != "room":
                return None
            
            room_id = state.get("room_id")
            if not room_id or room_id not in self.rooms:
                del self.player_state[profile_id]
                return None
            
            room = self.rooms[room_id]
            room.players = [p for p in room.players if p.profile_id != profile_id]
            room.ready_players.discard(profile_id)
            
            # Delete room if empty or only creator remains
            if len(room.players) == 0 or (len(room.players) == 1 and room.players[0].profile_id == room.creator_id):
                del self.rooms[room_id]
                del self.player_state[profile_id]
                return None
            
            # If creator left, transfer to first player
            if profile_id == room.creator_id and room.players:
                new_creator = room.players[0]
                room.creator_id = new_creator.profile_id
                room.creator_name = new_creator.game_name
            
            del self.player_state[profile_id]
            return room_id

    async def remove_room(self, room_id: str) -> bool:
        """Remove a room entirely, cleaning up any tracked players."""
        async with self._lock:
            room = self.rooms.pop(room_id, None)
            if room is None:
                return False

            for player in room.players:
                self.player_state.pop(player.profile_id, None)
            return True
    
    async def get_room(self, room_id: str) -> Optional[Room]:
        """Get room info."""
        async with self._lock:
            return self.rooms.get(room_id)

    async def start_match(self, match_id: str) -> bool:
        """Mark a match as active and broadcast game_start to both players."""
        async with self._lock:
            match = self.active_matches.get(match_id)
            if not match:
                return False

            if match.get("status") == "active":
                return True

            match["status"] = "active"
            players = match.get("players", [])

            payload = {
                "event": "game_start",
                "match_id": match_id,
                "timestamp": datetime.now().isoformat(),
            }

            # Broadcast to players
            for p in players:
                try:
                    await p.websocket.send_json(payload)
                except Exception:
                    pass

            return True
    
    async def get_public_rooms(self) -> List[Room]:
        """Get all public (non-private) rooms that aren't full."""
        async with self._lock:
            # Clean expired rooms
            expired = [rid for rid, room in self.rooms.items() if room.is_expired()]
            for rid in expired:
                del self.rooms[rid]
            
            return [
                room for room in self.rooms.values()
                if not room.is_private and not room.is_full() and not room.is_expired()
            ]

    async def get_rooms_for_mode(self, mode: str, include_started: bool = False) -> List[Room]:
        """List rooms for a specific mode, including private ones when needed."""
        async with self._lock:
            expired = [rid for rid, room in self.rooms.items() if room.is_expired()]
            for rid in expired:
                del self.rooms[rid]

            rooms = [room for room in self.rooms.values() if room.mode == mode and not room.is_expired()]
            if include_started:
                return rooms
            return [room for room in rooms if room.status == "waiting"]
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue statistics."""
        async with self._lock:
            # Clean expired entries
            self.waitlist = [e for e in self.waitlist if not e.is_expired()]
            
            return {
                "queue_size": len(self.waitlist),
                "active_rooms": len(self.rooms),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def cleanup(self):
        """Clean up expired entries and rooms (call periodically)."""
        async with self._lock:
            # Remove expired waitlist entries
            self.waitlist = [e for e in self.waitlist if not e.is_expired()]
            
            # Remove expired rooms
            expired_rooms = [rid for rid, room in self.rooms.items() if room.is_expired()]
            for rid in expired_rooms:
                # Remove players from room from player_state
                for player in self.rooms[rid].players:
                    if player.profile_id in self.player_state:
                        del self.player_state[player.profile_id]
                del self.rooms[rid]


# ══════════════════════════════════════════════════════════════════
# MESSAGE PROTOCOL
# ══════════════════════════════════════════════════════════════════

"""
WebSocket Message Format:

CLIENT -> SERVER:
1. Join random queue:
   {
     "action": "join_queue"
   }

2. Leave random queue:
   {
     "action": "leave_queue"
   }

3. Create custom room:
   {
     "action": "create_room",
     "room_name": "My Room",
     "is_private": false,
     "password": null
   }

4. Join custom room:
   {
     "action": "join_room",
     "room_id": "room_...",
     "password": null
   }

5. Leave custom room:
   {
     "action": "leave_room"
   }

6. Get public rooms list:
   {
     "action": "list_rooms"
   }

SERVER -> CLIENT:
1. Queue joined:
   {
     "event": "queue_joined",
     "position": 1,
     "estimated_wait_seconds": 30
   }

2. Match found:
   {
     "event": "match_found",
     "match_id": "match_...",
     "opponent": { "profile_id": 123, "game_name": "Player", "elo": 1000 },
     "created_at": "2026-05-26T..."
   }

3. Room created:
   {
     "event": "room_created",
     "room": { ... }
   }

4. Player joined room:
   {
     "event": "player_joined_room",
     "player": { "profile_id": 123, "game_name": "Player", "elo": 1000 },
     "room": { ... }
   }

5. Player left room:
   {
     "event": "player_left_room",
     "profile_id": 123,
     "room": { ... }
   }

6. Public rooms list:
   {
     "event": "rooms_list",
     "rooms": [ ... ]
   }

7. Error:
   {
     "event": "error",
     "message": "Error description"
   }
"""


# Global matchmaking manager instance
_manager: Optional[MatchmakingManager] = None


def get_matchmaking_manager() -> MatchmakingManager:
    """Get or create the global matchmaking manager."""
    global _manager
    if _manager is None:
        _manager = MatchmakingManager()
    return _manager
