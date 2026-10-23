# 🔒 Guide de Migration de Sécurité

## Priorité 1 — Checklist de durcissement

### ✅ COMPLETÉ
- [x] Correction de SQL Injection dans `server/api/leaderboard.py` (LIMIT/OFFSET paramétrés)
- [x] Nettoyage des secrets dans `config.example.json` (placeholders au lieu de vrais valeurs)
- [x] Nettoyage des secrets dans `server/config.json` (placeholders au lieu de vrais valeurs)
- [x] Création de `.env.example` pour externalisation des secrets
- [x] Création de `.gitignore` pour empêcher le commit de secrets

### ⚠️ À FAIRE (manuel)

#### 1. Restaurer les vrais credentials
Copiez vos vraies valeurs dans `server/config.json` :
```json
{
    "database": {
        "password": "VOTRE_MOT_DE_PASSE_MYSQL"
    },
    "jwt": {
        "secret": "VOTRE_SECRET_JWT_GENERE_AVEC:"
    },
    "discord": {
        "client_id": "VOTRE_CLIENT_ID",
        "client_secret": "VOTRE_CLIENT_SECRET",
        "bot_token": "VOTRE_BOT_TOKEN"
    }
}
```

**Générer un JWT secret sécurisé :**
```bash
openssl rand -hex 32
```

#### 2. Migration vers .env (recommandé)
```bash
cd server
cp .env.example .env
# Éditer .env avec vos vraies valeurs
```

Puis modifier `server/server.py` pour charger `.env` via `python-dotenv`.

#### 3. CORS — Remplacer l'IP par un domaine
Dans `config.json`, remplacer `"http://45.156.84.114:8080"` par un domaine :
```json
"origins": [
    "https://subladder.com",
    "https://app.subladder.com"
]
```

#### 4. HTTPS/TLS (Priorité 3)
- Configurer un certificat Let's Encrypt
- Utiliser un reverse proxy (nginx/Caddy)
- Ou activer HTTPS directement dans FastAPI

#### 5. Rate Limiting (Priorité 1)
- Installer `slowapi` ou `flask-limiter`
- Appliquer sur les endpoints sensibles : auth, score, matchmaking

---

## 🚨 Alertes de sécurité détectées

| Fichier | Problème | Gravité |
|---------|----------|---------|
| `config.json` (ancien) | Secrets en clair | 🔴 Critique |
| `config.example.json` (ancien) | Secrets commités | 🔴 Critique |
| `leaderboard.py` (ancien) | SQL Injection sur LIMIT/OFFSET | 🔴 Critique |
| Aucun `.gitignore` | Risque de fuite de secrets | 🟡 Moyen |

---

## 📋 Commandes de vérification post-migration

```bash
# Vérifier qu'aucun secret n'est dans le git history
git log --all --full-history --source -- "*config*" | grep -i "password\|secret\|token"

# Vérifier le format JSON
python -c "import json; json.load(open('server/config.json'))"

# Tester les endpoints
curl http://localhost:8000/docs
curl http://localhost:8000/api/leaderboard
```
