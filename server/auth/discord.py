"""
Fonctions d'authentification via Discord.
"""
import requests
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import secrets
import os
import logging
from jose import jwt
from database import get_db
from .jwt import _generate_jwt
from .oauth_result import store_oauth_result

# Configuration du logger
logger = logging.getLogger(__name__)

# Router pour les endpoints d'authentification Discord
router = APIRouter(prefix="/auth/discord", tags=["auth_discord"])

def _load_config():
    """Charger la configuration depuis config.json ou depuis les variables d'environnement."""
    import json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.example.json")

    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

    discord_config = dict(config.get("discord", {}))
    discord_config.update({
        "enabled": os.getenv("DISCORD_ENABLED", discord_config.get("enabled", False)),
        "client_id": os.getenv("DISCORD_CLIENT_ID", discord_config.get("client_id")),
        "client_secret": os.getenv("DISCORD_CLIENT_SECRET", discord_config.get("client_secret")),
        "redirect_uri": os.getenv("DISCORD_REDIRECT_URI", discord_config.get("redirect_uri")),
        "bot_token": os.getenv("DISCORD_BOT_TOKEN", discord_config.get("bot_token")),
    })
    config["discord"] = discord_config
    return config

def _is_discord_enabled():
    """Vérifier si l'authentification Discord est activée."""
    config = _load_config()
    discord_config = config.get("discord", {})
    return discord_config.get("enabled", False)

def _get_discord_api_url(endpoint):
    """Obtenir l'URL complète de l'API Discord."""
    return f"https://discord.com/api{endpoint}"

def _get_discord_auth_url(request: Request, state: str | None = None):
    """Obtenir l'URL d'authentification Discord."""
    config = _load_config()
    discord_config = config.get("discord", {})

    client_id = discord_config.get("client_id")
    redirect_uri = request.query_params.get("redirect_uri") or discord_config.get("redirect_uri")
    scope = "identify email"

    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="Configuration Discord incomplète")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state or secrets.token_urlsafe(32),
    }

    return f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"

