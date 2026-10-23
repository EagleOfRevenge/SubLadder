"""
menu/ — Package de gestion du menu principal.

Exporte les fonctions principales pour afficher les écrans de menu.
"""

from .menu import build
from .mode_picker import build_mode_picker
from .singleplayer_submenu import build_singleplayer_submenu
from .multiplayer_submenu import build_multiplayer_submenu

__all__ = [
    "build",
    "build_mode_picker",
    "build_singleplayer_submenu",
    "build_multiplayer_submenu",
]
