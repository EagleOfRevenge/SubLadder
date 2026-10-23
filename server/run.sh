#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SubLadder Server — Script de lancement (Linux/macOS)
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Colors ──────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "${BLUE}[STEP]${NC} $1"; }

# ── Check virtual environment ──────────────────────────────────

if [ ! -d "venv" ]; then
    log_warn "Environnement virtuel introuvable — exécution du déploiement..."
    bash deploy.sh
    echo ""
fi

# ── Activate venv ──────────────────────────────────────────────

source venv/bin/activate

# ── Environment variables from config ──────────────────────────

if [ -f "config.json" ]; then
    # Extract debug mode from config
    DEBUG_VAL=$(python3 -c "import json; c=json.load(open('config.json')); print(str(c.get('server',{}).get('debug', False)).lower())" 2>/dev/null || echo "false")
    export DEBUG="$DEBUG_VAL"
fi

# ── Start server ───────────────────────────────────────────────

log_info "═══════════════════════════════════════════════════════════"
log_info "  SubLadder Server v4.0"
log_info "  Port: ${PORT:-8000}"
log_info "  Debug: ${DEBUG:-false}"
log_info "═══════════════════════════════════════════════════════════"
log_info ""

python3 server.py
