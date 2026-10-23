"""
game/screens/profile/submenus/type_picker.py — Écran de choix du type de profil.
"""

import tkinter as tk
from tkinter import font as tkfont

from constants import (
    BG_DARK, BG_PANEL, GOLD, SILVER, WHITE,
    BTN_DEFAULT, BTN_HOVER, MENU_BTN_BG, MENU_BTN_ACT,
    LIFELINE_ON, LIFELINE_TEXT_ON, BTN_CORRECT
)


def show_type_picker(app, on_offline=None, on_online=None):
    """Afficher l'écran de choix de type de profil."""
    app._clear()
    
    f = app._container
    
    # Titre
    header = tk.Frame(f, bg=BG_DARK)
    header.pack(fill="x", pady=(24, 16))
    tk.Label(header, text="Create New Profile",
             bg=BG_DARK, fg=GOLD, font=app.f_title).pack()
    
    # Panneau de choix
    picker_frame = tk.Frame(f, bg=BG_DARK)
    picker_frame.pack(expand=True, fill="both", padx=40, pady=20)
    
    tk.Label(picker_frame, text="Choose profile type:",
             bg=BG_DARK, fg=SILVER, font=app.f_label).pack(pady=(0, 16))
    
    # Bouton Profil local
    btn_local = tk.Button(
        picker_frame,
        text="📁  Profil local\n\n" + "Stats conservées localement\nAucune connexion requise",
        bg=LIFELINE_ON, fg=LIFELINE_TEXT_ON, font=app.f_prize_hl,
        relief="flat", cursor="hand2", padx=30, pady=20,
        width=28, height=4,
        command=lambda: _on_select(app, "offline", on_offline)
    )
    btn_local.pack(pady=8)
    _add_hover(btn_local, app)
    
    # Bouton Profil en ligne
    btn_online = tk.Button(
        picker_frame,
        text="🌐  Profil en ligne\n\n" + "Sync avec le serveur\nLier email / Discord / Steam",
        bg=BTN_DEFAULT, fg=GOLD, font=app.f_prize_hl,
        relief="flat", cursor="hand2", padx=30, pady=20,
        width=28, height=4,
        command=lambda: _on_select(app, "online", on_online)
    )
    btn_online.pack(pady=8)
    _add_hover(btn_online, app)
    
    # Bouton retour
    tk.Button(f, text="← Retour",
              bg=MENU_BTN_BG, fg=SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=8,
              command=app.show_profile).pack(pady=16)


def _on_select(app, profile_type, callback):
    """Gérer la sélection du type de profil."""
    if callback:
        callback()


def _add_hover(btn, app):
    """Ajouter les effets de survol sur un bouton."""
    def _enter(e=None):
        btn.config(bg=BTN_HOVER, highlightbackground=MENU_BTN_ACT, highlightthickness=2)
    def _leave(e=None):
        btn.config(bg=LIFELINE_ON if btn.cget("fg") == LIFELINE_TEXT_ON else BTN_DEFAULT,
                   highlightbackground=LIFELINE_ON, highlightthickness=0)
    btn.bind("<Enter>", _enter)
    btn.bind("<Leave>", _leave)
