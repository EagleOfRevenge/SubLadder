"""
Social graph services for friends, blocks, reports, presence, and notifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import pymysql
from fastapi import HTTPException, WebSocket

from .models import PlayerStatus


STATUS_BUCKET_ORDER = ["online", "ingame", "away", "offline"]

STATUS_BUCKETS = {
    PlayerStatus.ONLINE.value: "online",
    PlayerStatus.LOBBY.value: "online",
    PlayerStatus.LOOKING_FOR_MATCH.value: "online",
    PlayerStatus.MATCH_FOUND.value: "online",
    PlayerStatus.LOADING_GAME.value: "online",
    PlayerStatus.NORMAL_GAME.value: "ingame",
    PlayerStatus.RANKED_GAME.value: "ingame",
    PlayerStatus.TUTORIAL.value: "ingame",
    PlayerStatus.TRAINING.value: "ingame",
    PlayerStatus.CUSTOM_GAME.value: "ingame",
    PlayerStatus.AWAY.value: "away",
    PlayerStatus.OFFLINE.value: "offline",
}

STATUS_LABELS = {
    PlayerStatus.ONLINE.value: {"en": "Online", "fr": "En ligne"},
    PlayerStatus.LOBBY.value: {"en": "Lobby", "fr": "Lobby"},
    PlayerStatus.LOOKING_FOR_MATCH.value: {"en": "Looking for match", "fr": "Recherche"},
    PlayerStatus.MATCH_FOUND.value: {"en": "Match found", "fr": "Match trouvé"},
    PlayerStatus.LOADING_GAME.value: {"en": "Loading game", "fr": "Chargement"},
    PlayerStatus.NORMAL_GAME.value: {"en": "Normal game", "fr": "Partie normale"},
    PlayerStatus.RANKED_GAME.value: {"en": "Ranked game", "fr": "Partie classée"},
    PlayerStatus.TUTORIAL.value: {"en": "Tutorial", "fr": "Tutoriel"},
    PlayerStatus.TRAINING.value: {"en": "Training", "fr": "Entraînement"},
    PlayerStatus.CUSTOM_GAME.value: {"en": "Custom game", "fr": "Partie perso"},
    PlayerStatus.AWAY.value: {"en": "Away", "fr": "Absent"},
    PlayerStatus.OFFLINE.value: {"en": "Offline", "fr": "Hors ligne"},
}


@dataclass(frozen=True)
class ProfileIdentity:
    profile_id: int
    profile_name: str


class SocialEventHub:
    def __init__(self):
        self._clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self._clients.discard(websocket)

    async def broadcast(self, payload: dict[str, Any]):
        stale: list[WebSocket] = []
        for websocket in list(self._clients):
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)


SOCIAL_EVENT_HUB = SocialEventHub()


def bucket_for_status(status_name: Optional[str]) -> str:
    if not status_name:
        return "offline"
    return STATUS_BUCKETS.get(status_name, "offline")


def status_label(status_name: Optional[str], lang: str = "en") -> str:
    key = status_name or PlayerStatus.OFFLINE.value
    labels = STATUS_LABELS.get(key, STATUS_LABELS[PlayerStatus.OFFLINE.value])
    return labels.get(lang, labels["en"])


def _require_row(row: Optional[dict], message: str):
    if not row:
        raise HTTPException(status_code=404, detail=message)
    return row


def _resolve_profile_id(db: pymysql.Connection, profile_name: str) -> ProfileIdentity:
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT id, game_name FROM profiles WHERE game_name = %s",
            (profile_name,),
        )
        profile = cursor.fetchone()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    return ProfileIdentity(profile_id=profile["id"], profile_name=profile["game_name"])


def _resolve_current_identity(db: pymysql.Connection, current_user: dict) -> ProfileIdentity:
    profile_name = current_user.get("game_name")
    if not profile_name:
        raise HTTPException(status_code=401, detail="Profil utilisateur manquant")
    return _resolve_profile_id(db, profile_name)


def _pair_exists(db: pymysql.Connection, first_id: int, second_id: int) -> Optional[dict]:
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            """
            SELECT * FROM friends
            WHERE (player_id = %s AND friend_id = %s)
               OR (player_id = %s AND friend_id = %s)
            ORDER BY FIELD(status, 'accepted', 'pending', 'declined')
            LIMIT 1
            """,
            (first_id, second_id, second_id, first_id),
        )
        return cursor.fetchone()


class BlockService:
    def is_blocked(self, db: pymysql.Connection, blocker_id: int, blocked_id: int) -> bool:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM blocked_players WHERE blocker_id = %s AND blocked_id = %s",
                (blocker_id, blocked_id),
            )
            return cursor.fetchone() is not None

    def block_player(self, db: pymysql.Connection, blocker_id: int, blocked_id: int):
        if blocker_id == blocked_id:
            raise HTTPException(status_code=400, detail="Impossible de se bloquer soi-même")

        with db.cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO blocked_players (blocker_id, blocked_id) VALUES (%s, %s)",
                (blocker_id, blocked_id),
            )
            cursor.execute(
                "DELETE FROM friends WHERE (player_id = %s AND friend_id = %s) OR (player_id = %s AND friend_id = %s)",
                (blocker_id, blocked_id, blocked_id, blocker_id),
            )
            cursor.execute(
                "DELETE FROM friends WHERE (player_id = %s AND friend_id = %s) OR (player_id = %s AND friend_id = %s)",
                (blocked_id, blocker_id, blocker_id, blocked_id),
            )
        db.commit()

    def unblock_player(self, db: pymysql.Connection, blocker_id: int, blocked_id: int):
        with db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM blocked_players WHERE blocker_id = %s AND blocked_id = %s",
                (blocker_id, blocked_id),
            )
        db.commit()

    def list_blocked(self, db: pymysql.Connection, blocker_id: int) -> list[dict]:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT bp.blocked_id AS profile_id, p.game_name AS profile_name, p.current_status, bp.created_at
                FROM blocked_players bp
                JOIN profiles p ON p.id = bp.blocked_id
                WHERE bp.blocker_id = %s
                ORDER BY p.game_name ASC
                """,
                (blocker_id,),
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row["profile_id"],
                "name": row["profile_name"],
                "status": row.get("current_status") or PlayerStatus.OFFLINE.value,
                "bucket": bucket_for_status(row.get("current_status")),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
            }
            for row in rows
        ]


