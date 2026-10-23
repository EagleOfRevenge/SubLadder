"""
game/screens/profile/ui/sync_status.py — Indicateur de sync pour profil online.
"""

import tkinter as tk
import threading
import time
import datetime

from constants import BG_PANEL, BTN_DEFAULT, SILVER, GOLD, WHITE, BTN_CORRECT
from ui_helpers import create_scrollable_frame


def build_sync_section(content_frame, app, profile_name: str, profile: dict):
    """Construire la section de sync pour un profil online. Retourne le status_label."""
    ptype = profile.get("profile_type", "offline")
    
    if ptype != "online":
        return None
    
    # Sync status frame
    sync_status_frame = tk.Frame(content_frame, bg=app.BG_DARK)
    sync_status_frame.pack(pady=(2, 0), fill="x", anchor="center")
    
    ptype_icon = "🔒" if ptype == "online" else "📁"
    ptype_label_text = f"{ptype_icon}  Online Profile" if ptype == "online" else f"{ptype_icon}  Offline Profile"
    
    tk.Label(sync_status_frame, text=ptype_label_text,
             bg=app.BG_DARK, fg=SILVER, font=app.f_small).pack(side="left", padx=10)
    
    sync_status_label = tk.Label(sync_status_frame, text="", 
                                 bg=app.BG_DARK, fg=SILVER, font=app.f_small)
    sync_status_label.pack(side="right", padx=10)
    sync_status_label._sync_status = "idle"
    
    # Trigger sync in background
    _trigger_profile_sync(app, profile_name, sync_status_label)
    
    # Sync info panel
    sync_info = tk.Frame(content_frame, bg=BG_PANEL)
    sync_info.pack(pady=(4, 8), padx=30, fill="x")
    
    last_synced = profile.get("last_synced")
    if last_synced:
        sync_time = datetime.datetime.fromtimestamp(last_synced)
        time_diff = time.time() - last_synced
        
        if time_diff < 60:
            time_str = "just now"
        elif time_diff < 3600:
            time_str = f"{int(time_diff/60)}m ago"
        else:
            time_str = f"{int(time_diff/3600)}h ago"
        
        tk.Label(sync_info, text=f"Last sync: {time_str}",
                 bg=BG_PANEL, fg=SILVER, font=app.f_small, anchor="center").pack()
    else:
        tk.Label(sync_info, text="Never synced (click Sync button)",
                 bg=BG_PANEL, fg=SILVER, font=app.f_small, anchor="center").pack()
    
    # Sync Now button
    tk.Button(sync_status_frame, text="🔄 Sync",
              bg=BTN_DEFAULT, fg=SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=8, pady=2,
              command=lambda: _trigger_profile_sync(app, profile_name, sync_status_label, force=True)
              ).pack(side="right", padx=2)
    
    return sync_status_label


def _trigger_profile_sync(app, profile_name: str, status_label: tk.Label, force: bool = False):
    """Déclencher la sync du profil depuis le serveur en thread background."""
    from game.auth.client import APIClient
    from game.auth.cache import ProfileCache
    from utils import save_data
    
    profile = app.data["profiles"].get(profile_name, {})
    ptype = profile.get("profile_type", "offline")
    
    if ptype != "online":
        return
    
    user_id = profile.get("user_id")
    token = app.data.get("auth", {}).get("tokens", {}).get(profile_name)
    
    if not token:
        status_label.config(text="✗ No auth")
        if not force:
            return
    
    if not user_id:
        status_label.config(text="✗ No user ID")
        return
    
    if not hasattr(app, '_profile_cache'):
        app._profile_cache = ProfileCache(cache_duration=300)
    
    cache = app._profile_cache
    
    if cache.is_syncing(user_id) and not force:
        return
    
    if not force and cache.get(user_id):
        status_label.config(text="✓")
        return
    
    def sync_thread():
        error_msg = None
        try:
            cache.start_sync(user_id)
            status_label.config(text="⏳")
            status_label.update()
            
            api_client = APIClient()
            result = api_client.get_profile(token)
            
            if result.get("error"):
                error_msg = result["error"]
                cached = cache.get_stale(user_id)
                if cached:
                    status_label.config(text="✗")
                else:
                    status_label.config(text="✗")
                    raise Exception(f"Sync failed: {error_msg}")
                return
            
            profile_data = result.get("profile", {})
            if not profile_data:
                raise Exception("Empty profile data from server")
            
            app.data["profiles"][profile_name].update({
                "games_played": profile_data.get("games_played", 0),
                "total_xp": profile_data.get("level", 0) * 1000,
                "level": profile_data.get("level", 0),
                "total_score": profile_data.get("total_score", 0),
                "server_username": profile_data.get("game_name"),
                "last_synced": time.time(),
            })
            
            cache.set(user_id, profile_data)
            save_data(app.data, silent=True)
            
            status_label.config(text="✓", fg="#44cc44")
            
        except Exception as e:
            error_msg = str(e)
            cached = cache.get_stale(user_id)
            if cached:
                status_label.config(text="✗", fg="#cc8844")
            else:
                status_label.config(text="✗", fg="#cc4444")
                if app.data.get("debug"):
                    print(f"❌ Profile sync error: {error_msg}")
        finally:
            try:
                cache.end_sync(user_id)
                status_label.update()
            except:
                pass
    
    thread = threading.Thread(target=sync_thread, daemon=True)
    thread.start()
