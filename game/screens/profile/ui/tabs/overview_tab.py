"""
game/screens/profile/ui/tabs/overview_tab.py — Onglet Overview pour profil online.
"""

import tkinter as tk
import threading

from .....constants import BG_PANEL, SILVER, GOLD, WHITE


def build_overview_tab(remote_panel, app, profile_name: str):
    """Afficher l'onglet Overview pour un profil online."""
    _clear_remote(remote_panel)
    tk.Label(remote_panel, text=app.s("loading") if hasattr(app, 's') else "Loading...",
             bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
    tk.Label(remote_panel, text="Connecting to the server…",
             bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=(0, 4))
    tk.Label(remote_panel, text="This panel refreshes automatically when the profile is available.",
             bg=BG_PANEL, fg=SILVER, font=app.f_small, wraplength=520, justify="left").pack(pady=(0, 8))

    def _get_token():
        return app.data.get("auth", {}).get("tokens", {}).get(profile_name)

    def fetch_and_show():
        def thread_fn():
            try:
                from .....auth.client import APIClient
                api = APIClient()
            except Exception:
                from .....auth.client import APIClient
                api = APIClient()
            token = _get_token()
            if not token:
                app.after(0, lambda: _show_error(remote_panel, app, app.s("no_auth_token") if hasattr(app, 's') else "No auth token"))
                return
            try:
                result = api.get_profile_overview(profile_name, token)
                app.after(0, lambda: _display_overview(remote_panel, result, app))
            except Exception as e:
                app.after(0, lambda: _show_error(remote_panel, app, str(e)))

        threading.Thread(target=thread_fn, daemon=True).start()

    fetch_and_show()


def _display_overview(remote_panel, res, app):
    _clear_remote(remote_panel)
    if not isinstance(res, dict):
        tk.Label(remote_panel, text="No overview data available", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
        return
    if res.get("error"):
        tk.Label(remote_panel, text="Unable to load remote profile data.", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
        tk.Label(remote_panel, text="The server may be offline or the connection may have timed out.", bg=BG_PANEL, fg=SILVER, font=app.f_small, wraplength=520, justify="left").pack(pady=(0, 4))
        tk.Label(remote_panel, text=str(res["error"]), bg=BG_PANEL, fg=SILVER, font=app.f_small, wraplength=520, justify="left").pack(pady=(0, 8))
        return
    ov = res
    tk.Label(remote_panel, text=f"{ov.get('game_name', '')} — {ov.get('current_rank', {}).get('display', '')}",
             bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(pady=(8, 4), anchor="w")
    tk.Label(remote_panel, text=f"Ranked wins: {ov.get('ranked_wins', 0)}  ·  Games: {ov.get('games_played', 0)}  ·  Win%: {ov.get('win_rate', 0)}",
             bg=BG_PANEL, fg=WHITE, font=app.f_small).pack(pady=(0, 8), anchor="w")


def _clear_remote(remote_panel):
    for w in remote_panel.winfo_children():
        w.destroy()


def _show_error(remote_panel, app, msg):
    _clear_remote(remote_panel)
    tk.Label(remote_panel, text="Profile unavailable",
             bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(pady=(10, 6))
    tk.Label(remote_panel, text="The server may be offline or your session may have expired.",
             bg=BG_PANEL, fg=SILVER, font=app.f_small, wraplength=520, justify="left").pack(pady=(0, 8))
    tk.Label(remote_panel, text=msg,
             bg=BG_PANEL, fg=WHITE, font=app.f_small, wraplength=520, justify="left").pack(pady=(0, 4))
