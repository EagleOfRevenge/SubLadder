# ═══════════════════════════════════════════════════════════════
# Sub Ladder v4.0 — FastAPI Server
# Server IP: 45.156.84.114
# Port: 8000
# ═══════════════════════════════════════════════════════════════

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
import os
import sys
import asyncio
import logging
import json

# ── Configuration ──────────────────────────────────────────────

APP_VERSION = "4.0"
APP_TITLE = "Sub Ladder - Server API"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ── Initialize FastAPI ────────────────────────────────────────

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Backend API for Sub Ladder game server",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# ── CORS Middleware ───────────────────────────────────────────
# Load CORS origins from config.json if present, otherwise use conservative defaults
origins = [
    "http://localhost",
    "http://127.0.0.1",
]
try:
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            cors_cfg = cfg.get("cors", {})
            cfg_origins = cors_cfg.get("origins")
            if cfg_origins:
                origins = cfg_origins
except Exception:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

session_secret = os.getenv("SESSION_SECRET_KEY", os.getenv("SECRET_KEY", "change-this-session-secret-key"))
app.add_middleware(SessionMiddleware, secret_key=session_secret, same_site="lax", https_only=True)

# ── Import Routers ────────────────────────────────────────────

try:
    from database import get_db
    from auth.routes import router as auth_router
    from auth.discord import router as discord_router
    from auth.steam import router as steam_router
    from api.score import router as score_router
    from api.leaderboard import router as leaderboard_router
    from api.profile import router as profile_router
    from api.streamer import router as streamer_router
    from api.cheat import router as cheat_router
    from api.ranked import router as ranked_router
    from api.admin import router as admin_router
    from api.multiplayer import router as multiplayer_router
    from api.social import router as social_router
    from admin.routes import router as admin_panel_router
except ImportError as e:
    print(f"❌ Error importing routers: {e}")
    sys.exit(1)

# ── Authentication ────────────────────────────────────────────

security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Extract and verify JWT token from Authorization header.
    Returns user payload if valid, None if not provided.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    try:
        from auth.jwt import _verify_jwt
        payload = _verify_jwt(token)
        return {
            "id": payload.get("sub"),
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "game_name": payload.get("profile_name"),
        }
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Export for use in routers
app.dependency_overrides[get_current_user] = get_current_user

# ── Configure structured logging ──────────────────────────────
try:
    from logging_config import configure_logging
    configure_logging(logging.INFO if not DEBUG else logging.DEBUG)
    logging.getLogger(__name__).info("Structured logging configured")
except Exception:
    logging.basicConfig(level=logging.INFO)

# ── Observability & Rate Limiting Middleware ──────────────────
try:
    from middleware.rate_limit import RateLimitMiddleware
    from observability import ObservabilityMiddleware, metrics_endpoint
    app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)
    app.add_middleware(ObservabilityMiddleware)
    # Metrics endpoint (not under /api to be scraped)
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])
except Exception as e:
    logging.getLogger(__name__).warning(f"Observability/rate-limit middleware not available: {e}")

# ── Register Routers ──────────────────────────────────────────

app.include_router(auth_router, tags=["authentication"])
app.include_router(discord_router, tags=["authentication"])
app.include_router(steam_router, tags=["authentication"])
app.include_router(score_router, prefix="/api", tags=["scores"])
app.include_router(leaderboard_router, prefix="/api", tags=["leaderboards"])
app.include_router(profile_router, prefix="/api", tags=["profiles"])
app.include_router(streamer_router, prefix="/api", tags=["streamer"])
app.include_router(cheat_router, prefix="/api", tags=["cheat"])
app.include_router(ranked_router, prefix="/api", tags=["ranked"])
app.include_router(admin_router, prefix="/api", tags=["admin"])
app.include_router(admin_panel_router, prefix="/admin", tags=["admin-panel"])
app.include_router(multiplayer_router, tags=["multiplayer"])
app.include_router(social_router, prefix="/api", tags=["social"])

