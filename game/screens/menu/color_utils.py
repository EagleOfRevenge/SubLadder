"""
color_utils.py — Utilitaires de colorimétrie pour le menu.
"""


def hex_to_rgb(value: str):
    """Convertir une chaîne HEX (#RRGGBB) en tuple RGB."""
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convertir un tuple RGB en chaîne HEX (#RRGGBB)."""
    return "#" + "".join(f"{min(255, max(0, c)):02x}" for c in rgb)


def blend_colors(from_hex: str, to_hex: str, fraction: float):
    """Mélanger deux couleurs HEX avec une fraction donnée (0.0 - 1.0)."""
    from_rgb = hex_to_rgb(from_hex)
    to_rgb = hex_to_rgb(to_hex)
    blended = tuple(int(from_rgb[i] + (to_rgb[i] - from_rgb[i]) * fraction)
                    for i in range(3))
    return rgb_to_hex(blended)
