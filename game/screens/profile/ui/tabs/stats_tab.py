"""
game/screens/profile/ui/tabs/stats_tab.py — Onglet Stats pour profil online.
"""

import tkinter as tk
import threading

from .....constants import BG_PANEL, SILVER, GOLD, WHITE


def build_stats_tab(remote_panel, app, profile_name: str):
    """Afficher l'onglet Stats pour un profil online."""
    _clear_remote(remote_panel)
    tk.Label(remote_panel, text=app.s("loading") if hasattr(app, 's') else "Loading...",
             bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)

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
            try:
                result = api.get_profile_stats(profile_name, token)
                app.after(0, lambda: _display_stats(remote_panel, result, app))
            except Exception as e:
                app.after(0, lambda: _show_error(str(e)))

        threading.Thread(target=thread_fn, daemon=True).start()

    fetch_and_show()


def _display_stats(remote_panel, res, app):
    _clear_remote(remote_panel)
    if isinstance(res, dict) and res.get("error"):
        tk.Label(remote_panel, text="Unable to load stats.", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
        tk.Label(remote_panel, text=str(res["error"]), bg=BG_PANEL, fg=SILVER, font=app.f_small, wraplength=520, justify="left").pack(pady=(0, 8))
        return
    if not isinstance(res, dict):
        tk.Label(remote_panel, text="No stats available", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
        return
    off = res.get("offline", {})
    on = res.get("online", {})
    tk.Label(remote_panel, text="Offline stats", bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(6, 2))
    tk.Label(remote_panel, text=f"Games: {off.get('games_played', 0)}  ·  Wins: {off.get('games_won', 0)}  ·  Win%: {off.get('win_rate', 0)}",
             bg=BG_PANEL, fg=WHITE, font=app.f_small).pack(anchor="w", padx=8)
    tk.Label(remote_panel, text="Online (ranked)", bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8, 2))
    tk.Label(remote_panel, text=f"ELO: {on.get('current_elo', 0)}  ·  Rank: {on.get('current_rank', {}).get('display', '')}  ·  Win%: {on.get('ranked_win_rate', 0)}",
             bg=BG_PANEL, fg=WHITE, font=app.f_small).pack(anchor="w", padx=8)


def _clear_remote(remote_panel):
    for w in remote_panel.winfo_children():
        w.destroy()


def _show_error(msg):
    from tkinter import messagebox
    messagebox.showerror("", msg)