# ── Health Check Endpoint ─────────────────────────────────────

@app.get("/api/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for server status.
    Used by game clients to verify server is online.
    """
    # Basic DB ping
    db_ok = False
    queue_status = None
    try:
        from database import get_connection
        conn = get_connection()
        try:
            conn.ping()
            db_ok = True
        finally:
            conn.close()
    except Exception:
        db_ok = False

    # Try to get matchmaking queue size
    try:
        from websocket.matchmaking import get_matchmaking_manager
        mgr = get_matchmaking_manager()
        qs = await mgr.get_queue_status()
        queue_status = qs
    except Exception:
        queue_status = None

    return {
        "status": "ok" if db_ok else "degraded",
        "version": APP_VERSION,
        "service": "SubLadder Server API",
        "database": {"ok": db_ok},
        "matchmaking": queue_status,
    }

# ── Root Endpoint ─────────────────────────────────────────────

@app.get("/", tags=["info"])
async def root():
    """API information endpoint."""
    return {
        "service": APP_TITLE,
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "auth": "/auth",
            "scores": "/api",
            "leaderboard": "/api/leaderboard",
            "profile": "/api/profile",
            "ranked": "/api/ranked",
            "multiplayer": "/api/multiplayer",
            "social": "/api/social",
            "admin": "/api/admin",
        }
    }

# ── Error Handlers ────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    if DEBUG:
        print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ── Startup/Shutdown ──────────────────────────────────────────

# Global scheduler instance
_scheduler = None

@app.on_event("startup")
async def startup_event():
    """Run on server startup."""
    global _scheduler
    
    print(f"✅ {APP_TITLE} v{APP_VERSION} starting up...")
    print(f"📊 Debug mode: {'ON' if DEBUG else 'OFF'}")
    print(f"🌐 Available endpoints:")
    print(f"   - Health check: GET /api/health")
    print(f"   - Auth: POST /auth/register, /auth/login")
    print(f"   - Scores: POST /api/score")
    print(f"   - Leaderboard: GET /api/leaderboard")
    print(f"   - Profile: GET /api/profile")
    print(f"   - Ranked: GET/POST /api/ranked/*")
    print(f"   - Multiplayer: WS /api/multiplayer/ws (+ REST endpoints)")
    print(f"   - API Docs: GET /docs")
    
    # Start ranked scheduler for daily tasks (decay, rank resets)
    try:
        from scheduler import RankedScheduler
        _scheduler = RankedScheduler(get_db)
        _scheduler.start()
    except Exception as e:
        print(f"⚠️  Warning: Failed to start scheduler: {e}")
    
    # Start matchmaking cleanup scheduler
    try:
        from websocket.matchmaking import get_matchmaking_manager
        manager = get_matchmaking_manager()
        
        async def cleanup_matchmaking():
            """Cleanup expired rooms and waitlist entries every 60 seconds."""
            while True:
                try:
                    await manager.cleanup()
                    await asyncio.sleep(60)
                except Exception as e:
                    print(f"⚠️  Matchmaking cleanup error: {e}")
                    await asyncio.sleep(60)
        
        asyncio.create_task(cleanup_matchmaking())
        print(f"✅ Matchmaking cleanup scheduler started")
    except Exception as e:
        print(f"⚠️  Warning: Failed to start matchmaking scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown."""
    global _scheduler
    
    if _scheduler:
        _scheduler.stop()
    
    print(f"👋 {APP_TITLE} shutting down...")

# ── Main Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    WORKERS = int(os.getenv("WORKERS", "4"))
    
    print(f"\n{'='*60}")
    print(f"  Sub Ladder Server v{APP_VERSION}")
    print(f"  Starting on {HOST}:{PORT}")
    print(f"  Workers: {WORKERS}")
    print(f"{'='*60}\n")
    
    # Start server
    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        workers=WORKERS,
        reload=DEBUG,
        log_level="info"
    )
