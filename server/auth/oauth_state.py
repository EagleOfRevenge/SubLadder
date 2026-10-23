"""
Gestion stateless CSRF pour OAuth2.
"""
from datetime import datetime, timezone, timedelta
import secrets
import hmac
import hashlib
from jose import jwt

def _get_discord_config():
    """Récupérer la config Discord."""
    import json
    import os
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.example.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _generate_oauth_state(room_code: str = None) -> tuple[str, dict]:
    """
    Génère un state CSRF unique et ses metadata associées.
    Retourne (state, metadata_dict) où metadata_dict contient room_code et timestamp.
    """
    state = secrets.token_urlsafe(32)
    metadata = {
        "state": state,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if room_code:
        metadata["room_code"] = room_code
    return state, metadata


def _make_state_jwt(state: str, room_code: str = None) -> str:
    """
    Encode les metadata OAuth2 dans un JWT court (TTL 5 min).
    C'est le payload chiffré/signé envoyé dans le cookie.
    """
    config = _get_discord_config()
    secret = config.get("discord", {}).get("state_secret", "change-this-to-a-random-secret-key!")
    
    payload = {
        "state": state,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    if room_code:
        payload["room_code"] = room_code
    return jwt.encode(payload, secret, algorithm="HS256")


def _parse_state_jwt(token: str) -> dict:
    """
    Decode et valide un JWT de state OAuth2.
    Retourne les metadata si valide, None sinon.
    """
    config = _get_discord_config()
    secret = config.get("discord", {}).get("state_secret", "change-this-to-a-random-secret-key!")
    
    try:
        from jose import jwt, ExpiredSignatureError, JWTError
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        # Vérifier que le state n'est pas trop vieux (même si le JWT TTL le gère)
        exp = payload.get("exp", 0)
        if exp < datetime.now(timezone.utc).timestamp():
            return None
        return payload
    except (ExpiredSignatureError, JWTError, Exception):
        return None