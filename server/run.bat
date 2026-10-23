@echo off
REM ═══════════════════════════════════════════════════════════════
REM SubLadder Server — Script de lancement (Windows)
REM ═══════════════════════════════════════════════════════════════

cd /d "%~dp0"

REM ── Check virtual environment ─────────────────────────────────

if not exist "venv" (
    echo [WARN] Environnement virtuel introuvable — execution du deploiement...
    call deploy.bat
    echo.
)

REM ── Activate venv ─────────────────────────────────────────────

call venv\Scripts\activate

REM ── Environment variables from config ─────────────────────────

if exist "config.json" (
    for /f "tokens=2 delims=:," %%a in ('findstr /c:"debug" config.json') do (
        set DEBUG_VAL=%%a
    )
    set DEBUG=%DEBUG_VAL%
)

REM ── Start server ──────────────────────────────────────────────

echo.
echo ===============================================================
echo   SubLadder Server v4.0
echo   Port: %PORT:8000%
echo   Debug: %DEBUG:false=%
echo ===============================================================
echo.

python server.py
