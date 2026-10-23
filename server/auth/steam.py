"""
Fonctions d'authentification via Steam.
"""
import requests
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode, urlparse, parse_qs
import secrets
import os
import logging
from jose import jwt
from database import get_db
from .jwt import _generate_jwt
from .oauth_result import store_oauth_result

# Configuration du logger
logger = logging.getLogger(__name__)

# Router pour les endpoints d'authentification Steam
router = APIRouter(prefix="/auth/steam", tags=["auth_steam"])

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

    steam_config = dict(config.get("steam", {}))
    steam_config.update({
        "enabled": os.getenv("STEAM_ENABLED", steam_config.get("enabled", False)),
        "api_key": os.getenv("STEAM_API_KEY", steam_config.get("api_key")),
        "redirect_uri": os.getenv("STEAM_REDIRECT_URI", steam_config.get("redirect_uri")),
    })
    config["steam"] = steam_config
    return config

def _is_steam_enabled():
    """Vérifier si l'authentification Steam est activée."""
    config = _load_config()
    steam_config = config.get("steam", {})
    return steam_config.get("enabled", False)

def _get_steam_api_url(endpoint):
    """Obtenir l'URL complète de l'API Steam."""
    return f"https://api.steampowered.com{endpoint}"

def _get_steam_auth_url(request: Request, state: str | None = None):
    """Obtenir l'URL d'authentification Steam."""
    config = _load_config()
    steam_config = config.get("steam", {})

    redirect_uri = request.query_params.get("redirect_uri") or steam_config.get("redirect_uri")

    if not redirect_uri:
        raise HTTPException(status_code=500, detail="Configuration Steam incomplète")

    # Pour l'authentification Steam OpenID
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": redirect_uri if state is None else f"{redirect_uri}&state={state}",
        "openid.realm": urlparse(redirect_uri).scheme + "://" + urlparse(redirect_uri).netloc,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }

    return f"https://steamcommunity.com/openid/login?{urlencode(params)}"

@router.get("/login")
async def steam_login(request: Request):
    """Rediriger vers l'authentification Steam."""
    if not _is_steam_enabled():
        raise HTTPException(status_code=400, detail="Authentification Steam désactivée")
    
    # Générer et stocker le state dans la session pour prévenir les attaques CSRF
    state = request.query_params.get("state") or secrets.token_urlsafe(32)
    request.session["steam_oauth_state"] = state

    # Rediriger vers l'URL d'authentification Steam
    auth_url = _get_steam_auth_url(request, state=state)
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def steam_callback(request: Request, db=Depends(get_db)):
    """Gérer le retour de l'authentification Steam."""
    if not _is_steam_enabled():
        raise HTTPException(status_code=400, detail="Authentification Steam désactivée")
    
    # Récupérer les paramètres de la requête
    query_params = dict(request.query_params)

    # Vérifier le state pour prévenir les attaques CSRF
    stored_state = request.session.get("steam_oauth_state")
    received_state = query_params.get("state")
    if stored_state and received_state and stored_state != received_state:
        raise HTTPException(status_code=400, detail="Requête CSRF invalide")

    # Vérifier si on a un openid.mode et un openid.return_to
    if 'openid.mode' not in query_params or query_params['openid.mode'] != 'id_res':
        raise HTTPException(status_code=400, detail="Erreur d'authentification Steam")
    
    # Vérifier que l'utilisateur est authentifié
    if 'openid.identity' not in query_params:
        raise HTTPException(status_code=400, detail="Identité Steam non fournie")
    
    # Récupérer l'identifiant Steam
    steam_identity = query_params['openid.identity']
    
    # Extraire l'ID Steam de l'URL
    try:
        steam_id = steam_identity.split('/')[-1]
    except (IndexError, AttributeError):
        raise HTTPException(status_code=400, detail="Format d'identifiant Steam invalide")
    
    # Rechercher l'utilisateur par ID Steam
    with db.cursor() as cursor:
        # Vérifier si un utilisateur existe déjà avec ce Steam ID
        cursor.execute("SELECT id, email, password_hash, discord_id FROM users WHERE steam_id = %s", (steam_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # L'utilisateur existe déjà, se connecter
            user_id = existing_user[0]
            email = existing_user[1]
            password_hash = existing_user[2]
            discord_id = existing_user[3]
            
            # Mettre à jour les informations Steam si elles ont changé (optionnel)
            # Pour l'instant, Steam ne permet pas de récupérer le nom d'utilisateur via OpenID
            # On peut le faire avec l'API Web si on a une clé API
            
        else:
            # Créer un nouvel utilisateur
            email = None  # Aucun email pour Steam
            password_hash = None  # Aucun mot de passe pour Steam
            discord_id = None  # Aucun Discord ID
            
            # Créer le nouvel utilisateur avec les données Steam
            cursor.execute(
                "INSERT INTO users (email, password_hash, steam_id, discord_id, discord_username, discord_avatar) VALUES (%s, %s, %s, %s, %s, %s)",
                (email, password_hash, steam_id, discord_id, None, None)
            )
            
            user_id = cursor.lastrowid
        
        db.commit()
    
    # Générer le JWT
    # Pour Steam, on utilisera l'ID Steam comme nom de profil par défaut
    token = _generate_jwt(user_id, email or "", f"Steam_{steam_id}")
    
    result = {
        "message": "Authentification Steam réussie",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email or "",
            "profile_name": f"Steam_{steam_id}",
            "steam_id": steam_id,
        },
    }

    store_oauth_result(received_state or stored_state or "", result)
    
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
                background: linear-gradient(135deg, #1b2838 0%, #2a475e 100%);
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
                color: #1b2838;
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
            <h1>Authentification Steam réussie !</h1>
            <p class="success">Vous pouvez fermer cette page et retourner au jeu.</p>
        </div>
        <script>
            navigator.clipboard.writeText('{token}').catch(err => {{
                console.error('Erreur copie presse-papier:', err);
            }});
            
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
async def link_steam_account(request: Request, db=Depends(get_db)):
    """Lier un compte Steam à un compte existant."""
    if not _is_steam_enabled():
        raise HTTPException(status_code=400, detail="Authentification Steam désactivée")
    
    # Récupérer les données de la requête (à implémenter selon le besoin)
    # Cela pourrait inclure le token JWT du compte existant et/ou d'autres informations
    raise HTTPException(status_code=501, detail="Fonctionnalité non implémentée")