#!/usr/bin/env bash
set -euo pipefail

# Installation clé en main pour SubLadder sur Ubuntu Server 24.04 / 24.10 / 26.04
# Usage: sudo bash install_ubuntu.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="subladder"
APP_USER="${APP_USER:-subladder}"
APP_HOME="/home/${APP_USER}"

CONFIG_FILE="$SCRIPT_DIR/config.json"
EXAMPLE_CONFIG_FILE="$SCRIPT_DIR/config.example.json"

if [[ -f "$CONFIG_FILE" ]]; then
  CONFIG_SOURCE="$CONFIG_FILE"
elif [[ -f "$EXAMPLE_CONFIG_FILE" ]]; then
  CONFIG_SOURCE="$EXAMPLE_CONFIG_FILE"
else
  echo "Aucun fichier de configuration trouvé. Vérifiez config.json ou config.example.json." >&2
  exit 1
fi

HOST="${HOST:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('server', {}).get('host', '0.0.0.0'))
PY
)}"
PORT="${PORT:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('server', {}).get('port', 8000))
PY
)}"
DB_HOST="${DB_HOST:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('database', {}).get('host', '127.0.0.1'))
PY
)}"
DB_PORT="${DB_PORT:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('database', {}).get('port', 3306))
PY
)}"
DB_NAME="${DB_NAME:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('database', {}).get('name', 'sub_ladder'))
PY
)}"
DB_USER="${DB_USER:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('database', {}).get('user', 'root'))
PY
)}"
DB_PASSWORD="${DB_PASSWORD:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('database', {}).get('password', ''))
PY
)}"
JWT_SECRET="${JWT_SECRET:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('jwt', {}).get('secret', ''))
PY
)}"
JWT_ALGORITHM="${JWT_ALGORITHM:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('jwt', {}).get('algorithm', 'HS256'))
PY
)}"
JWT_EXPIRES_MINUTES="${JWT_EXPIRES_MINUTES:-$(python3 - <<'PY' "$CONFIG_SOURCE"
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('jwt', {}).get('expires_minutes', 10080))
PY
)}"

if [[ -z "$JWT_SECRET" ]]; then
  JWT_SECRET="$(openssl rand -hex 32 2>/dev/null || tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32)"
fi

if [[ ${EUID} -ne 0 ]]; then
  echo "Ce script doit être exécuté en root. Exemple : sudo bash install_ubuntu.sh" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

log() {
  echo "[INSTALL] $*"
}

log "Mise à jour des paquets..."
apt-get update
apt-get install -y python3 python3-venv python3-pip python3-dev build-essential curl git ufw openssl

if ! id -u "$APP_USER" >/dev/null 2>&1; then
  log "Création de l'utilisateur système $APP_USER"
  useradd --create-home --shell /bin/bash "$APP_USER"
fi

log "Création du répertoire d'application..."
install -d -o "$APP_USER" -g "$APP_USER" "$APP_HOME"

log "Installation des dépendances Python..."
cd "$SCRIPT_DIR"
sudo -u "$APP_USER" bash -lc "cd '$SCRIPT_DIR' && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
  log "Création du fichier .env à partir de l'exemple"
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
fi

log "Configuration du fichier .env"
cat > "$SCRIPT_DIR/.env" <<EOF
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=$JWT_ALGORITHM
JWT_EXPIRES_MINUTES=$JWT_EXPIRES_MINUTES

DISCORD_CLIENT_ID=${DISCORD_CLIENT_ID:-}
DISCORD_CLIENT_SECRET=${DISCORD_CLIENT_SECRET:-}
DISCORD_REDIRECT_URI=${DISCORD_REDIRECT_URI:-https://dedicated-zap1280014-1.zap-srv.com/auth/discord/callback}
DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN:-}

CORS_ENABLED=true
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

SERVER_HOST=$HOST
SERVER_PORT=$PORT
DEBUG=false
WORKERS=4
EOF
chown "$APP_USER:$APP_USER" "$SCRIPT_DIR/.env"

log "Création du service systemd..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=SubLadder Server
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$SCRIPT_DIR
EnvironmentFile=$SCRIPT_DIR/.env
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null 2>&1 || true

if command -v ufw >/dev/null 2>&1; then
  log "Ouverture du port TCP $PORT via UFW"
  ufw allow "$PORT"/tcp >/dev/null 2>&1 || true
fi

log "Démarrage du service..."
systemctl start "$SERVICE_NAME"

sleep 5
systemctl is-active --quiet "$SERVICE_NAME"

log "Installation terminée."
log "Vérification : sudo systemctl status $SERVICE_NAME"
log "Health check : curl http://127.0.0.1:$PORT/api/health"
