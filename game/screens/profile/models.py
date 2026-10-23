"""
game/screens/profile/models.py — Types de données pour le système de profil.
"""

from enum import Enum


class ProfileType(str, Enum):
    """Type de profil."""
    OFFLINE = "offline"
    ONLINE = "online"


class LinkType(str, Enum):
    """Type de liaison de compte."""
    EMAIL = "email"
    DISCORD = "discord"
    STEAM = "steam"
