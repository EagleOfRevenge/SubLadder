"""
mode_picker.py — build_mode_picker() : Sélecteur de difficulté.

Affiche les modes de jeu disponibles (Normal, Hard, Legendary)
avec verrouillage conditionnel du mode Legendary.
"""

import tkinter as tk

from constants import GAME_MODES


def build_mode_picker(app):
    """Construire l'écran de sélection de difficulté."""
    app._clear()
    f = app._container
    lang_code = app._lang.get("code", "en")

    tk.Label(f, text="✦  Sub Ladder  ✦",
             bg=app.BG_DARK, fg=app.GOLD, font=app.f_title).pack(pady=(36, 4))
    tk.Label(f,
             text=("Choose your difficulty" if lang_code == "en"
                   else "Choisissez la difficulté"),
             bg=app.BG_DARK, fg=app.SILVER, font=app.f_label).pack(pady=(0, 24))

    profile = app.data.get("active_profile")
    p = app.data["profiles"].get(profile, {}) if profile else {}
    legendary_unlocked = p.get("legendary_unlocked", False)

    for mode_id, info in GAME_MODES.items():
        locked = (mode_id == "legendary" and not legendary_unlocked)
        label = info.get(f"label_{lang_code}", info["label_en"])
        color = info["color"] if not locked else app.TEXT_DISABLED
        text = label if not locked else f"🔒  {label}"

        btn_frame = tk.Frame(f, bg=app.BG_DARK)
        btn_frame.pack(pady=5)

        btn = tk.Button(
            btn_frame, text=text,
            bg=app.BTN_DEFAULT if not locked else app.BTN_DISABLED,
            fg=color,
            font=app.f_menu_btn,
            relief="flat",
            cursor="hand2" if not locked else "arrow",
            width=20, pady=10,
            activebackground=app.BTN_HOVER if not locked else app.BTN_DISABLED,
            activeforeground=color,
            highlightbackground=app.BTN_DEFAULT if not locked else app.BTN_DISABLED,
            highlightthickness=0,
            state="normal" if not locked else "disabled",
            command=lambda m=mode_id: app.start_new_game(mode=m)
        )
        btn.pack()

        if not locked:
            def _make_hover_handlers(button, normal_bg, hover_bg):
                def _on_enter(e=None):
                    button.config(bg=hover_bg, highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)

                def _on_leave(e=None):
                    button.config(bg=normal_bg, highlightbackground=normal_bg, highlightthickness=0)

                return _on_enter, _on_leave

            enter_handler, leave_handler = _make_hover_handlers(btn, app.BTN_DEFAULT, app.BTN_HOVER)
            btn.bind("<Enter>", enter_handler)
            btn.bind("<Leave>", leave_handler)

        if locked:
            hint = ("Win a Hard game to unlock" if lang_code == "en"
                    else "Gagnez une partie Difficile pour débloquer")
            tk.Label(btn_frame, text=hint, bg=app.BG_DARK,
                     fg=app.TEXT_DISABLED, font=app.f_small).pack()

    tk.Button(f, text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=6,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
              command=app.show_menu).pack(pady=24)
