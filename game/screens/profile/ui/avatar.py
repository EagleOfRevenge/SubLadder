"""
game/screens/profile/ui/avatar.py — Chargement et affichage d'avatars.
"""

import os
import tkinter as tk


def load_profile_avatar(app, profile_name: str, size: int = 32):
    """Charger et redimensionner l'avatar d'un profil. Retourne un PhotoImage ou None."""
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


def create_avatar_display(parent, app, profile_name: str, size: int = 96):
    """Créer un widget d'affichage d'avatar. Retourne le frame contenant l'avatar."""
    avatar_frame = tk.Frame(parent, bg=app.BG_DARK)
    
    avatar_img = load_profile_avatar(app, profile_name, size)
    if avatar_img:
        avatar_lbl = tk.Label(avatar_frame, image=avatar_img, bg=app.BG_DARK)
        avatar_lbl.pack(pady=8)
        avatar_lbl._img_ref = avatar_img
    else:
        placeholder = tk.Label(avatar_frame, text="📷", bg=app.BG_DARK, 
                             fg=app.SILVER, font=("Arial", size // 2))
        placeholder.pack(pady=8)
    
    return avatar_frame
