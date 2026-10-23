from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
import os
import pymysql

from auth.jwt import _load_config, resolve_user_role
from database import get_db
from auth.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin-panel"])


def _require_admin(user):
    if not user or resolve_user_role(user.get("email")) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


class AdminPanelLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


@router.get("/", response_class=HTMLResponse)
async def admin_panel_index(user=Depends(get_current_user)):
    """Render the admin overview page for beta moderators."""
    _require_admin(user)
    return HTMLResponse(
        """
        <html>
          <head><title>SubLadder Admin</title></head>
          <body style='font-family:Arial;padding:24px;background:#10192e;color:#e8edf5'>
            <h1>SubLadder Admin Panel</h1>
            <p>Closed beta moderation tools are available here.</p>
            <ul>
              <li><a href='/admin/bans' style='color:#f5c842'>Manage bans</a></li>
              <li><a href='/admin/rank' style='color:#f5c842'>Adjust ranked ELO</a></li>
              <li><a href='/admin/health' style='color:#f5c842'>Health check</a></li>
            </ul>
            <p>All moderation actions should be logged and reviewed during the beta.</p>
          </body>
        </html>
        """
    )


@router.get("/bans", response_class=HTMLResponse)
async def admin_panel_bans(user=Depends(get_current_user), db: pymysql.Connection = Depends(get_db)):
    """Show the current active bans in a basic HTML table and expose a simple form."""
    _require_admin(user)
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT id, profile_id, reason, banned_by, created_at, expires_at, active FROM bans WHERE active = 1 ORDER BY created_at DESC LIMIT 50"
        )
        bans = cursor.fetchall()

    rows = "".join(
        f"<tr><td>{b['id']}</td><td>{b.get('profile_id') or '-'}</td><td>{b.get('reason') or '-'}</td><td>{b.get('banned_by') or '-'}</td><td>{b.get('created_at')}</td><td>{b.get('expires_at') or 'Permanent'}</td></tr>"
        for b in bans
    )
    body = f"""
    <html><head><title>SubLadder Bans</title></head>
    <body style='font-family:Arial;padding:24px;background:#10192e;color:#e8edf5'>
      <h1>Active bans</h1>
      <p><a href='/admin/' style='color:#f5c842'>Back</a></p>
      <form method='post' action='/admin/bans' style='margin-bottom:20px'>
        <label>Profile ID: <input type='number' name='profile_id' required></label><br><br>
        <label>Reason: <input type='text' name='reason' maxlength='255' required></label><br><br>
        <label>Expires (YYYY-MM-DD HH:MM:SS, optional): <input type='text' name='expires_at'></label><br><br>
        <button type='submit'>Ban profile</button>
      </form>
      <form method='post' action='/admin/unban' style='margin-bottom:20px'>
        <label>Ban ID: <input type='number' name='ban_id' required></label>
        <button type='submit'>Unban</button>
      </form>
      <table border='1' cellspacing='0' cellpadding='6'>
        <tr><th>ID</th><th>Profile</th><th>Reason</th><th>Banned by</th><th>Created</th><th>Expires</th></tr>
        {rows or '<tr><td colspan=6>No active bans</td></tr>'}
      </table>
    </body></html>
    """
    return HTMLResponse(body)


@router.post("/bans")
async def admin_panel_create_ban(request: Request, user=Depends(get_current_user), db: pymysql.Connection = Depends(get_db)):
    """Create a simple ban from the admin panel form."""
    _require_admin(user)
    form = await request.form()
    profile_id = form.get("profile_id")
    reason = form.get("reason", "")
    expires_at = form.get("expires_at", "")

    if not profile_id or not str(profile_id).strip():
        raise HTTPException(status_code=400, detail="profile_id required")
    if not reason or not str(reason).strip():
        raise HTTPException(status_code=400, detail="reason required")

    try:
        profile_id_int = int(str(profile_id).strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="profile_id must be an integer") from exc

    expires_dt = None
    if str(expires_at).strip():
        try:
            expires_dt = str(expires_at).strip()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="expires_at invalid") from exc

    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO bans (profile_id, reason, banned_by, created_at, expires_at, active) VALUES (%s, %s, %s, NOW(), %s, 1)",
            (profile_id_int, str(reason).strip(), user.get("email") or "admin", expires_dt)
        )
    db.commit()
    return RedirectResponse(url="/admin/bans", status_code=303)


@router.post("/unban")
async def admin_panel_unban(request: Request, user=Depends(get_current_user), db: pymysql.Connection = Depends(get_db)):
    """Remove an active ban from the admin panel."""
    _require_admin(user)
    form = await request.form()
    ban_id = form.get("ban_id")
    if not ban_id or not str(ban_id).strip():
        raise HTTPException(status_code=400, detail="ban_id required")
    try:
        ban_id_int = int(str(ban_id).strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ban_id must be an integer") from exc

    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE bans SET active = 0, lifted_at = NOW(), lift_reason = %s WHERE id = %s",
            (f"Removed by {user.get('email') or 'admin'}", ban_id_int)
        )
    db.commit()
    return RedirectResponse(url="/admin/bans", status_code=303)


@router.get("/rank", response_class=HTMLResponse)
async def admin_panel_rank(user=Depends(get_current_user), db: pymysql.Connection = Depends(get_db)):
    """Show a basic ranked overview for moderators."""
    _require_admin(user)
    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT p.game_name, e.elo, e.games_played, e.games_won FROM elo_ratings e JOIN profiles p ON p.id = e.profile_id ORDER BY e.elo DESC LIMIT 20"
        )
        rows = cursor.fetchall()

    table_rows = "".join(
        f"<tr><td>{r['game_name']}</td><td>{r['elo']}</td><td>{r['games_played']}</td><td>{r['games_won']}</td></tr>"
        for r in rows
    )
    body = f"""
    <html><head><title>SubLadder Ranked</title></head>
    <body style='font-family:Arial;padding:24px;background:#10192e;color:#e8edf5'>
      <h1>Ranked overview</h1>
      <p><a href='/admin/' style='color:#f5c842'>Back</a></p>
      <table border='1' cellspacing='0' cellpadding='6'>
        <tr><th>Profile</th><th>ELO</th><th>Games</th><th>Wins</th></tr>
        {table_rows or '<tr><td colspan=4>No ranked data</td></tr>'}
      </table>
    </body></html>
    """
    return HTMLResponse(body)


@router.get("/health", response_class=HTMLResponse)
async def admin_panel_health(user=Depends(get_current_user)):
    """Small health check endpoint for the admin panel."""
    _require_admin(user)
    return HTMLResponse("<p>Admin panel healthy</p>")
