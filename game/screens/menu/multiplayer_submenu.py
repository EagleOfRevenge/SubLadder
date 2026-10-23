"""
multiplayer_submenu.py — Sous-menu Multiplayer.

Affiche les options multiplayer disponibles : Ranked, Normal,
Streamer vs Viewer. Réservé aux comptes "online" (mail, Discord, Steam).
"""

import tkinter as tk


def build_multiplayer_submenu(app):
    """Construire le sous-menu Multiplayer."""
    app._clear()
    f = app._container
    lang_code = app._lang.get("code", "en")

    # Titre
    tk.Label(f, text="✦  Sub Ladder  ✦",
             bg=app.BG_DARK, fg=app.GOLD, font=app.f_title).pack(pady=(36, 4))

    subtitle_text = ("Multiplayer" if lang_code == "en"
                     else "Multijoueur")
    tk.Label(f, text=subtitle_text,
             bg=app.BG_DARK, fg=app.SILVER, font=app.f_label).pack(pady=(0, 24))

    # Vérification du profil online
    profile = app.data.get("active_profile")
    p = app.data["profiles"].get(profile, {}) if profile else {}
    profile_type = p.get("profile_type", "offline")

    # Items du sous-menu
    # Chaque tuple: (texte, commande, est_verrouillé, message_de_verrouillage)
    items = [
        (
            app.s("ranked"),
            app.show_ranked,
            False,  # Toujours accessible si online
            None,
        ),
        (
            app.s("multiplayer_normal", default="Normal"),
            app.show_multiplayer_normal,
            False,  # Toujours accessible si online
            None,
        ),
        (
            app.s("streamer_vs_viewer", default="Streamer vs Viewer"),
            app.show_streamer_vs_viewer,
            False,  # Toujours accessible si online
            None,
        ),
    ]

    # Si profil offline, tout est verrouillé
    if profile_type == "offline":
        hint_text = (
            "Online account required" if lang_code == "en"
            else "Compte en ligne requis"
        )
        for text, _, _, _ in items:
            btn_frame = tk.Frame(f, bg=app.BG_DARK)
            btn_frame.pack(pady=(4, 4))
            btn = tk.Button(
                btn_frame, text=f"🔒  {text}",
                bg=app.BTN_DISABLED, fg=app.TEXT_DISABLED,
                font=app.f_menu_btn,
                relief="flat", cursor="arrow",
                width=22, pady=10,
                state="disabled",
            )
            btn.pack()
            hint_lbl = tk.Label(btn_frame, text=hint_text, bg=app.BG_DARK,
                                fg=app.TEXT_DISABLED, font=app.f_small)
            hint_lbl.pack()

        # Bouton retour
        _add_back_button(f, app)
        return

    # Profil online : afficher les options
    for text, command, locked, hint in items:
        if locked:
            _add_locked_button(f, app, text, hint, lang_code)
        else:
            btn = _make_menu_button(app, f, text, command, gold=True)
            btn.pack(pady=(4, 4))

    # Bouton retour
    _add_back_button(f, app)


def _add_locked_button(parent, app, text, hint, lang_code):
    """Ajouter un bouton verrouillé avec hint."""
    btn_frame = tk.Frame(parent, bg=app.BG_DARK)
    btn_frame.pack(pady=(4, 4))
    btn = tk.Button(
        btn_frame, text=f"🔒  {text}",
        bg=app.BTN_DISABLED, fg=app.TEXT_DISABLED,
        font=app.f_menu_btn,
        relief="flat", cursor="arrow",
        width=22, pady=10,
        state="disabled",
    )
    btn.pack()
    if hint:
        hint_text = (hint if lang_code == "en"
                     else hint.replace("required", "requis"))
        tk.Label(btn_frame, text=hint_text, bg=app.BG_DARK,
                 fg=app.TEXT_DISABLED, font=app.f_small).pack()


def _add_back_button(parent, app):
    """Ajouter le bouton retour."""
    tk.Button(parent, text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=6,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
              command=app.show_menu).pack(pady=(24, 0))


def _make_menu_button(app, parent, text, command, gold=False):
    """Créer un bouton de style menu avec hover effects."""
    fg_normal = app.MENU_BTN_ACT if gold else app.MENU_BTN_FG
    fg_hover = app.MENU_BTN_ACT
    bg_normal = app.MENU_BTN_BG
    bg_hover = app.BTN_HOVER

    def _on_enter(e=None):
        btn.config(bg=bg_hover, fg=fg_hover,
                   highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)

    def _on_leave(e=None):
        btn.config(bg=bg_normal, fg=fg_normal,
                   highlightbackground=bg_normal, highlightthickness=0)

    btn = tk.Button(
        parent, text=text,
        bg=bg_normal, fg=fg_normal,
        font=app.f_menu_btn,
        relief="flat", cursor="hand2",
        width=22, pady=10,
        activebackground=bg_hover, activeforeground=fg_hover,
        highlightbackground=bg_normal, highlightthickness=0,
        command=command
    )
    btn.bind("<Enter>", _on_enter)
    btn.bind("<Leave>", _on_leave)
    return btn