@router.get("/login")
async def discord_login(request: Request):
    """Rediriger vers l'authentification Discord."""
    if not _is_discord_enabled():
        raise HTTPException(status_code=400, detail="Authentification Discord désactivée")
    
    # Générer et stocker le state dans la session pour prévenir les attaques CSRF
    state = request.query_params.get("state") or secrets.token_urlsafe(32)
    request.session["discord_oauth_state"] = state

    # Rediriger vers l'URL d'authentification Discord
    auth_url = _get_discord_auth_url(request, state=state)
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def discord_callback(code: str, state: str, request: Request, db=Depends(get_db)):
    """Gérer le retour de l'authentification Discord."""
    if not _is_discord_enabled():
        raise HTTPException(status_code=400, detail="Authentification Discord désactivée")
    
    # Vérifier le paramètre state pour prévenir les attaques CSRF
    stored_state = request.session.get("discord_oauth_state")
    if not stored_state or stored_state != state:
        logger.warning(f"État CSRF non valide ou manquant lors de l'authentification Discord. State reçu: {state}")
        raise HTTPException(status_code=400, detail="Requête CSRF invalide")
    
    # Récupérer les informations du token
    config = _load_config()
    discord_config = config.get("discord", {})
    
    client_id = discord_config.get("client_id")
    client_secret = discord_config.get("client_secret")
    redirect_uri = discord_config.get("redirect_uri")
    
    if not all([client_id, client_secret, redirect_uri]):
        raise HTTPException(status_code=500, detail="Configuration Discord incomplète")
    
    # Échanger le code contre un token d'accès
    token_url = "https://discord.com/api/oauth2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()
        token_data = response.json()
        
        # Récupérer les informations utilisateur
        user_url = _get_discord_api_url("/users/@me")
        user_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        user_response = requests.get(user_url, headers=user_headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
    except requests.RequestException as e:
        logger.error(f"Erreur lors de l'appel à l'API Discord : {str(e)}")
        raise HTTPException(status_code=400, detail="Erreur lors de l'authentification Discord")
    
    # Validation des données utilisateur reçues
    if "id" not in user_data:
        logger.error("Données utilisateur Discord incomplètes : ID manquant")
        raise HTTPException(status_code=400, detail="Données utilisateur invalides")
    
    # Valider le format de l'ID Discord (doit être un string numérique)
    discord_id = str(user_data["id"])
    if not discord_id.isdigit():
        logger.error(f"Format d'ID Discord invalide : {discord_id}")
        raise HTTPException(status_code=400, detail="Format d'ID Discord invalide")
    
    # Valider le nom d'utilisateur
    if "username" not in user_data:
        logger.error("Données utilisateur Discord incomplètes : username manquant")
        raise HTTPException(status_code=400, detail="Données utilisateur invalides")
    
    discord_username = user_data["username"]
    if not isinstance(discord_username, str) or len(discord_username) == 0:
        logger.error("Nom d'utilisateur Discord invalide")
        raise HTTPException(status_code=400, detail="Nom d'utilisateur Discord invalide")
    
    # Valider l'email si présent
    email = user_data.get("email")
    if email and not isinstance(email, str):
        logger.error("Format d'email Discord invalide")
        raise HTTPException(status_code=400, detail="Format d'email Discord invalide")
    
    # Rechercher l'utilisateur par ID Discord
    
    with db.cursor() as cursor:
        # Vérifier si un utilisateur existe déjà avec ce Discord ID
        cursor.execute("SELECT id, email, password_hash, steam_id FROM users WHERE discord_id = %s", (discord_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # L'utilisateur existe déjà, se connecter
            user_id = existing_user[0]
            email = existing_user[1]
            password_hash = existing_user[2]
            steam_id = existing_user[3]
            
            # Mettre à jour les informations Discord si elles ont changé
            discord_username = user_data["username"]
            discord_avatar = user_data.get("avatar")
            
            if discord_avatar:
                avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar}.png"
            else:
                avatar_url = None
            
            cursor.execute(
                "UPDATE users SET discord_username = %s, discord_avatar = %s WHERE id = %s",
                (discord_username, avatar_url, user_id)
            )
            
        else:
            # Créer un nouvel utilisateur
            email = user_data.get("email")
            password_hash = None  # Aucun mot de passe pour Discord
            steam_id = None  # Aucun Steam ID
            
            # Vérifier si l'email est déjà utilisé par un autre compte
            if email:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Email déjà utilisé")
            
            # Créer le nouvel utilisateur avec les données Discord
            discord_username = user_data["username"]
            discord_avatar = user_data.get("avatar")
            
            if discord_avatar:
                avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar}.png"
            else:
                avatar_url = None
            
            cursor.execute(
                "INSERT INTO users (email, password_hash, discord_id, discord_username, discord_avatar, steam_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (email, password_hash, discord_id, discord_username, avatar_url, steam_id)
            )
            
            user_id = cursor.lastrowid
        
        db.commit()
    
    # Générer le JWT
    token = _generate_jwt(user_id, email or "", discord_username)
    
    result = {
        "message": "Authentification Discord réussie",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email or "",
            "profile_name": discord_username,
            "discord_id": discord_id,
            "discord_avatar": avatar_url
        },
    }

    store_oauth_result(state, result)
    
    # Retourner une page HTML de succès au lieu du JSON brut (sécurité)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SubLadder - Authentification</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #5865F2 0%, #4752C4 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            .container {{
                background: white;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                max-width: 400px;
            }}
            .icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #5865F2;
                margin: 0 0 10px 0;
                font-size: 24px;
            }}
            p {{
                color: #656870;
                margin: 10px 0;
            }}
            .success {{
                color: #43B581;
                font-weight: bold;
            }}
            .token-info {{
                background: #f0f0f0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                font-size: 12px;
                color: #72767d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">✓</div>
            <h1>Authentification réussie !</h1>
            <p class="success">Vous pouvez fermer cette page et retourner au jeu.</p>
        </div>
        <script>
            // Copier le token dans le presse-papier
            navigator.clipboard.writeText('{token}').catch(err => {{
                console.error('Erreur copie presse-papier:', err);
            }});
            
            // Fermer la page automatiquement après 3 secondes
            setTimeout(() => {{
                window.close();
            }}, 3000);
        </script>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

@router.post("/link")
async def link_discord_account(request: Request, db=Depends(get_db)):
    """Lier un compte Discord à un compte existant."""
    if not _is_discord_enabled():
        raise HTTPException(status_code=400, detail="Authentification Discord désactivée")
    
    # Récupérer les données de la requête (à implémenter selon le besoin)
    # Cela pourrait inclure le token JWT du compte existant et/ou d'autres informations
    raise HTTPException(status_code=501, detail="Fonctionnalité non implémentée")