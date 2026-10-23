"""
game/screens/profile/ui/tabs/achievements_tab.py — Onglet Achievements intégré au profil.
"""

import tkinter as tk

from constants import BG_PANEL, SILVER, GOLD, WHITE


def build_achievements_tab(remote_panel, app, profile_name: str):
    """Afficher les succès du profil dans l'onglet Profil."""
    for widget in remote_panel.winfo_children():
        widget.destroy()

    profile = app.data.get("profiles", {}).get(profile_name, {})
    unlocked = set(profile.get("achievements", []))
    total = len(getattr(app, "ach_defs", []))
    done = len(unlocked)
    pct = int(done / max(total, 1) * 100)

    tk.Label(remote_panel, text=f"Achievements: {done}/{total} ({pct}%)",
             bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8, 4))

    if not getattr(app, "ach_defs", []):
        tk.Label(remote_panel, text="No achievements available", bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(anchor="w", padx=8, pady=4)
        return

    for ach in app.ach_defs:
        is_unlocked = ach["id"] in unlocked
        icon = "🏆" if is_unlocked else "🔒"
        name = ach.get("name", {}).get(app._lang.get("code", "en"), ach.get("name", {}).get("en", ach["id"]))
        tk.Label(remote_panel, text=f"{icon} {name}", bg=BG_PANEL, fg=WHITE if is_unlocked else SILVER, font=app.f_small, anchor="w").pack(anchor="w", padx=10, pady=2)
