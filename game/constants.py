"""
constants.py — Sub Ladder
All shared constants: colors, prize ladder, game modes, XP system, resolutions.
"""

import math

# ══════════════════════════════════════════════════════════════════
# PRIZE LADDER
# ══════════════════════════════════════════════════════════════════

PRIZE_LADDER = [
    "1 sub",    # Q1
    "2 subs",   # Q2
    "3 subs",   # Q3
    "5 subs",   # Q4
    "10 subs",  # Q5  🔒 safe haven
    "15 subs",  # Q6
    "20 subs",  # Q7
    "30 subs",  # Q8
    "40 subs",  # Q9
    "50 subs",  # Q10 🔒 safe haven
    "60 subs",  # Q11
    "70 subs",  # Q12
    "80 subs",  # Q13
    "90 subs",  # Q14
    "100 subs", # Q15 🏆
]

PRIZE_VALUES = [1, 2, 3, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100]
SAFE_HAVENS  = {5, 10}
ANSWER_LABELS = ["A", "B", "C", "D"]
ANIMATION_MS  = 1200
QUESTION_TIME = 30   # seconds for visual countdown (0 = disabled)

# ══════════════════════════════════════════════════════════════════
# GAME MODES
# ══════════════════════════════════════════════════════════════════

GAME_MODES = {
    "easy":      {"key": "level_easy",      "label_en": "Easy",      "label_fr": "Facile",     "color": "#4caf50"},
    "normal":    {"key": "level_normal",     "label_en": "Normal",    "label_fr": "Normal",     "color": "#f5c842"},
    "hard":      {"key": "level_hard",       "label_en": "Hard",      "label_fr": "Difficile",  "color": "#ef5350"},
    "legendary": {"key": "level_legendary",  "label_en": "Legendary", "label_fr": "Légendaire", "color": "#aa00ff"},
}

# ══════════════════════════════════════════════════════════════════
# RESOLUTIONS
# ══════════════════════════════════════════════════════════════════

RESOLUTIONS = [
    ("900 × 720",   900,   720),
    ("1024 × 768",  1024,  768),
    ("1280 × 800",  1280,  800),
    ("1920 × 1080", 1920,  1080),
    ("3840 × 2160", 3840,  2160),   # 4K
]

# ══════════════════════════════════════════════════════════════════
# COLORS
# ══════════════════════════════════════════════════════════════════

BG_DARK           = "#0a0e1a"
BG_MID            = "#10192e"
BG_PANEL          = "#141d30"
GOLD              = "#f5c842"
GOLD_DARK         = "#c8992a"
SILVER            = "#aab4c8"
WHITE             = "#e8edf5"
BTN_DEFAULT       = "#1a2540"
BTN_HOVER         = "#1e2d50"
BTN_SELECTED      = "#c87800"
BTN_CORRECT       = "#1a7a3a"
BTN_WRONG         = "#7a1a1a"
BTN_DISABLED      = "#111828"
TEXT_YELLOW       = "#f5c842"
TEXT_DISABLED     = "#3a4560"
LIFELINE_ON       = "#1a2d50"
LIFELINE_OFF      = "#111828"
LIFELINE_TEXT_ON  = "#f5c842"
LIFELINE_TEXT_OFF = "#2a3550"
MENU_BTN_BG       = "#1a2540"
MENU_BTN_FG       = "#e8edf5"
MENU_BTN_ACT      = "#f5c842"

