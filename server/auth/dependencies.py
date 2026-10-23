"""
Dépendances FastAPI pour l'authentification.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from .jwt import _verify_jwt

security = HTTPBearer(auto_error=False)


def get_db_auth():
    """Obtenir une connexion à la base de données."""
    from database import get_db

    return get_db()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Vérifie le token JWT et retourne les informations de l'utilisateur."""
    if not credentials:
        return None
    try:
        return _verify_jwt(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Vérifie le token JWT et retourne les informations de l'utilisateur actif."""
    return get_current_user(credentials)


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dépendance pour vérifier qu'un utilisateur est authentifié."""
    return get_current_user(credentials)


def get_username_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extrait le nom d'utilisateur depuis le token JWT."""
    payload = get_current_user(credentials)
    return payload.get("profile_name") if payload else None


def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extrait l'ID utilisateur à partir du token JWT."""
    payload = get_current_user(credentials)
    return int(payload.get("sub")) if payload and payload.get("sub") is not None else None
