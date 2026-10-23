"""
Fonctions de gestion des mots de passe.
"""
import bcrypt

def _hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe hashé."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))