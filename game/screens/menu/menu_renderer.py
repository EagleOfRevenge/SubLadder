"""
menu_renderer.py — Rendu du menu interactif (navigation, animation).
"""

import tkinter as tk

from .color_utils import blend_colors


# Items du menu principal (ordre = ordre d'affichage)
# Chaque tuple: (id, cle_translation, commande_fallback)
# Les commandes réelles sont liées dynamiquement dans build()
MENU_ITEMS = [
    ("singleplayer", "singleplayer"),
    ("ranked", "ranked"),
    ("top_scores", "top_scores"),
    ("profile", "profile"),
    ("achievements", "achievements"),
    ("options", "options"),
    ("discord", "discord"),
    ("quit", "quit"),
]


def create_animation_state():
    """Créer un état d'animation initialisé."""
    return {"frame": 0, "active": False}


def pulse_widget(app, current_card, current_active, arrow_label, current_label, animation_state, step=0):
    """Animation de pulsation sur la carte sélectionnée."""
    if app is None or current_card is None or current_active is None or arrow_label is None or current_label is None:
        animation_state["active"] = False
        return

    steps = 8
    progress = step / steps
    brighten = blend_colors(app.BTN_SELECTED, app.BTN_HOVER, progress)
    arrow_color = blend_colors(app.GOLD, app.MENU_BTN_FG, progress)

    current_card.config(bg=brighten)
    current_active.config(bg=brighten)
    arrow_label.config(bg=brighten, fg=arrow_color)
    current_label.config(bg=brighten)

    if step < steps:
        app.after(16, lambda s=step + 1: pulse_widget(app, current_card, current_active,
                                                        arrow_label, current_label, animation_state, s))
    else:
        current_card.config(bg=app.BTN_SELECTED)
        current_active.config(bg=app.BTN_SELECTED)
        arrow_label.config(bg=app.BTN_SELECTED, fg=app.GOLD)
        current_label.config(bg=app.BTN_SELECTED)
        animation_state["active"] = False


def trigger_animation(app, animation_state, current_card, current_active, arrow_label, current_label):
    """Déclencher l'animation si pas déjà active."""
    if not animation_state["active"]:
        animation_state["active"] = True
        pulse_widget(app, current_card, current_active, arrow_label, current_label, animation_state, 0)


def render_menu(app, current_index, menu_items, top_label, current_label,
                bottom_label, save_info, counter_text, save_hint, mode_color):
    """Rendre le menu avec l'item courant sélectionné."""
    idx = current_index["value"]
    count = len(menu_items)
    prev_id, prev_text, _ = menu_items[(idx - 1) % count]
    cur_id, cur_text, _ = menu_items[idx]
    next_id, next_text, _ = menu_items[(idx + 1) % count]

    top_label.config(text=f"↑ {prev_text}")
    current_label.config(text=cur_text)
    bottom_label.config(text=f"↓ {next_text}")
    counter_text.config(text=f"{idx + 1} / {count}")

    if cur_id == "load_game" and save_hint:
        save_info.config(text=save_hint, fg=mode_color)
    else:
        save_info.config(text="", fg=app.SILVER)


def move_menu(current_index, delta):
    """Déplacer l'index de menu de delta positions."""
    current_index["value"] = (current_index["value"] + delta) % len(menu_items)


def activate_menu(current_index, menu_items):
    """Activer l'item de menu courant. Retourne la commande."""
    _, _, command = menu_items[current_index["value"]]
    return command
