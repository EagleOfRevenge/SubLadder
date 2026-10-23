@echo off
REM ═══════════════════════════════════════════════════════════════
REM SubLadder Server — Script de deploiement (Windows)
REM ═══════════════════════════════════════════════════════════════

cd /d "%~dp0"

echo [INFO] Verification des prerequis...

REM ── Check Python ──────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python est requis. Installez-le d'abord.
    exit /b 1
)

echo [INFO] Python %PYTHON_VERSION% detecte

REM ── Virtual environment ───────────────────────────────────────

if not exist "venv" (
    echo [INFO] Creation de l'environnement virtuel...
    python -m venv venv
)

call venv\Scripts\activate

REM ── Install dependencies ──────────────────────────────────────

echo [INFO] Installation des dependances...
pip install -r requirements.txt --quiet

echo [INFO] Dependances installees.

REM ── Configuration ─────────────────────────────────────────────

if not exist "config.json" (
    echo [WARN] config.json introuvable — copie de config.example.json
    copy config.example.json config.json >nul
    echo [WARN] Modifiez config.json avant de lancer en production !
)

REM ── Database initialization ───────────────────────────────────

echo [INFO] Initialisation de la base de donnees...
python database\init_db.py --host 127.0.0.1 --port 3306 --user root --password ""

echo.
echo ===============================================================
echo Deploiement termine avec succes !
echo.
echo   Demarrer le serveur :  run.bat
echo   Swagger UI :           http://localhost:8000/docs
echo   Health check :         http://localhost:8000/api/health
echo ===============================================================
echo.

pause
