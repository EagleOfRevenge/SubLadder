"""
game/screens/profile/ui/tabs/ranking_tab.py — Onglet Ranking intégré au profil.
"""

import tkinter as tk

from constants import BG_PANEL, SILVER, GOLD, WHITE


def build_ranking_tab(remote_panel, app, profile_name: str):
    """Afficher le classement du joueur et sa division."""
    for widget in remote_panel.winfo_children():
        widget.destroy()

    profile = app.data.get("profiles", {}).get(profile_name, {})
    profile_type = profile.get("profile_type", "offline")

    if profile_type != "online":
        tk.Label(remote_panel, text="This profile is not linked to an online account yet.", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(anchor="w", padx=8, pady=8)
        return

    rank = profile.get("ranked_rank", {})
    rank_value = rank.get("rank", "N/A")
    percentile = rank.get("percentile", "N/A")
    division = rank.get("display", "Unranked")

    tk.Label(remote_panel, text=f"Ranked position: #{rank_value}", bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8, 4))
    tk.Label(remote_panel, text=f"Top {percentile}%", bg=BG_PANEL, fg=WHITE, font=app.f_small).pack(anchor="w", padx=8, pady=2)
    tk.Label(remote_panel, text=f"Division: {division}", bg=BG_PANEL, fg=WHITE, font=app.f_small).pack(anchor="w", padx=8, pady=2)
