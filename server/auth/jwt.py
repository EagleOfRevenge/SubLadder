"""
Fonctions utilitaires JWT.
"""
from datetime import datetime, timezone, timedelta
import os
import secrets
from jose import jwt, JWTError
from fastapi import HTTPException, status


def _load_config():
    """Charger la configuration depuis l’environnement ou depuis config.json."""
    import json
    import os

    config = {}
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.example.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

    env_config = config.get("jwt", {})
    env_config = dict(env_config)
    env_secret = os.getenv("JWT_SECRET")
    if env_secret:
        env_config["secret"] = env_secret
    env_algorithm = os.getenv("JWT_ALGORITHM")
    if env_algorithm:
        env_config["algorithm"] = env_algorithm
    env_expires = os.getenv("JWT_EXPIRES_MINUTES")
    if env_expires:
        try:
            env_config["expires_minutes"] = int(env_expires)
        except ValueError:
            pass

    config["jwt"] = env_config
    return config


def resolve_user_role(email: str | None) -> str:
    """Resolve the role for a user based on a small allowlist of admin emails."""
    if not email:
        return "user"
    config = _load_config()
    admin_emails = set()
    admin_cfg = config.get("admin", {})
    if isinstance(admin_cfg, dict):
        for value in admin_cfg.get("emails", []) or []:
            if isinstance(value, str) and value.strip():
                admin_emails.add(value.strip().lower())
    env_admins = os.getenv("ADMIN_EMAILS", "")
    for value in env_admins.split(","):
        value = value.strip().lower()
        if value:
            admin_emails.add(value)
    return "admin" if email.strip().lower() in admin_emails else "user"


def _generate_jwt(user_id: int, email: str, profile_name: str) -> str:
    """Générer un JWT token."""
    config = _load_config()
    jwt_config = config.get("jwt", {})
    secret = os.getenv("JWT_SECRET") or jwt_config.get("secret") or "change-this-to-a-random-secret-key!"
    algorithm = os.getenv("JWT_ALGORITHM") or jwt_config.get("algorithm") or "HS256"
    expires = int(os.getenv("JWT_EXPIRES_MINUTES", jwt_config.get("expires_minutes", "10080")))

    payload = {
        "sub": str(user_id),
        "email": email,
        "profile_name": profile_name,
        "role": resolve_user_role(email),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def _verify_jwt(token: str, db=None):
    """Vérifier un JWT token et rejeter les tokens blacklistés."""
    config = _load_config()
    jwt_config = config.get("jwt", {})
    secret = os.getenv("JWT_SECRET") or jwt_config.get("secret") or "change-this-to-a-random-secret-key!"
    algorithm = os.getenv("JWT_ALGORITHM") or jwt_config.get("algorithm") or "HS256"

    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm], options={"require": ["sub", "exp", "jti"]})
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if not payload.get("jti"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if db is None:
        from database import get_db
        try:
            db = next(get_db())
        except Exception:
            db = None

    if db is not None:
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT 1 FROM jwt_blacklist WHERE jti = %s", (payload["jti"],))
                if cursor.fetchone():
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token révoqué")
        except Exception:
            pass

    return payload
