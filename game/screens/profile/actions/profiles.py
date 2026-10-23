"""
game/screens/profile/actions/profiles.py — Actions sur les profils (create/delete/select).
"""

import tkinter as tk
from tkinter import simpledialog, messagebox
from functools import partial

from constants import GOLD, BG_DARK, BG_PANEL, SILVER, WHITE, LIFELINE_ON
from utils import log_ui_exception


def create_offline_profile(app, active_profile_name: str = None):
    """Créer un nouveau profil offline. Hérite les stats du profil actif si fourni."""
    lang = app._lang.get("code", "en")
    name = simpledialog.askstring(
        app.s("profile_title") if hasattr(app, 's') else "Profile",
        app.s("enter_name") if hasattr(app, 's') else "Enter profile name",
        parent=app
    )
    if name is None:
        return None
    name = name.strip()
    if not name:
        messagebox.showerror("", app.s("name_empty") if hasattr(app, 's') else "Name cannot be empty.", parent=app)
        return None
    if name in app.data["profiles"]:
        messagebox.showerror("", app.s("name_taken") if hasattr(app, 's') else "Name already taken.", parent=app)
        return None

    # Hériter les stats du profil actif si fourni
    inherited = None
    if active_profile_name and active_profile_name in app.data["profiles"]:
        inherited = app.data["profiles"][active_profile_name]

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
    return name


def create_new_profile(app):
    """Ouvrir le sélecteur de type de profil pour créer un nouveau profil."""
    from .profiles import create_offline_profile
    from ..submenus.type_picker import show_type_picker

    show_type_picker(app, on_offline=partial(_on_create_offline, app))


def _on_create_offline(app):
    """Créer un profil offline après sélection."""
    active = app.data.get("active_profile")
    name = create_offline_profile(app, active)
    if name:
        from .build import build
        app.after_idle(partial(_safe_rebuild_profile, app, build))


def delete_profile(app, name: str):
    """Supprimer un profil."""
    lang = app._lang.get("code", "en")
    if not messagebox.askyesno("", app.s("confirm_delete", name=name) if hasattr(app, 's') else f"Delete profile '{name}'?", parent=app):
        return
    del app.data["profiles"][name]
    remaining = list(app.data["profiles"].keys())
    app.data["active_profile"] = remaining[0] if remaining else None
    from utils import save_data
    save_data(app.data, silent=True)
    from .build import build
    app.after_idle(partial(_safe_rebuild_profile, app, build))


def select_profile(app, name: str):
    """Sélectionner un profil."""
    app.data["active_profile"] = name
    from utils import save_data
    save_data(app.data, silent=True)
    from .build import build
    app.after_idle(partial(_safe_rebuild_profile, app, build))


def _safe_rebuild_profile(app, build_func):
    """Rebuild the profile screen and log any exception that would be hidden in frozen builds."""
    try:
        build_func(app)
    except Exception as exc:
        log_ui_exception("profile.actions.profiles.rebuild", exc)
        messagebox.showerror(
            "",
            "An error occurred while opening the profile screen. Check the UI error log in AppData\\Roaming\\SubLadder.",
            parent=app,
        )
