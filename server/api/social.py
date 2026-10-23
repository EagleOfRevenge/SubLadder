"""
Sub Ladder v4.0 — Social API
Friends, presence, blocks, reports, and social snapshot endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from typing import Any
import pymysql
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from auth.dependencies import get_current_user
from social import (
    SOCIAL_EVENT_HUB,
    BlockRequest,
    FriendRequestAction,
    FriendRequestCreate,
    FriendService,
    PlayerStatus,
    PresenceUpdate,
    ProfileService,
    ReportRequest,
    ReportService,
    BlockService,
    PresenceService,
    bucket_for_status,
)

router = APIRouter(prefix="/social", tags=["social"])

friend_service = FriendService()
block_service = BlockService()
presence_service = PresenceService()
report_service = ReportService()
profile_service = ProfileService()


def _validate_profile_name(profile_name: str) -> str:
    if not isinstance(profile_name, str):
        raise HTTPException(status_code=422, detail="Nom de profil invalide")
    if not re.fullmatch(r"[A-Za-z0-9_\-]{3,32}", profile_name):
        raise HTTPException(status_code=422, detail="Nom de profil invalide")
    return profile_name


def _current_profile_identity(db: pymysql.Connection, current_user: dict) -> tuple[int, str]:
    profile_name = current_user.get("game_name")
    if not profile_name:
        raise HTTPException(status_code=401, detail="Profil utilisateur manquant")
    profile_name = _validate_profile_name(profile_name)
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id, game_name FROM profiles WHERE game_name = %s", (profile_name,))
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    return int(row["id"]), row["game_name"]


@router.get("/me")
async def get_my_social_snapshot(
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile_id, _ = _current_profile_identity(db, current_user)
    return profile_service.get_snapshot(db, profile_id)


@router.get("/friends")
async def list_friends(
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile_id, _ = _current_profile_identity(db, current_user)
    return {"friends": friend_service.list_friends(db, profile_id)}


@router.get("/requests/incoming")
async def list_incoming_requests(
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile_id, _ = _current_profile_identity(db, current_user)
    return {"requests": friend_service.list_requests(db, profile_id, "incoming")}


@router.get("/requests/outgoing")
async def list_outgoing_requests(
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile_id, _ = _current_profile_identity(db, current_user)
    return {"requests": friend_service.list_requests(db, profile_id, "outgoing")}


@router.post("/requests/send")
async def send_request(
    payload: FriendRequestCreate,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    sender_id, _ = _current_profile_identity(db, current_user)
    target_id = _resolve_target_profile_id(db, payload.target_profile_name)
    result = friend_service.send_request(db, sender_id, target_id)
    await SOCIAL_EVENT_HUB.broadcast({"type": "friend_request_sent", "payload": result})
    return result


@router.post("/requests/accept")
async def accept_request(
    payload: FriendRequestAction,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    receiver_id, _ = _current_profile_identity(db, current_user)
    requestor_id = _resolve_target_profile_id(db, payload.requestor_profile_name)
    result = friend_service.accept_request(db, receiver_id, requestor_id)
    await SOCIAL_EVENT_HUB.broadcast({"type": "friend_request_accepted", "payload": result})
    return result


@router.post("/requests/decline")
async def decline_request(
    payload: FriendRequestAction,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    receiver_id, _ = _current_profile_identity(db, current_user)
    requestor_id = _resolve_target_profile_id(db, payload.requestor_profile_name)
    result = friend_service.decline_request(db, receiver_id, requestor_id)
    await SOCIAL_EVENT_HUB.broadcast({"type": "friend_request_declined", "payload": result})
    return result


@router.post("/requests/cancel")
async def cancel_request(
    payload: FriendRequestAction,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    sender_id, _ = _current_profile_identity(db, current_user)
    target_id = _resolve_target_profile_id(db, payload.requestor_profile_name)
    return friend_service.cancel_request(db, sender_id, target_id)


@router.delete("/friends/{friend_profile_name}")
async def remove_friend(
    friend_profile_name: str,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile_id, _ = _current_profile_identity(db, current_user)
    friend_id = _resolve_target_profile_id(db, friend_profile_name)
    result = friend_service.remove_friend(db, profile_id, friend_id)
    await SOCIAL_EVENT_HUB.broadcast({"type": "friend_removed", "payload": result})
    return result


@router.get("/blocked")
async def list_blocked(
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile_id, _ = _current_profile_identity(db, current_user)
    return {"blocked": block_service.list_blocked(db, profile_id)}


@router.post("/blocked")
async def block_player(
    payload: BlockRequest,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    blocker_id, _ = _current_profile_identity(db, current_user)
    blocked_id = _resolve_target_profile_id(db, payload.blocked_profile_name)
    block_service.block_player(db, blocker_id, blocked_id)
    await SOCIAL_EVENT_HUB.broadcast({"type": "player_blocked", "payload": {"blocker_id": blocker_id, "blocked_id": blocked_id}})
    return {"status": "blocked", "blocked_profile_name": payload.blocked_profile_name}


@router.delete("/blocked/{blocked_profile_name}")
async def unblock_player(
    blocked_profile_name: str,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    blocker_id, _ = _current_profile_identity(db, current_user)
    blocked_id = _resolve_target_profile_id(db, blocked_profile_name)
    block_service.unblock_player(db, blocker_id, blocked_id)
    return {"status": "unblocked", "blocked_profile_name": blocked_profile_name}


@router.post("/reports")
async def report_player(
    payload: ReportRequest,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    reporter_id, _ = _current_profile_identity(db, current_user)
    reported_id = _resolve_target_profile_id(db, payload.reported_profile_name)
    result = report_service.create_report(db, reporter_id, reported_id, payload.reason, payload.description)
    await SOCIAL_EVENT_HUB.broadcast({"type": "player_reported", "payload": result})
    return result


@router.post("/presence")
async def update_presence(
    payload: PresenceUpdate,
    db: pymysql.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    profile_id, _ = _current_profile_identity(db, current_user)
    presence_service.update_status(db, profile_id, payload.status.value, payload.message)
    event = {"type": "presence_updated", "profile_id": profile_id, "status": payload.status.value, "message": payload.message, "bucket": bucket_for_status(payload.status.value)}
    await SOCIAL_EVENT_HUB.broadcast(event)
    return event


@router.get("/presence/{profile_name}")
async def get_presence(
    profile_name: str,
    db: pymysql.Connection = Depends(get_db),
):
    profile_id = _resolve_target_profile_id(db, profile_name)
    status_row = presence_service.get_status(db, profile_id)
    if not status_row:
        raise HTTPException(status_code=404, detail="Statut introuvable")
    return {
        "profile_name": profile_name,
        "status": status_row.get("current_status") or PlayerStatus.OFFLINE.value,
        "message": status_row.get("status_message"),
        "last_seen_at": status_row.get("last_seen_at").isoformat() if status_row.get("last_seen_at") else None,
    }


@router.websocket("/ws")
async def social_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        from auth.jwt import _verify_jwt
        payload = _verify_jwt(token)
        if not payload.get("sub"):
            raise Exception("missing-sub")
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await SOCIAL_EVENT_HUB.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        SOCIAL_EVENT_HUB.disconnect(websocket)
    except Exception:
        SOCIAL_EVENT_HUB.disconnect(websocket)


def _resolve_target_profile_id(db: pymysql.Connection, profile_name: str) -> int:
    profile_name = _validate_profile_name(profile_name)
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id FROM profiles WHERE game_name = %s", (profile_name,))
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ce nom n'est pas utilisé par un joueur !")
    return int(row["id"])
