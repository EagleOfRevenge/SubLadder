"""
menu.py — build() : Menu principal du jeu.

Orchestre les modules du package menu pour afficher le menu principal
avec navigation clavier/souris, profil utilisateur, et sous-menus.
"""

import tkinter as tk
import webbrowser

from constants import GAME_MODES, DISCORD_URL, GAME_VERSION


def build(app):
    """Construire l'écran du menu principal."""
    app._clear()
    app._timer_stop()
    app.sound.play_music("menu")

    f = app._container

    # Background image
    bg_img = app.images.background(
        "menu", size=(app.winfo_width() or 900, app.winfo_height() or 720))
    if bg_img:
        lbl = tk.Label(f, image=bg_img, bg=app.BG_DARK)
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        lbl._img_ref = bg_img

    app.title(app.s("title"))

    tk.Label(f, text="✦  Sub Ladder  ✦",
             bg=app.BG_DARK, fg=app.GOLD, font=app.f_title).pack(pady=(40, 6))

    # Section profil
    from .profile_display import build_profile_section
    profile_section = build_profile_section(app, f)
    from ..friend_list import build as build_friend_list
    build_friend_list(app, f)

    # Save hint
    sv = app.data.get("save")
    mode_color = None
    save_hint = None
    if sv:
        mode_id = sv.get("mode", "normal")
        mode_info = GAME_MODES.get(mode_id, GAME_MODES["normal"])
        lang_code = app._lang.get("code", "en")
        mode_label = mode_info.get(f"label_{lang_code}", mode_info["label_en"])
        mode_color = mode_info["color"]
        level = sv.get("level", "?")
        save_hint = f"{mode_label}  ·  Q{level} / 15"

    # Items du menu avec leurs commandes
    menu_items = [
        ("singleplayer", app.s("singleplayer"), app.show_singleplayer_submenu),
        ("multiplayer", app.s("multiplayer"), app.show_multiplayer_submenu),
        ("ranked", app.s("ranked"), app.show_ranked),
        ("top_scores", app.s("top_scores"), app.show_top_scores),
        ("profile", app.s("profile"), app.show_profile),
        ("achievements", app.s("achievements"), app.show_achievements),
        ("options", app.s("options"), app.show_options),
        ("discord", app.s("discord"), lambda: webbrowser.open(DISCORD_URL)),
        ("quit", app.s("quit"), app.destroy),
    ]

    current_index = {"value": 0}
    animation_state = {"frame": 0, "active": False}

    # Container de navigation
    selector_frame = tk.Frame(f, bg=app.BG_DARK)
    selector_frame.pack(pady=12, expand=True)

    # Navigation hint
    lang_code = app._lang.get("code", "en")
    nav_hint = ("Use ↑/↓ or mouse wheel to browse, Enter/click to confirm"
                if lang_code == "en"
                else "Utilisez ↑/↓ ou la molette pour naviguer, Entrée/clic pour valider")
    tk.Label(selector_frame, text=nav_hint,
             bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack(pady=(0, 6))
    quick_tip = ("Tip: your profile and server status are shown here for a faster start"
                 if lang_code == "en"
                 else "Astuce : votre profil et l’état du serveur sont affichés ici pour démarrer plus vite")
    tk.Label(selector_frame, text=quick_tip,
             bg=app.BG_DARK, fg=app.TEXT_DISABLED, font=app.f_small).pack(pady=(0, 8))

    # Labels haut/bas + carte centrale
    top_label = tk.Label(selector_frame, text="",
                          bg=app.BG_DARK, fg=app.TEXT_DISABLED, font=app.f_menu_btn)
    top_label.pack(pady=(0, 4))

    current_card = tk.Frame(selector_frame, bg=app.BTN_SELECTED,
                            bd=0, highlightthickness=2,
                            highlightbackground=app.MENU_BTN_ACT,
                            padx=18, pady=16)
    current_card.pack(pady=6, fill="x", padx=30)

    current_active = tk.Frame(current_card, bg=app.BTN_SELECTED)
    current_active.pack(fill="x")

    arrow_label = tk.Label(current_active, text="▶", bg=app.BTN_SELECTED,
                           fg=app.GOLD, font=app.f_title)
    arrow_label.pack(side="left", padx=(0, 12))

    current_label = tk.Label(current_active, text="",
                             bg=app.BTN_SELECTED, fg=app.BG_DARK,
                             font=app.f_big, anchor="w")
    current_label.pack(side="left", fill="x", expand=True)

    bottom_label = tk.Label(selector_frame, text="",
                            bg=app.BG_DARK, fg=app.TEXT_DISABLED,
                            font=app.f_menu_btn)
    bottom_label.pack(pady=(4, 10))

    save_info = tk.Label(selector_frame, text="",
                         bg=app.BG_DARK, fg=app.SILVER,
                         font=app.f_small)
    save_info.pack(pady=(0, 10))

    counter_text = tk.Label(selector_frame, text="",
                            bg=app.BG_DARK, fg=app.SILVER,
                            font=app.f_small)
    counter_text.pack(pady=(0, 4))

    # Import des modules
    from .menu_renderer import pulse_widget, trigger_animation, render_menu
    from .menu_navigation import bind_menu_navigation

    # Callbacks
    def _move(delta):
        current_index["value"] = (current_index["value"] + delta) % len(menu_items)
        render_menu(app, current_index, menu_items, top_label, current_label,
                     bottom_label, save_info, counter_text, save_hint, mode_color)
        trigger_animation(app, animation_state, current_card, current_active, arrow_label, current_label)

    def _activate(event=None):
        _, _, command = menu_items[current_index["value"]]
        command()

    def _on_up(event=None):
        _move(-1)
        return "break"

    def _on_down(event=None):
        _move(1)
        return "break"

    def _on_enter(event=None):
        _activate()
        return "break"

    def _on_mousewheel(event):
        if hasattr(event, 'delta') and event.delta != 0:
            _move(-1 if event.delta > 0 else 1)
        elif getattr(event, 'num', None) == 4:
            _move(-1)
        elif getattr(event, 'num', None) == 5:
            _move(1)
        return "break"

    # Bindings
    bind_menu_navigation(
        app,
        f,
        move_up_callback=_on_up,
        move_down_callback=_on_down,
        activate_callback=_on_enter,
    )

    # Clics sur la carte
    current_card.bind("<Button-1>", _activate)
    current_active.bind("<Button-1>", _activate)
    current_label.bind("<Button-1>", _activate)
    arrow_label.bind("<Button-1>", _activate)
    top_label.bind("<Button-1>", lambda e: _move(-1))
    bottom_label.bind("<Button-1>", lambda e: _move(1))

    f.focus_set()

    # Premier rendu
    render_menu(app, current_index, menu_items, top_label, current_label,
                bottom_label, save_info, counter_text, save_hint, mode_color)

    # Version label — en bas à droite
    tk.Label(f, text=GAME_VERSION,
             bg=app.BG_DARK, fg=app.TEXT_DISABLED,
             font=app.f_small).place(relx=1.0, rely=1.0,
                                      anchor="se", x=-10, y=-8)

    # Server status — en bas à gauche
    server_online = app.data.get("server", {}).get("is_online", False)
    server_status = "🟢 Online" if server_online else "🔴 Offline"
    tk.Label(f, text=server_status,
             bg=app.BG_DARK, fg=("#44cc44" if server_online else "#cc4444"),
             font=app.f_small).place(relx=0.0, rely=1.0,
                                      anchor="sw", x=10, y=-8)
