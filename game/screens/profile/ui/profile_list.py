"""
game/screens/profile/ui/profile_list.py — Liste des profils avec avatars.
"""

import tkinter as tk
from functools import partial

from constants import GOLD, SILVER, WHITE, BTN_DEFAULT
from ui_helpers import create_scrollable_frame
from .avatar import load_profile_avatar


def build_profile_list(content_frame, app, on_select=None):
    """Construire la liste des profils. Retourne le frame de la liste."""
    profiles = app.data["profiles"]
    active = app.data.get("active_profile")
    
    list_frame = tk.Frame(content_frame, bg=app.BG_DARK)
    list_frame.pack(pady=8, fill="x", anchor="center")
    
    if profiles:
        for name in sorted(profiles.keys()):
            marker = "▶ " if name == active else "   "
            color = name == active and GOLD or SILVER
            
            profile_row = tk.Frame(list_frame, bg=app.BG_DARK)
            profile_row.pack(pady=2, fill="x", padx=30, anchor="center")
            
            avatar_img = load_profile_avatar(app, name, size=32)
            if avatar_img:
                avatar_lbl = tk.Label(profile_row, image=avatar_img, bg=app.BG_DARK)
                avatar_lbl.pack(side="left", padx=(0, 8))
                avatar_lbl._img_ref = avatar_img
            
            tk.Button(
                profile_row, text=f"{marker}{name}",
                bg=BTN_DEFAULT, fg=color, font=app.f_label,
                relief="flat", cursor="hand2", pady=6,
                command=partial(on_select, name) if on_select else None
            ).pack(side="left", fill="x", expand=True)
    else:
        tk.Label(list_frame, text="—", bg=app.BG_DARK, fg=SILVER,
                 font=app.f_label).pack(anchor="center")
    
    return list_frame
