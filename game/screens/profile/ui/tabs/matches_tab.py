"""
game/screens/profile/ui/tabs/matches_tab.py — Onglet Matches pour profil online.
"""

import tkinter as tk
import threading

from .....constants import BG_PANEL, SILVER, GOLD, WHITE


def build_matches_tab(remote_panel, app, profile_name: str):
    """Afficher l'onglet Matches pour un profil online."""
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
                result = api.get_profile_matches(profile_name, token, limit=20, offset=0)
                app.after(0, lambda: _display_matches(remote_panel, result, app))
            except Exception as e:
                app.after(0, lambda: _show_error(str(e)))

        threading.Thread(target=thread_fn, daemon=True).start()

    fetch_and_show()


def _display_matches(remote_panel, res, app):
    _clear_remote(remote_panel)
    if isinstance(res, dict) and res.get("error"):
        tk.Label(remote_panel, text="Unable to load match history.", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
        tk.Label(remote_panel, text=str(res["error"]), bg=BG_PANEL, fg=SILVER, font=app.f_small, wraplength=520, justify="left").pack(pady=(0, 8))
        return
    if not isinstance(res, list):
        tk.Label(remote_panel, text="No matches available", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
        return
    for m in res[:20]:
        txt = f"{m.get('match_id')}  {m.get('opponent_name')}  {m.get('result')}  ({m.get('elo_change')})  {m.get('match_date', '')[:19]}"
        tk.Label(remote_panel, text=txt, bg=BG_PANEL, fg=WHITE, font=app.f_small, anchor="w").pack(anchor="w", padx=8, pady=2)


def _clear_remote(remote_panel):
    for w in remote_panel.winfo_children():
        w.destroy()


def _show_error(msg):
    from tkinter import messagebox
    messagebox.showerror("", msg)
