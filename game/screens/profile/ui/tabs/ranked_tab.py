"""
game/screens/profile/ui/tabs/ranked_tab.py — Onglet Ranked pour profil online.
"""

import tkinter as tk
import threading

from .....constants import BG_PANEL, SILVER, GOLD, WHITE


def build_ranked_tab(remote_panel, app, profile_name: str):
    """Afficher l'onglet Ranked pour un profil online."""
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
                result = api.get_profile_ranked(profile_name, token)
                app.after(0, lambda: _display_ranked(remote_panel, result, app))
            except Exception as e:
                app.after(0, lambda: _show_error(str(e)))

        threading.Thread(target=thread_fn, daemon=True).start()

    fetch_and_show()


def _display_ranked(remote_panel, res, app):
    _clear_remote(remote_panel)
    if isinstance(res, dict) and res.get("error"):
        tk.Label(remote_panel, text="Unable to load ranked data.", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
        tk.Label(remote_panel, text=str(res["error"]), bg=BG_PANEL, fg=SILVER, font=app.f_small, wraplength=520, justify="left").pack(pady=(0, 8))
        return
    if not isinstance(res, dict):
        tk.Label(remote_panel, text="No ranked data available", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(pady=8)
        return
    pr = res.get('player_rank')
    gch = res.get('grand_champions', [])
    ch = res.get('champions', [])
    if pr:
        tk.Label(remote_panel, text=f"You: #{pr.get('rank')}  {pr.get('profile_name')}  {pr.get('elo')}",
                 bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(6, 2))
    tk.Label(remote_panel, text="Grand Champions", bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8, 2))
    for g in gch:
        tk.Label(remote_panel, text=f"#{g.get('rank')} {g.get('profile_name')} — {g.get('elo')}", bg=BG_PANEL, fg=WHITE, font=app.f_small).pack(anchor="w", padx=12)
    tk.Label(remote_panel, text="Champions", bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8, 2))
    for c in ch:
        tk.Label(remote_panel, text=f"#{c.get('rank')} {c.get('profile_name')} — {c.get('elo')}", bg=BG_PANEL, fg=WHITE, font=app.f_small).pack(anchor="w", padx=12)


def _clear_remote(remote_panel):
    for w in remote_panel.winfo_children():
        w.destroy()


def _show_error(msg):
    from tkinter import messagebox
    messagebox.showerror("", msg)
