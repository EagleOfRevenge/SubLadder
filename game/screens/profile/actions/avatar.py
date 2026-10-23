"""
game/screens/profile/actions/avatar.py — Changement d'avatar.
"""

import tkinter as tk
from tkinter import filedialog, messagebox

from utils import save_avatar, save_data


def change_avatar(app, profile_name: str):
    """Ouvrir un dialogue de sélection d'avatar pour le profil."""
    file_path = filedialog.askopenfilename(
        parent=app,
        title="Select avatar image",
        filetypes=[("PNG/JPG Images", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
    )
    
    if not file_path:
        return
    
    avatar_filename = save_avatar(file_path, profile_name)
    if not avatar_filename:
        messagebox.showerror("", "Invalid image file. Please use PNG or JPG (max 2MB).", parent=app)
        return
    
    old_avatar = app.data["profiles"][profile_name].get("avatar")
    if old_avatar and old_avatar != avatar_filename:
        from utils import delete_avatar
        delete_avatar(old_avatar)
    
    app.data["profiles"][profile_name]["avatar"] = avatar_filename
    save_data(app.data, silent=True)
    messagebox.showinfo("", "Avatar updated!", parent=app)
    
    from .build import build
    build(app)
