#!/usr/bin/env bash
set -euo pipefail

# Script de lancement + vérification du serveur SubLadder
# Usage: bash run_and_check.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
HEALTH_URL="http://127.0.0.1:${PORT}/api/health"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/server.log}"

log() {
  echo "[RUN] $*"
}

if [[ ! -d "$SCRIPT_DIR/venv" ]]; then
  log "Environnement virtuel introuvable. Installation requise."
  exit 1
fi

source "$SCRIPT_DIR/venv/bin/activate"

if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
  log "Fichier .env introuvable. Copiez .env.example vers .env avant de continuer."
  exit 1
fi

set -a
source "$SCRIPT_DIR/.env"
set +a

if command -v systemctl >/dev/null 2>&1; then
  log "Démarrage via systemd..."
  sudo systemctl start subladder || true
  sleep 3
  sudo systemctl status subladder --no-pager || true
else
  log "Démarrage direct du serveur..."
  nohup python3 server.py > "$LOG_FILE" 2>&1 &
fi

for i in {1..20}; do
  if curl -fsS "$HEALTH_URL" >/tmp/subladder_health.json 2>/dev/null; then
    log "Serveur OK"
    cat /tmp/subladder_health.json
    exit 0
  fi
  sleep 2
done

log "Le serveur n’a pas répondu à temps."
log "Journal : $LOG_FILE"
if [[ -f "$LOG_FILE" ]]; then
  tail -n 40 "$LOG_FILE" || true
fi
exit 1
