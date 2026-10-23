from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.dependencies import get_current_user
from streamer import streamer_manager

router = APIRouter(prefix="/streamer", tags=["streamer"])


# Request/response models
class CreateSessionRequest(BaseModel):
    streamer_link: str
    live_duration: int = Field(3600, ge=0)
    viewver_response_time: int = Field(20, ge=1)


class CreateSessionResponse(BaseModel):
    id: str
    streamer_link: str
    live_duration: int
    viewver_response_time: int
    status: str
    participants: list
    integrations: Dict[str, Any]


class JoinRequest(BaseModel):
    player_id: str


class StatusUpdateRequest(BaseModel):
    action: str  # start | end | set
    status: Optional[str] = None


class IntegrationRequest(BaseModel):
    provider: str  # twitch|youtube
    config: Dict[str, Any]


@router.post("/create", response_model=CreateSessionResponse)
async def create_session(
    req: CreateSessionRequest,
    user = Depends(get_current_user),
):
    """Create a new streamer session."""
    # allow anonymous creation as well, but prefer authenticated user
    session = streamer_manager.create_session(
        streamer_link=req.streamer_link,
        live_duration=req.live_duration,
        viewver_response_time=req.viewver_response_time,
    )

    return CreateSessionResponse(
        id=session.id,
        streamer_link=session.streamer_link,
        live_duration=session.live_duration,
        viewver_response_time=session.viewver_response_time,
        status=session.status,
        participants=session.participants,
        integrations=session.integrations,
    )


@router.post("/{session_id}/join")
async def join_session(
    session_id: str,
    req: JoinRequest,
    user = Depends(get_current_user),
):
    """Join a session as a viewver/player."""
    success = streamer_manager.join_session(session_id, req.player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    session = streamer_manager.sessions.get(session_id)
    return {"ok": True, "participants": session.participants}


@router.post("/{session_id}/leave")
async def leave_session(
    session_id: str,
    req: JoinRequest,
    user = Depends(get_current_user),
):
    """Leave a session."""
    success = streamer_manager.leave_session(session_id, req.player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session non trouvée ou participant inconnu")
    session = streamer_manager.sessions.get(session_id)
    return {"ok": True, "participants": session.participants}


@router.post("/{session_id}/status")
async def update_status(
    session_id: str,
    req: StatusUpdateRequest,
    user = Depends(get_current_user),
):
    """Update session status (start/end/set)."""
    action = req.action.lower()
    if action == "start":
        session = streamer_manager.start_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        return {"ok": True, "status": session.status}
    elif action == "end":
        session = streamer_manager.end_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        return {"ok": True, "status": session.status}
    elif action == "set":
        if not req.status:
            raise HTTPException(status_code=400, detail="status requis pour l'action 'set'")
        session = streamer_manager.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        session.status = req.status
        return {"ok": True, "status": session.status}
    else:
        raise HTTPException(status_code=400, detail="Action inconnue")


@router.get("/{session_id}/stats")
async def get_stats(session_id: str):
    """Get aggregated statistics and session results."""
    results = streamer_manager.get_session_results(session_id)
    if not results:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return results


@router.post("/{session_id}/link")
async def link_integration(session_id: str, req: IntegrationRequest, user = Depends(get_current_user)):
    """Link Twitch or YouTube configuration for chat/live integration."""
    provider = req.provider.lower()
    if provider not in ("twitch", "youtube"):
        raise HTTPException(status_code=400, detail="Provider invalide")

    success = streamer_manager.set_integration(session_id, provider, req.config)
    if not success:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    session = streamer_manager.sessions.get(session_id)
    return {"ok": True, "integrations": session.integrations}


@router.get("/{session_id}")
async def get_session(session_id: str):
    session = streamer_manager.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return {
        "id": session.id,
        "streamer_link": session.streamer_link,
        "live_duration": session.live_duration,
        "viewver_response_time": session.viewver_response_time,
        "status": session.status,
        "participants": session.participants,
        "integrations": session.integrations,
        "questions_count": len(session.questions),
        "current_question_index": session.current_question_index,
    }
