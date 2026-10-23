"""
singleplayer_submenu.py — Sous-menu Singleplayer.

Affiche les options "Nouvelle Partie" et "Charger la partie"
pour le mode solo.
"""

import tkinter as tk


def build_singleplayer_submenu(app):
    """Construire le sous-menu Singleplayer."""
    app._clear()
    f = app._container
    lang_code = app._lang.get("code", "en")

    # Titre
    tk.Label(f, text="✦  Sub Ladder  ✦",
             bg=app.BG_DARK, fg=app.GOLD, font=app.f_title).pack(pady=(36, 4))

    subtitle_text = ("Singleplayer" if lang_code == "en"
                     else "Solo")
    tk.Label(f, text=subtitle_text,
             bg=app.BG_DARK, fg=app.SILVER, font=app.f_label).pack(pady=(0, 24))

    # Bouton "Nouvelle Partie"
    new_game_text = app.s("new_game")
    btn_new = _make_menu_button(app, f, new_game_text, app.start_new_game,
                                gold=True)
    btn_new.pack(pady=(4, 4))

    # Bouton "Charger la partie"
    load_game_text = app.s("load_game")
    btn_load = _make_menu_button(app, f, load_game_text, app.load_game)
    btn_load.pack(pady=(4, 4))

    # Save hint (si une sauvegarde existe)
    sv = app.data.get("save")
    if sv:
        from constants import GAME_MODES
        mode_id = sv.get("mode", "normal")
        mode_info = GAME_MODES.get(mode_id, GAME_MODES["normal"])
        mode_label = mode_info.get(f"label_{lang_code}", mode_info["label_en"])
        mode_color = mode_info["color"]
        level = sv.get("level", "?")
        save_hint = f"{mode_label}  ·  Q{level} / 15"
        tk.Label(f, text=save_hint,
                 bg=app.BG_DARK, fg=mode_color,
                 font=app.f_small).pack(pady=(12, 0))

    # Bouton "Retour"
    tk.Button(f, text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=6,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
              command=app.show_menu).pack(pady=(24, 0))


def _make_menu_button(app, parent, text, command, gold=False):
    """Créer un bouton de style menu avec hover effects."""
    from .color_utils import blend_colors

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
