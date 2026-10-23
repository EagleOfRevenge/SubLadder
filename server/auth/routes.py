"""
Endpoints d'authentification principaux.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import pymysql
import re
from database import get_db
from .jwt import _generate_jwt, resolve_user_role
from .passwords import _hash_password, _verify_password
from .oauth_result import peek_oauth_result

# Router pour les endpoints d'authentification
router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    game_name: str = Field(..., min_length=3, max_length=32)

# ── Bloc 4 — Endpoints Register/Login ──────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db=Depends(get_db)):
    """Créer un compte email/mot de passe + profil de jeu."""
    if not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", str(data.email)):
        raise HTTPException(status_code=422, detail="Email invalide")

    if not re.fullmatch(r"[A-Za-z0-9_\-]{3,32}", data.game_name):
        raise HTTPException(status_code=422, detail="Nom de profil invalide")

    if len(data.password) < 8 or len(data.password) > 128:
        raise HTTPException(status_code=422, detail="Mot de passe invalide")

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Vérifier si l'email existe déjà
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email déjà utilisé")

        # Hash le mot de passe
        password_hash = _hash_password(data.password)

        # Créer l'utilisateur
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (data.email, password_hash)
        )
        user_id = cursor.lastrowid

        # Créer le profil de jeu
        cursor.execute(
            "INSERT INTO profiles (user_id, game_name) VALUES (%s, %s)",
            (user_id, data.game_name)
        )

    db.commit()

    # Générer le JWT
    token = _generate_jwt(user_id, data.email, data.game_name)

    return {
        "message": "Compte créé avec succès",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": data.email,
            "profile_name": data.game_name,
            "role": resolve_user_role(data.email),
        },
    }


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """Se connecter avec email/mot de passe."""
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        # Trouver l'utilisateur par email
        cursor.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (form_data.username,))
        user = cursor.fetchone()

        if not user or not _verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

        # Trouver le profil par défaut
        cursor.execute(
            "SELECT id, game_name FROM profiles WHERE user_id = %s ORDER BY created_at ASC LIMIT 1",
            (user["id"],)
        )
        profile = cursor.fetchone()

    token = _generate_jwt(user["id"], user["email"], profile["game_name"] if profile else None)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "profile_name": profile["game_name"] if profile else None,
            "role": resolve_user_role(user["email"]),
        },
    }


@router.post("/logout")
async def logout(jti: str, db=Depends(get_db)):
    """Révoquer un token JWT (ajouté au blacklist)."""
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO jwt_blacklist (jti, expires_at) VALUES (%s, DATE_ADD(NOW(), INTERVAL 7 DAY))",
            (jti,)
        )
    db.commit()
    return {"message": "Déconnecté avec succès"}


@router.get("/oauth/result")
async def oauth_result(state: str):
    """Return the most recent OAuth result for a given state, if any."""
    result = peek_oauth_result(state)
    if not result:
        return {"status": "pending"}
    return {"status": "ready", "result": result}