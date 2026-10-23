"""
profile_display.py — Affichage du profil utilisateur dans le menu.
"""

import tkinter as tk

from constants import player_level_from_xp, player_title


def format_profile_subtitle(profile_data, lang_code, level_display, title=None, games_played=None):
    """Return a concise subtitle for the profile card in the main menu."""
    if not isinstance(profile_data, dict):
        return f"{'Level' if lang_code == 'en' else 'Niveau'} {level_display}"

    if profile_data.get("profile_type") == "online":
        games = profile_data.get("games_played", games_played if games_played is not None else 0)
        level = profile_data.get("level", level_display) or level_display
        games_word = "games" if lang_code == "en" else "parties"
        return f"{'Level' if lang_code == 'en' else 'Niveau'} {level} • {games} {games_word}"

    title_text = title or ""
    if title_text:
        return f"{'Level' if lang_code == 'en' else 'Niveau'} {level_display} ✦ {title_text}"
    return f"{'Level' if lang_code == 'en' else 'Niveau'} {level_display}"


def build_profile_section(app, parent):
    """Construire la section profil (avatar + nom + niveau + titre).
    
    Retourne le widget tk.Frame contenant le profil.
    """
    from .avatar import load_menu_avatar
    
    profile = app.data.get("active_profile")
    lang_code = app._lang.get("code", "en")
    
    profile_section = tk.Frame(parent, bg=app.BG_DARK)
    profile_section.pack(pady=(0, 12))
    
    if not profile:
        sub = "No profile selected" if lang_code == "en" else "Aucun profil sélectionné"
        tk.Label(profile_section, text=sub, bg=app.BG_DARK, fg=app.SILVER,
                 font=app.f_small).pack()
        return profile_section
    
    # Avatar
    avatar_img = load_menu_avatar(app, profile, size=48)
    if avatar_img:
        avatar_lbl = tk.Label(profile_section, image=avatar_img, bg=app.BG_DARK)
        avatar_lbl.pack(side="left", padx=(0, 12))
        avatar_lbl._img_ref = avatar_img
    
    # Données du profil
    p_data = app.data["profiles"].get(profile, {})
    ptype = p_data.get("profile_type", "offline")
    total_xp = p_data.get("total_xp", 0)
    plvl, _, _ = player_level_from_xp(total_xp)
    title = player_title(plvl, lang_code)
    
    profile_info = tk.Frame(profile_section, bg=app.BG_DARK)
    profile_info.pack(side="left")
    
    # Nom du profil
    profile_label = f"{profile}  {'🔒' if ptype == 'online' else '📁'}"
    tk.Label(profile_info, text=profile_label, bg=app.BG_DARK, fg=app.GOLD,
             font=app.f_label).pack(anchor="w")
    
    # Sous-titre (niveau + titre ou games jouées)
    if ptype == "online":
        games_played = p_data.get("games_played", 0)
        level_display = p_data.get("level", 0) or plvl
        sub = format_profile_subtitle(p_data, lang_code, level_display, games_played=games_played)

        # Statut de synchronisation
        sync_status = "✓"
        if hasattr(app, '_profile_cache'):
            cache = app._profile_cache
            user_id = p_data.get("user_id")
            if user_id:
                if cache.is_syncing(user_id):
                    sync_status = "⏳"
                elif cache.is_expired(user_id) and not cache.get_stale(user_id):
                    sync_status = "✗"
    else:
        sub = format_profile_subtitle(p_data, lang_code, plvl, title=title)
        sync_status = None

    tk.Label(profile_info, text=sub, bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_small).pack(anchor="w")
    
    if sync_status:
        tk.Label(profile_info, text=f"  {sync_status}", bg=app.BG_DARK, fg=app.SILVER,
                 font=app.f_small).pack(anchor="w")
    
    return profile_section
