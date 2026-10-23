"""
avatar.py — Chargement et redimensionnement d'avatars pour le menu.
"""

import os


def load_menu_avatar(app, profile_name: str, size: int = 48):
    """Charger et redimensionner l'avatar d'un profil.
    
    Retourne un PhotoImage PIL/Tk ou None si l'avatar n'existe pas.
    """
    try:
        from PIL import Image, ImageTk
        from utils import get_avatar_path
        
        profile = app.data["profiles"].get(profile_name, {})
        avatar_filename = profile.get("avatar")
        if not avatar_filename:
            return None
        
        avatar_path = get_avatar_path(avatar_filename)
        if not os.path.exists(avatar_path):
            return None
        
        img = Image.open(avatar_path).convert("RGBA")
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None