class PresenceService:
    def update_status(self, db: pymysql.Connection, profile_id: int, status_name: str, message: Optional[str] = None):
        with db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE profiles
                SET current_status = %s,
                    status_message = %s,
                    last_seen_at = NOW()
                WHERE id = %s
                """,
                (status_name, message, profile_id),
            )
        db.commit()

    def get_status(self, db: pymysql.Connection, profile_id: int) -> Optional[dict]:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT current_status, status_message, last_seen_at FROM profiles WHERE id = %s",
                (profile_id,),
            )
            return cursor.fetchone()


class FriendService:
    block_service = BlockService()

    def list_friends(self, db: pymysql.Connection, profile_id: int) -> list[dict]:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    f.friend_id AS profile_id,
                    p.game_name AS profile_name,
                    p.avatar,
                    p.current_status,
                    p.status_message,
                    p.last_seen_at,
                    f.created_at,
                    f.status,
                    COALESCE(er.games_played, 0) AS games_played,
                    COALESCE(er.elo, 0) AS elo
                FROM friends f
                JOIN profiles p ON p.id = f.friend_id
                LEFT JOIN elo_ratings er ON er.profile_id = p.id
                WHERE f.player_id = %s AND f.status = 'accepted'
                ORDER BY
                    CASE
                        WHEN p.current_status IN ('online', 'lobby', 'looking_for_match', 'match_found', 'loading_game') THEN 0
                        WHEN p.current_status IN ('normal_game', 'ranked_game', 'tutorial', 'training', 'custom_game') THEN 1
                        WHEN p.current_status = 'away' THEN 2
                        ELSE 3
                    END,
                    p.game_name ASC
                """,
                (profile_id,),
            )
            rows = cursor.fetchall()
        return [self._row_to_friend(row) for row in rows]

    def list_requests(self, db: pymysql.Connection, profile_id: int, direction: str) -> list[dict]:
        column = "friend_id" if direction == "incoming" else "player_id"
        source_column = "player_id" if direction == "incoming" else "friend_id"
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT
                    f.{source_column} AS profile_id,
                    p.game_name AS profile_name,
                    p.avatar,
                    p.current_status,
                    p.status_message,
                    f.created_at,
                    f.status
                FROM friends f
                JOIN profiles p ON p.id = f.{source_column}
                WHERE f.{column} = %s AND f.status = 'pending'
                ORDER BY f.created_at DESC
                """,
                (profile_id,),
            )
            rows = cursor.fetchall()
        return [self._row_to_friend(row) for row in rows]

    def send_request(self, db: pymysql.Connection, sender_id: int, target_id: int) -> dict:
        if sender_id == target_id:
            raise HTTPException(status_code=400, detail="Impossible d'ajouter son propre profil")
        if self.block_service.is_blocked(db, target_id, sender_id) or self.block_service.is_blocked(db, sender_id, target_id):
            raise HTTPException(status_code=403, detail="Demande d'ami bloquée")

        existing = _pair_exists(db, sender_id, target_id)
        if existing and existing["status"] == "accepted":
            raise HTTPException(status_code=409, detail="Déjà amis")
        if existing and existing["status"] == "pending" and existing["player_id"] == target_id:
            return self.accept_request(db, sender_id, target_id)
        if existing and existing["status"] == "pending" and existing["player_id"] == sender_id:
            raise HTTPException(status_code=409, detail="Demande déjà envoyée")

        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO friends (player_id, friend_id, status) VALUES (%s, %s, 'pending')",
                (sender_id, target_id),
            )
        db.commit()
        return {"status": "pending", "sender_id": sender_id, "target_id": target_id}

    def accept_request(self, db: pymysql.Connection, current_id: int, requestor_id: int) -> dict:
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE friends SET status = 'accepted' WHERE player_id = %s AND friend_id = %s AND status = 'pending'",
                (requestor_id, current_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Demande d'ami introuvable")
            cursor.execute(
                "INSERT INTO friends (player_id, friend_id, status) VALUES (%s, %s, 'accepted') ON DUPLICATE KEY UPDATE status = 'accepted'",
                (current_id, requestor_id),
            )
        db.commit()
        return {"status": "accepted", "requestor_id": requestor_id, "receiver_id": current_id}

    def decline_request(self, db: pymysql.Connection, current_id: int, requestor_id: int) -> dict:
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE friends SET status = 'declined' WHERE player_id = %s AND friend_id = %s AND status = 'pending'",
                (requestor_id, current_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Demande d'ami introuvable")
        db.commit()
        return {"status": "declined", "requestor_id": requestor_id, "receiver_id": current_id}

    def cancel_request(self, db: pymysql.Connection, sender_id: int, target_id: int) -> dict:
        with db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM friends WHERE player_id = %s AND friend_id = %s AND status = 'pending'",
                (sender_id, target_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Demande d'ami introuvable")
        db.commit()
        return {"status": "cancelled", "sender_id": sender_id, "target_id": target_id}

    def remove_friend(self, db: pymysql.Connection, first_id: int, second_id: int) -> dict:
        with db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM friends WHERE (player_id = %s AND friend_id = %s) OR (player_id = %s AND friend_id = %s)",
                (first_id, second_id, second_id, first_id),
            )
        db.commit()
        return {"status": "removed", "first_id": first_id, "second_id": second_id}

    def get_relationship(self, db: pymysql.Connection, first_id: int, second_id: int) -> Optional[dict]:
        return _pair_exists(db, first_id, second_id)

    def _row_to_friend(self, row: dict) -> dict:
        status_name = row.get("current_status") or PlayerStatus.OFFLINE.value
        return {
            "id": row.get("profile_id"),
            "name": row.get("profile_name"),
            "avatar": row.get("avatar"),
            "level": row.get("games_played", 0),
            "rank": f"ELO {row.get('elo', 0)}" if row.get("elo") is not None else "",
            "clan": row.get("clan", ""),
            "tag": row.get("tag", ""),
            "mode": status_label(status_name, "en"),
            "message": row.get("status_message") or "",
            "status": status_name,
            "bucket": bucket_for_status(status_name),
            "status_icon": self._status_icon(status_name),
            "status_label_en": status_label(status_name, "en"),
            "status_label_fr": status_label(status_name, "fr"),
            "notifications": 0,
            "unread": False,
            "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
        }

    def _status_icon(self, status_name: str) -> str:
        return {
            PlayerStatus.ONLINE.value: "🟢",
            PlayerStatus.LOBBY.value: "🔵",
            PlayerStatus.LOOKING_FOR_MATCH.value: "🔎",
            PlayerStatus.MATCH_FOUND.value: "⏳",
            PlayerStatus.LOADING_GAME.value: "⬇️",
            PlayerStatus.NORMAL_GAME.value: "🟠",
            PlayerStatus.RANKED_GAME.value: "🔴",
            PlayerStatus.TUTORIAL.value: "📘",
            PlayerStatus.TRAINING.value: "🧪",
            PlayerStatus.CUSTOM_GAME.value: "🧩",
            PlayerStatus.AWAY.value: "🟡",
        }.get(status_name, "⚫")


class ReportService:
    spam_cooldown = timedelta(hours=6)

    def create_report(self, db: pymysql.Connection, reporter_id: int, reported_id: int, reason: str, description: Optional[str] = None) -> dict:
        if reporter_id == reported_id:
            raise HTTPException(status_code=400, detail="Impossible de se signaler soi-même")

        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT created_at
                FROM player_reports
                WHERE reporter_id = %s AND reported_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (reporter_id, reported_id),
            )
            last_report = cursor.fetchone()
            if last_report and last_report.get("created_at"):
                elapsed = datetime.now() - last_report["created_at"]
                if elapsed < self.spam_cooldown:
                    raise HTTPException(status_code=429, detail="Report déjà envoyé récemment")
            cursor.execute(
                "INSERT INTO player_reports (reporter_id, reported_id, reason, description) VALUES (%s, %s, %s, %s)",
                (reporter_id, reported_id, reason, description),
            )
        db.commit()
        return {"status": "created", "reporter_id": reporter_id, "reported_id": reported_id}


class NotificationService:
    def badge_count(self, db: pymysql.Connection, profile_id: int) -> int:
        friend_service = FriendService()
        incoming = friend_service.list_requests(db, profile_id, "incoming")
        return len(incoming)


class ProfileService:
    friend_service = FriendService()
    block_service = BlockService()
    presence_service = PresenceService()
    notification_service = NotificationService()

    def get_snapshot(self, db: pymysql.Connection, profile_id: int) -> dict:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT id, game_name, avatar, current_status, status_message, last_seen_at, created_at FROM profiles WHERE id = %s",
                (profile_id,),
            )
            profile = _require_row(cursor.fetchone(), "Profil non trouvé")

        return {
            "profile": {
                "id": profile["id"],
                "name": profile["game_name"],
                "avatar": profile.get("avatar"),
                "status": profile.get("current_status") or PlayerStatus.OFFLINE.value,
                "status_message": profile.get("status_message"),
                "last_seen_at": profile.get("last_seen_at").isoformat() if profile.get("last_seen_at") else None,
                "created_at": profile.get("created_at").isoformat() if profile.get("created_at") else None,
            },
            "friends": self.friend_service.list_friends(db, profile_id),
            "incoming_requests": self.friend_service.list_requests(db, profile_id, "incoming"),
            "outgoing_requests": self.friend_service.list_requests(db, profile_id, "outgoing"),
            "blocked_players": self.block_service.list_blocked(db, profile_id),
            "notification_count": self.notification_service.badge_count(db, profile_id),
        }
