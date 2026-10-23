"""
game/screens/profile/ui/tabs/top_players_tab.py — Onglet Top players intégré au profil.
"""

import tkinter as tk

from constants import BG_PANEL, SILVER, GOLD, WHITE


def build_top_players_tab(remote_panel, app, profile_name: str):
    """Afficher les meilleurs joueurs, en particulier les paliers Champion/Grand Champion."""
    for widget in remote_panel.winfo_children():
        widget.destroy()

    tk.Label(remote_panel, text="Top players", bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8, 4))
    tk.Label(remote_panel, text="Champion / Grand Champion", bg=BG_PANEL, fg=WHITE, font=app.f_small).pack(anchor="w", padx=8, pady=2)
    tk.Label(remote_panel, text="No leaderboard data available yet.", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(anchor="w", padx=8, pady=4)
