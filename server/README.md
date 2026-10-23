# SubLadder Server — Documentation

Serveur API pour le jeu SubLadder (FastAPI + MariaDB).

## Configuration

1. Copier le fichier d'exemple :
   ```bash
   cp config.example.json config.json
   ```

2. Modifier `config.json` :
   - Changer `jwt.secret` par une clé secrète forte
   - Mettre les credentials MariaDB
   - Configurer Discord (optionnel)

## Installation

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate    # Linux/macOS
# ou
venv\Scripts\activate       # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## Initialisation de la base de données

```bash
python database/init_db.py --host 127.0.0.1 --port 3306 --user root --password votre_mot_de_passe
```

## Lancement

```bash
# Via le script de lancement
./run.sh          # Linux/macOS
run.bat           # Windows

# Ou directement
python server.py
```

Le serveur démarre sur `http://0.0.0.0:8000`.

## API

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/auth/register` | Inscription |
| POST | `/auth/login` | Connexion |
| POST | `/auth/logout` | Déconnexion |
| POST | `/api/score` | Soumettre un score |
| GET | `/api/leaderboard` | Classement offline |
| GET | `/api/leaderboard/ranked` | Classement ranked |
| GET | `/api/profile/{name}/overview` | Vue d'ensemble du profil |
| GET | `/api/profile/{name}/stats` | Stats du profil |
| GET | `/api/profile/{name}/matches` | Historique des matchs |
| GET | `/api/profile/{name}/ranked` | Stats ranked |
| POST | `/api/admin/ban` | Bannir un profil/user |
| POST | `/api/admin/unban` | Retirer un ban |
| GET | `/api/admin/bans` | Lister les bans |
| POST | `/api/admin/adjust-rank` | Ajuster rang ELO |
| GET | `/api/admin/rank-history` | Historique des ajustements |
| GET | `/api/multiplayer/rooms` | Liste des salons |
| GET | `/api/multiplayer/queue-status` | Statut de la file d'attente |
| GET | `/api/multiplayer/room/{id}` | Info d'un salon |
| WS | `/api/multiplayer/ws` | WebSocket matchmaking |
| GET | `/api/health` | Health check |

## Déploiement

Voir `deploy.sh` pour le script de déploiement.

### Prérequis de production

- HTTPS/TLS obligatoire
- JWT secret fort (changé par défaut)
- Database credentials en variables d'environnement
- Rate limiting activé
- CORS restreint aux origines autorisées

## Architecture

```
server/
├── server.py          # FastAPI app principal
├── config.json        # Configuration
├── requirements.txt   # Dépendances Python
├── scheduler.py       # Tâches planifiées (ELO decay)
├── streamer.py        # Gestionnaire mode Streamer
├── cheat.py           # Détection anti-cheat
├── auth/
│   ├── routes.py      # Routes auth (register/login/logout)
│   ├── jwt.py         # JWT generation/verification
│   └── passwords.py   # Hashing passwords
├── api/
│   ├── score.py       # POST /api/score
│   ├── leaderboard.py # GET /api/leaderboard
│   ├── profile.py     # GET /api/profile/*
│   ├── ranked.py      # Ranked endpoints
│   ├── admin.py       # Admin endpoints
│   ├── multiplayer.py # Multiplayer REST + WebSocket
│   ├── streamer.py    # Streamer API
│   └── cheat.py       # Anti-cheat logs
├── database/
│   ├── init_db.py     # Initialisation DB
│   ├── schema.sql     # Schéma complet
│   └── __init__.py    # get_db()
├── websocket/
│   └── matchmaking.py # MatchmakingManager
└── chat/
    └── ...            # Chat system
```

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `HOST` | Adresse d'écoute | `0.0.0.0` |
| `PORT` | Port | `8000` |
| `WORKERS` | Nombre de workers uvicorn | `4` |
| `DEBUG` | Mode debug | `false` |

## Sécurité

- **JWT** : tokens expirables, secret configurable
- **Passwords** : bcrypt hashing
- **Anti-cheat** : validation côté serveur des scores
- **CORS** : restreindre les origines en production
- **HTTPS** : obligatoire en production
- **Rate limiting** : à configurer en production

## Next Steps

- [x] Score submission endpoint
- [x] Leaderboard endpoints
- [x] Authentication (JWT)
- [x] Profile endpoints
- [x] Admin endpoints
- [x] Multiplayer matchmaking
- [x] Anti-cheat basique
- [x] Streamer mode (basique)
- [ ] Multiplayer game broadcast (temps réel)
- [ ] Streamer WebSocket temps réel
- [ ] Rate limiting
- [ ] HTTPS/TLS production
- [ ] Monitoring/Métriques