# ── Color themes ──────────────────────────────────────────────────
# Each theme defines a full palette: backgrounds, accents, buttons, lifelines.
COLOR_THEMES = {
    "Dark Navy": {
        "BG_DARK": "#0a0e1a", "BG_MID": "#10192e", "BG_PANEL": "#141d30",
        "GOLD": "#f5c842", "SILVER": "#aab4c8",
        "BTN_DEFAULT": "#1a2540", "BTN_HOVER": "#1e2d50", "BTN_SELECTED": "#c87800",
        "BTN_CORRECT": "#1a7a3a", "BTN_WRONG": "#7a1a1a", "BTN_DISABLED": "#111828",
        "MENU_BTN_BG": "#1a2540", "MENU_BTN_FG": "#e8edf5", "MENU_BTN_ACT": "#f5c842",
        "LIFELINE_ON": "#1a2d50", "LIFELINE_OFF": "#111828",
        "LIFELINE_TEXT_ON": "#f5c842", "LIFELINE_TEXT_OFF": "#2a3550",
    },
    "Midnight Blue": {
        "BG_DARK": "#050a18", "BG_MID": "#0b1428", "BG_PANEL": "#0e1a36",
        "GOLD": "#64b5f6", "SILVER": "#90a4ae",
        "BTN_DEFAULT": "#0d1b3e", "BTN_HOVER": "#162a55", "BTN_SELECTED": "#4a90d9",
        "BTN_CORRECT": "#1a6a4a", "BTN_WRONG": "#6a1a1a", "BTN_DISABLED": "#0a1225",
        "MENU_BTN_BG": "#0d1b3e", "MENU_BTN_FG": "#d0e0f0", "MENU_BTN_ACT": "#64b5f6",
        "LIFELINE_ON": "#1a2d50", "LIFELINE_OFF": "#0a1225",
        "LIFELINE_TEXT_ON": "#64b5f6", "LIFELINE_TEXT_OFF": "#1a2540",
    },
    "Dark Red": {
        "BG_DARK": "#1a0505", "BG_MID": "#2a0808", "BG_PANEL": "#350a0a",
        "GOLD": "#ef9a9a", "SILVER": "#bcaaa4",
        "BTN_DEFAULT": "#2a0a0a", "BTN_HOVER": "#3d1010", "BTN_SELECTED": "#c85050",
        "BTN_CORRECT": "#1a6a3a", "BTN_WRONG": "#6a1a1a", "BTN_DISABLED": "#1a0808",
        "MENU_BTN_BG": "#2a0a0a", "MENU_BTN_FG": "#f0d0d0", "MENU_BTN_ACT": "#ef9a9a",
        "LIFELINE_ON": "#3a1010", "LIFELINE_OFF": "#1a0808",
        "LIFELINE_TEXT_ON": "#ef9a9a", "LIFELINE_TEXT_OFF": "#2a1515",
    },
    "Gold": {
        "BG_DARK": "#1a1400", "BG_MID": "#2a2000", "BG_PANEL": "#3a2d00",
        "GOLD": "#ffd700", "SILVER": "#d4af37",
        "BTN_DEFAULT": "#3a2d00", "BTN_HOVER": "#4d3d00", "BTN_SELECTED": "#b89000",
        "BTN_CORRECT": "#2a7a3a", "BTN_WRONG": "#7a1a1a", "BTN_DISABLED": "#2a2000",
        "MENU_BTN_BG": "#3a2d00", "MENU_BTN_FG": "#f0e0a0", "MENU_BTN_ACT": "#ffd700",
        "LIFELINE_ON": "#4d3d00", "LIFELINE_OFF": "#2a2000",
        "LIFELINE_TEXT_ON": "#ffd700", "LIFELINE_TEXT_OFF": "#3a2d00",
    },
    "Emerald": {
        "BG_DARK": "#001a0d", "BG_MID": "#002e17", "BG_PANEL": "#004225",
        "GOLD": "#50c878", "SILVER": "#a8d8a8",
        "BTN_DEFAULT": "#002a15", "BTN_HOVER": "#004225", "BTN_SELECTED": "#30a060",
        "BTN_CORRECT": "#1a8a4a", "BTN_WRONG": "#6a1a1a", "BTN_DISABLED": "#001a0d",
        "MENU_BTN_BG": "#002a15", "MENU_BTN_FG": "#d0f0d8", "MENU_BTN_ACT": "#50c878",
        "LIFELINE_ON": "#004225", "LIFELINE_OFF": "#001a0d",
        "LIFELINE_TEXT_ON": "#50c878", "LIFELINE_TEXT_OFF": "#002a15",
    },
    "Black": {
        "BG_DARK": "#000000", "BG_MID": "#0a0a0a", "BG_PANEL": "#141414",
        "GOLD": "#f5c842", "SILVER": "#b0b0b0",
        "BTN_DEFAULT": "#1a1a1a", "BTN_HOVER": "#2a2a2a", "BTN_SELECTED": "#c87800",
        "BTN_CORRECT": "#1a7a3a", "BTN_WRONG": "#7a1a1a", "BTN_DISABLED": "#0a0a0a",
        "MENU_BTN_BG": "#1a1a1a", "MENU_BTN_FG": "#e8e8e8", "MENU_BTN_ACT": "#f5c842",
        "LIFELINE_ON": "#1a1a1a", "LIFELINE_OFF": "#0a0a0a",
        "LIFELINE_TEXT_ON": "#f5c842", "LIFELINE_TEXT_OFF": "#2a2a2a",
    },
    "White": {
        "BG_DARK": "#f0f0f0", "BG_MID": "#d0d0d0", "BG_PANEL": "#c8c8c8",
        "GOLD": "#c8992a", "GOLD_DARK": "#a07820",
        "SILVER": "#5a6a7a", "WHITE": "#000000", "TEXT_DISABLED": "#8a9aaa",
        "BTN_DEFAULT": "#9a9a9a", "BTN_HOVER": "#1e2d50", "BTN_SELECTED": "#c87800",
        "BTN_CORRECT": "#1a7a3a", "BTN_WRONG": "#7a1a1a", "BTN_DISABLED": "#c0c0c0",
        "MENU_BTN_BG": "#1a2540", "MENU_BTN_FG": "#e8edf5", "MENU_BTN_ACT": "#c8992a",
        "LIFELINE_ON": "#1a2540", "LIFELINE_OFF": "#d0d0d0",
        "LIFELINE_TEXT_ON": "#f5c842", "LIFELINE_TEXT_OFF": "#5a6a7a",
    },
}

