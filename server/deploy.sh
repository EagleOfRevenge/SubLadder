#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SubLadder Server — Script de déploiement
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Colors ──────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Prerequisites check ────────────────────────────────────────

log_info "Vérification des prérequis..."

# Python
if ! command -v python3 &> /dev/null; then
    log_error "python3 est requis. Installez-le d'abord."
    exit 1
fi

log_info "Python $(python3 --version) détecté"

# pip
if ! command -v pip3 &> /dev/null; then
    log_error "pip3 est requis."
    exit 1
fi

# MariaDB
if ! command -v mysql &> /dev/null; then
    log_warn "mysql client non détecté — l'initialisation DB sera ignorée"
    SKIP_DB_INIT=true
else
    SKIP_DB_INIT=false
fi

# ── Virtual environment ────────────────────────────────────────

log_info "Configuration de l'environnement virtuel..."

if [ ! -d "venv" ]; then
    log_info "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

source venv/bin/activate

# Installer les dépendances
log_info "Installation des dépendances..."
pip install -r requirements.txt --quiet

log_info "Dépendances installées."

# ── Configuration ──────────────────────────────────────────────

if [ ! -f "config.json" ]; then
    log_warn "config.json introuvable — copie de config.example.json"
    cp config.example.json config.json
    log_warn "⚠️  Modifiez config.json avant de lancer en production !"
fi

# ── Database initialization ────────────────────────────────────

if [ "$SKIP_DB_INIT" = false ]; then
    log_info "Initialisation de la base de données..."
    python3 database/init_db.py \
        --host 127.0.0.1 \
        --port 3306 \
        --user "${DB_USER:-root}" \
        --password "${DB_PASS:-}" \
        --database "${DB_NAME:-sub_ladder}"
else
    log_warn "Initialisation DB ignorée (mysql client non disponible)"
fi

# ── Systemd service (optionnel) ────────────────────────────────

if [ "${INSTALL_SERVICE:-false}" = "true" ]; then
    log_info "Installation du service systemd..."

    SERVICE_FILE="/etc/systemd/system/subladder.service"
    sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=SubLadder Server
After=network.target mariadb.service

[Service]
Type=simple
User=${USER:-subladder}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/venv/bin/python ${SCRIPT_DIR}/server.py
Restart=on-failure
RestartSec=10
Environment=PATH=${SCRIPT_DIR}/venv/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable subladder
    sudo systemctl start subladder
    log_info "Service systemd installé et démarré."
fi

# ── Summary ────────────────────────────────────────────────────

echo ""
log_info "═══════════════════════════════════════════════════════════"
log_info "Déploiement terminé avec succès !"
log_info ""
log_info "  Démarrer le serveur :  ./run.sh"
log_info "  Swagger UI :           http://localhost:8000/docs"
log_info "  Health check :         http://localhost:8000/api/health"
log_info ""
log_info "  Service systemd :      systemctl status subladder"
log_info "═══════════════════════════════════════════════════════════"
echo ""
