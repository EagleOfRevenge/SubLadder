# ═══════════════════════════════════════════════════════════════
# Sub Ladder v4.0 — Anti-cheat logs and review endpoints
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt import _verify_jwt
from cheat import load_cheat_log

router = APIRouter(prefix="/cheat", tags=["cheat"])
security = HTTPBearer(auto_error=False)


def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    try:
        payload = _verify_jwt(credentials.credentials)
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "game_name": payload.get("profile_name"),
        }
    except HTTPException:
        raise


@router.get("/flags")
async def get_cheat_flags(current_user: dict = Depends(get_current_user_from_token)):
    """Return suspicious score submission warnings for the authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Non authentifié")
    entries = load_cheat_log(user_id=current_user["id"])
    return {"flags": entries}