def apply_theme(theme_name: str):
    """Return a dict of color overrides for the given theme name."""
    return COLOR_THEMES.get(theme_name, COLOR_THEMES["Dark Navy"])

# ══════════════════════════════════════════════════════════════════
# XP & LEVEL SYSTEM
# ══════════════════════════════════════════════════════════════════

XP_PER_MODE = {"easy": 5, "normal": 10, "hard": 20, "legendary": 40}
XP_WIN_BONUS = {"easy": 50, "normal": 100, "hard": 200, "legendary": 500}

def xp_multiplier(question_level: int) -> int:
    if question_level <= 5:  return 1
    if question_level <= 10: return 2
    return 3

def xp_for_correct(mode: str, question_level: int) -> int:
    return XP_PER_MODE.get(mode, 10) * xp_multiplier(question_level)

def xp_to_next_level(current_level: int) -> int:
    raw = 100 * (current_level ** 1.5)
    return max(100, int(round(raw / 50) * 50))

def player_level_from_xp(total_xp: int) -> tuple:
    """Return (level, xp_in_current_level, xp_needed_for_next)."""
    level, accumulated = 1, 0
    while True:
        needed = xp_to_next_level(level)
        if accumulated + needed > total_xp:
            return level, total_xp - accumulated, needed
        accumulated += needed
        level += 1

LEVEL_TITLES = [
    (1,  {"en": "Novice",     "fr": "Novice"}),
    (5,  {"en": "Amateur",    "fr": "Amateur"}),
    (10, {"en": "Challenger", "fr": "Challenger"}),
    (15, {"en": "Expert",     "fr": "Expert"}),
    (20, {"en": "Master",     "fr": "Maître"}),
    (25, {"en": "Champion",   "fr": "Champion"}),
    (30, {"en": "Legend",     "fr": "Légende"}),
    (40, {"en": "Mythic",     "fr": "Mythique"}),
]

def player_title(level: int, lang: str = "en") -> str:
    title = LEVEL_TITLES[0][1]
    for min_lvl, names in LEVEL_TITLES:
        if level >= min_lvl:
            title = names
    return title.get(lang, title["en"])

# ══════════════════════════════════════════════════════════════════
# MISC
# ══════════════════════════════════════════════════════════════════

DISCORD_URL  = "https://discord.gg/YgQZTaxnPx"
GAME_VERSION = "Closed Beta 1"

# Default font configs (overridden by app instance at runtime)
FONT_FAMILY = "Arial"
FONT_SIZE_TITLE = 18
FONT_SIZE_LABEL = 14
FONT_SIZE_SMALL = 11
FONT_SIZE_MENU_BTN = 13

def f_title():
    import tkinter.font as tkfont
    return tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE_TITLE, weight="bold")

def f_label():
    import tkinter.font as tkfont
    return tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE_LABEL, weight="normal")

def f_small():
    import tkinter.font as tkfont
    return tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE_SMALL, weight="normal")

def f_menu_btn():
    import tkinter.font as tkfont
    return tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE_MENU_BTN, weight="bold")
