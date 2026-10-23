"""
game/screens/profile/submenus/create_offline.py — Création de profil local.
"""

import tkinter as tk
from tkinter import simpledialog, messagebox

from constants import BG_DARK, BG_PANEL, GOLD, SILVER, WHITE, BTN_DEFAULT, LIFELINE_ON


def show_create_offline(app):
    """Afficher l'écran de création de profil local."""
    app._clear()
    
    f = app._container
    
    # Titre
    header = tk.Frame(f, bg=BG_DARK)
    header.pack(fill="x", pady=(24, 16))
    tk.Label(header, text="Profil local",
             bg=BG_DARK, fg=GOLD, font=app.f_title).pack()
    
    # Infos
    info = tk.Frame(f, bg=BG_DARK)
    info.pack(expand=True, fill="both", padx=40, pady=10)
    
    tk.Label(info, text="Le profil local conserve vos stats uniquement en local.",
             bg=BG_DARK, fg=SILVER, font=app.f_small).pack(pady=(10, 4))
    tk.Label(info, text="Aucune connexion internet requise.",
             bg=BG_DARK, fg=SILVER, font=app.f_small).pack(pady=(0, 10))
    
    # Nom du profil
    tk.Label(info, text="Nom du profil :",
             bg=BG_DARK, fg=GOLD, font=app.f_label).pack(pady=(10, 2))
    
    name_entry = tk.Entry(info, font=app.f_label, width=30, justify="center")
    name_entry.pack(pady=(0, 10))
    name_entry.focus_set()
    
    def on_enter(e=None):
        _do_create(app, name_entry.get())
    name_entry.bind("<Return>", on_enter)
    
    # Bouton créer
    create_btn = tk.Button(info, text="✅  Créer le profil",
                           bg=LIFELINE_ON, fg="white", font=app.f_prize_hl,
                           relief="flat", cursor="hand2", padx=20, pady=8,
                           command=lambda: _do_create(app, name_entry.get()))
    create_btn.pack(pady=8)
    
    def _enter(e=None):
        create_btn.config(bg="#55cc55")
    def _leave(e=None):
        create_btn.config(bg=LIFELINE_ON)
    create_btn.bind("<Enter>", _enter)
    create_btn.bind("<Leave>", _leave)
    
    # Bouton retour
    tk.Button(f, text="← Retour",
              bg=BTN_DEFAULT, fg=SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=8,
              command=app.show_profile).pack(pady=16)


def _do_create(app, name: str):
    """Créer le profil offline."""
    name = name.strip()
    if not name:
        messagebox.showerror("", "Name cannot be empty.", parent=app)
        return
    if name in app.data["profiles"]:
        messagebox.showerror("", "Name already taken.", parent=app)
        return
    
    active = app.data.get("active_profile")
    inherited = None
    if active and active in app.data["profiles"]:
        inherited = app.data["profiles"][active]
    
    new_profile = {
        "games_played": 0,
        "total_subs": 0,
        "best_game": 0,
        "correct_answers": 0,
        "achievements": [],
        "scores": [],
        "win_streak": 0,
        "total_xp": 0,
        "player_level": 1,
        "avatar": None,
        "profile_type": "offline",
    }
    
    app.data["profiles"][name] = new_profile
    app.data["active_profile"] = name
    from utils import save_data
    save_data(app.data, silent=True)
    
    from ..build import build
    build(app)
