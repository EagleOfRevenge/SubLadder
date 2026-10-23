# 🚀 QUICK START - SubLadder Server v4.0

## 📋 Prérequis
- Python 3.8+
- MariaDB/MySQL en local ou remote
- pip

## ⚡ ÉTAPES RAPIDES POUR DÉMARRER

### 1️⃣ Configuration de la base de données

```bash
# Copier le config example
cp server/config.example.json server/config.json

# ÉDITER server/config.json avec vos credentials DB:
# "host": "127.0.0.1" (ou votre DB host)
# "user": "root" (ou votre user)
# "password": "***" (votre password)
# "name": "sub_ladder" (DB name)

# CHANGER le JWT secret (IMPORTANT):
# "secret": "votre-clé-secrète-aléatoire-très-longue-et-sécurisée"
```

### 2️⃣ Initialiser la base de données

```bash
cd server
python database/init_db.py --host 127.0.0.1 --user root --password "votre_password"
```

✅ Vous devriez voir:
```
✅ Database 'sub_ladder' prête.
✓ [1/XX] Table créée
...
✅ Tables créées avec succès !
```

### 3️⃣ Installer les dépendances

```bash
pip install fastapi uvicorn pymysql bcrypt python-jose pydantic
```

### 4️⃣ Démarrer le serveur

```bash
cd server
python server.py
```

✅ Vous devriez voir:
```
============================================================
  Sub Ladder Server v4.0
  Starting on 0.0.0.0:8000
  Workers: 4
============================================================

✅ Sub Ladder - Server API v4.0 starting up...
📊 Debug mode: OFF
🌐 Available endpoints:
   - Health check: GET /api/health
   - Auth: POST /auth/register, /auth/login
   - Scores: POST /api/score
   - Leaderboard: GET /api/leaderboard
   - Profile: GET /api/profile
   - Ranked: GET/POST /api/ranked/*
   - Multiplayer: WS /api/multiplayer/ws (+ REST endpoints)
   - API Docs: GET /docs
```

### 5️⃣ Tester le serveur

Ouvrir dans votre navigateur:
- **Documentation API**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/api/health

Vous devriez voir:
```json
{
  "status": "ok",
  "version": "4.0",
  "service": "SubLadder Server API"
}
```

### 6️⃣ Tester l'authentification

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "game_name": "TestPlayer"
  }'
```

✅ Réponse attendue:
```json
{
  "message": "Compte créé avec succès",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "profile_name": "TestPlayer"
  }
}
```

### 7️⃣ Tester les endpoints profil

```bash
# Remplacer TOKEN par le access_token reçu ci-dessus
TOKEN="votre_token_ici"

curl -X GET "http://localhost:8000/api/profile/TestPlayer/overview" \
  -H "Authorization: Bearer $TOKEN"
```

✅ Réponse attendue:
```json
{
  "game_name": "TestPlayer",
  "account_created_at": "2026-05-26T...",
  "current_rank": {
    "tier": "Iron",
    "division": 1,
    "elo": 1000,
    "display": "Iron I",
    "icon": "⚫"
  },
  "ranked_wins": 0,
  "games_played": 0,
  "win_rate": 0.0
}
```

---

## 🎮 Tester le Multiplayer (WebSocket)

### 1. Rejoindre la queue aléatoire 1v1

```javascript
// Dans votre client JavaScript/Python/etc.

const ws = new WebSocket(
  'ws://localhost:8000/api/multiplayer/ws?profile_id=1&game_name=TestPlayer&elo=1000'
);

ws.onopen = () => {
  console.log('Connected!');
  
  // Rejoindre la queue aléatoire
  ws.send(JSON.stringify({
    action: 'join_queue'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Server:', message);
  
  if (message.event === 'queue_joined') {
    console.log(`Position en queue: ${message.position}`);
  } else if (message.event === 'match_found') {
    console.log(`Match trouvé! Adversaire: ${message.opponent.game_name}`);
  }
};
```

### 2. Créer un salon personnalisé

```javascript
ws.send(JSON.stringify({
  action: 'create_room',
  room_name: 'My Awesome Room',
  is_private: false,
  password: null
}));

// Réponse:
// {
//   "event": "room_created",
//   "room": {
//     "room_id": "room_abc123",
//     "creator_name": "TestPlayer",
//     "room_name": "My Awesome Room",
//     "player_count": 1,
//     "max_players": 4,
//     ...
//   }
// }
```

### 3. Lister les salons publics

```javascript
ws.send(JSON.stringify({
  action: 'list_rooms'
}));

// Réponse:
// {
//   "event": "rooms_list",
//   "rooms": [...]
// }
```

---

## ❓ TROUBLESHOOTING

### ❌ Erreur: "Connection refused" (DB)
**Solution**: Vérifier que MariaDB/MySQL est en cours d'exécution
```bash
# Windows
net start MySQL80

# Linux
sudo systemctl start mysql

# macOS
brew services start mysql
```

### ❌ Erreur: "JWT secret not configured"
**Solution**: Éditer `server/config.json` et ajouter un JWT secret

### ❌ Erreur: "Port 8000 already in use"
**Solution**: Changer le port dans `server/config.json` ou tuer le processus:
```bash
# Linux/macOS
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### ❌ Erreur: "ModuleNotFoundError"
**Solution**: Installer les dépendances manquantes
```bash
pip install fastapi uvicorn pymysql bcrypt python-jose pydantic
```

---

## 📚 PROCHAINES ÉTAPES

1. ✅ Serveur tourne sur `http://localhost:8000`
2. ✅ Auth fonctionne (register/login)
3. ✅ Endpoints profil fonctionnent
4. ✅ Multiplayer WebSocket fonctionne
5. ⏭️ **À faire**: Implémenter `POST /api/score` (voir SERVER_CHECKLIST.md)
6. ⏭️ **À faire**: Implémenter `GET /api/leaderboard`
7. ⏭️ **À faire**: Anti-cheat server-side

Voir `SERVER_CHECKLIST.md` pour la checklist complète.

---

## 🔗 LIENS UTILES

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health
- Root Info: http://localhost:8000/
