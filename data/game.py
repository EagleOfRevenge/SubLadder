"""
Sub Ladder - v1.5
A "Who Wants to Be a Millionaire?" style quiz game.
Built with Python + tkinter.

Features:
  - First-run wizard: language + profile creation
  - Main menu with background images, Discord button
  - Multiple profiles with stats, export profil JSON
  - Save / Load mid-game
  - Top Scores, Achievements with unlock popups
  - Options: language, resolution/fullscreen, volume slider
  - Lifelines: 50/50, Chat Vote, Switch
  - Visual countdown timer per question
  - End-of-game recap screen (questions, correct/wrong, avg time)
  - Question source displayed after answer reveal
  - Dynamic backgrounds (calm → serious → tense) + music per level range
  - Sound engine with volume control
  - Robust error handling on startup

Run via run.py at the project root.
"""

import json
import os
import random
import time
import webbrowser
import tkinter as tk
from tkinter import font as tkfont, simpledialog, messagebox, filedialog

from asset_manager import SoundEngine, ImageLoader, ensure_assets, PYGAME_OK
from first_run import run_wizard

# ══════════════════════════════════════════════════════════════════
# PATHS
# ══════════════════════════════════════════════════════════════════

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))   # …/SubLadder/data/
LANG_DIR    = os.path.join(BASE_DIR, "languages")
Q_DIR       = os.path.join(BASE_DIR, "questions")
DATA_FILE   = os.path.join(BASE_DIR, "data.json")
ACH_FILE    = os.path.join(BASE_DIR, "achievements.json")

DISCORD_URL = "https://discord.gg/YgQZTaxnPx"

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
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

SAFE_HAVENS = {5, 10}

ANSWER_LABELS = ["A", "B", "C", "D"]
ANIMATION_MS  = 1200
QUESTION_TIME = 30   # seconds for the visual countdown timer (0 = disabled)

RESOLUTIONS = [
    ("900 × 720",  900,  720),
    ("1024 × 768", 1024, 768),
    ("1280 × 800", 1280, 800),
    ("1920 × 1080",1920, 1080),
]

# ── Language helpers ──────────────────────────────────────────────

def list_languages() -> list[str]:
    """Return language names discovered in data/languages/*.json"""
    names = []
    if os.path.isdir(LANG_DIR):
        for fname in sorted(os.listdir(LANG_DIR)):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(LANG_DIR, fname), encoding="utf-8") as f:
                        d = json.load(f)
                    names.append(d.get("name", fname.replace(".json", "")))
                except Exception:
                    pass
    return names or ["English"]


def load_language(name: str) -> dict:
    """Load the language file matching 'name', return its full dict."""
    if os.path.isdir(LANG_DIR):
        for fname in os.listdir(LANG_DIR):
            if fname.endswith(".json"):
                try:
                    path = os.path.join(LANG_DIR, fname)
                    with open(path, encoding="utf-8") as f:
                        d = json.load(f)
                    if d.get("name") == name:
                        return d
                except Exception:
                    pass
    # Minimal English fallback so the app always starts
    return {
        "code": "en", "name": "English",
        "questions_file": "en_questions.json",
        "ui": {}
    }

# Colors
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
TEXT_DISABLED     = "#3a4560"
LIFELINE_ON       = "#1a2d50"
LIFELINE_OFF      = "#111828"
LIFELINE_TEXT_ON  = "#f5c842"
LIFELINE_TEXT_OFF = "#2a3550"
MENU_BTN_BG       = "#1a2540"
MENU_BTN_FG       = "#e8edf5"
MENU_BTN_ACT      = "#f5c842"


# ══════════════════════════════════════════════════════════════════
# DATA PERSISTENCE  (data.json)
# ══════════════════════════════════════════════════════════════════

DEFAULT_DATA = {
    "options": {
        "language":   "English",
        "resolution": "900 × 720",
        "fullscreen": False,
        "volume":     0.7,
    },
    "active_profile": None,
    "profiles": {},
    # profiles[name] = {
    #   "games_played": int,
    #   "total_subs":   int,
    #   "best_game":    int,
    #   "correct_answers": int,
    #   "scores": [ {"subs": int, "level": int, "won": bool}, ... ]   # last 20
    # }
    "save": None,
    # save = {
    #   "profile":   str,
    #   "level":     int,
    #   "lifelines": {"fifty": bool, "vote": bool, "switch": bool},
    #   "safe_prize":int,
    #   "used_ids":  [str, ...],
    #   "question_id": str,
    #   "displayed": {"answers": {...}, "correct": str},
    #   "eliminated":  [str, ...]
    # }
}


def load_data() -> dict:
    import copy
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            for k, v in DEFAULT_DATA.items():
                if k not in d:
                    d[k] = v
            return d
        except (json.JSONDecodeError, OSError) as e:
            # Corrupted data.json — back it up and start fresh
            backup = DATA_FILE + ".bak"
            try:
                import shutil
                shutil.copy2(DATA_FILE, backup)
            except Exception:
                pass
    return copy.deepcopy(DEFAULT_DATA)


#def save_data(data: dict):
#    try:
#        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)  # IMPORTANT
#        with open(DATA_FILE, "w", encoding="utf-8") as f:
#            json.dump(data, f, indent=2, ensure_ascii=False)
#        print("✅ data.json created :", DATA_FILE)
#    except OSError as e:
#        print("❌ ERROR SAVE :", e)
def save_data(data: dict):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass   # silently fail if disk is read-only or full


# ══════════════════════════════════════════════════════════════════
# QUESTION HELPERS
# ══════════════════════════════════════════════════════════════════

def load_questions(questions_file: str) -> list[dict]:
    path = os.path.join(Q_DIR, questions_file)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        qs = data.get("questions", [])
        if not qs:
            raise ValueError(f"No questions found in {questions_file}")
        return qs
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        # Fallback: try English if another language's file is missing
        fallback = os.path.join(Q_DIR, "en_questions.json")
        if path != fallback and os.path.exists(fallback):
            with open(fallback, "r", encoding="utf-8") as f:
                return json.load(f).get("questions", [])
        raise RuntimeError(f"Cannot load questions: {e}")


def load_achievements() -> list[dict]:
    if os.path.exists(ACH_FILE):
        try:
            with open(ACH_FILE, encoding="utf-8") as f:
                return json.load(f).get("achievements", [])
        except Exception:
            pass
    return []


def build_displayed_question(q: dict) -> dict:
    wrong_three = random.sample(q["other_answers"], min(3, len(q["other_answers"])))
    four = [q["right_answer"]] + wrong_three
    random.shuffle(four)
    answers = {ANSWER_LABELS[i]: four[i] for i in range(4)}
    correct = next(k for k, v in answers.items() if v == q["right_answer"])
    return {"answers": answers, "correct": correct}


def get_pool(questions: list[dict], level: int, exclude: set) -> list[dict]:
    pool = [q for q in questions if q["level"] == level and q["id"] not in exclude]
    if not pool:
        pool = [q for q in questions if q["level"] == level]
    return pool


# ══════════════════════════════════════════════════════════════════
# GAME STATE
# ══════════════════════════════════════════════════════════════════

class GameState:
    def __init__(self, all_questions: list[dict]):
        self.all_questions = all_questions
        self.current_level  = 1
        self.used_ids       = set()
        self.lifelines      = {"fifty": True, "vote": True, "switch": True}
        self.current_q      = None
        self.displayed      = None
        self.eliminated     = set()
        self.safe_prize     = 0
        self.game_over      = False
        self.won            = False
        self.correct_this_game = 0
        self._pick()

    def _pick(self):
        pool = get_pool(self.all_questions, self.current_level, self.used_ids)
        self.current_q  = random.choice(pool)
        self.used_ids.add(self.current_q["id"])
        self.displayed  = build_displayed_question(self.current_q)
        self.eliminated = set()

    # ── Lifelines ──

    def fifty_fifty(self) -> set:
        correct = self.displayed["correct"]
        wrong   = [k for k in ANSWER_LABELS if k != correct]
        removed = set(random.sample(wrong, 2))
        self.eliminated = removed
        self.lifelines["fifty"] = False
        return removed

    def chat_vote(self) -> dict:
        correct = self.displayed["correct"]
        w       = max(35, 75 - (self.current_level - 1) * 3)
        active  = [k for k in ANSWER_LABELS if k not in self.eliminated]
        wrong_a = [k for k in active if k != correct]
        per_w   = (100 - w) // max(len(wrong_a), 1)
        votes   = {k: (0 if k in self.eliminated else (w if k == correct else per_w))
                   for k in ANSWER_LABELS}
        total   = sum(votes.values())
        votes   = {k: round(v / total * 100) for k, v in votes.items()}
        diff    = 100 - sum(votes.values())
        votes[correct] += diff
        self.lifelines["vote"] = False
        return votes

    def switch(self):
        self.lifelines["switch"] = False
        self._pick()

    # ── Answer ──

    def answer(self, label: str) -> bool:
        ok = self.displayed["correct"] == label
        if ok:
            self.correct_this_game += 1
            if self.current_level == 15:
                self.won = self.game_over = True
            else:
                if self.current_level in SAFE_HAVENS:
                    self.safe_prize = self.current_level
                self.current_level += 1
                self._pick()
        else:
            self.game_over = True
        return ok

    def walk_away(self):
        self.game_over = True

    # ── Serialise / deserialise (for save/load) ──

    def to_dict(self) -> dict:
        return {
            "level":       self.current_level,
            "used_ids":    list(self.used_ids),
            "lifelines":   dict(self.lifelines),
            "safe_prize":  self.safe_prize,
            "correct_this_game": self.correct_this_game,
            "question_id": self.current_q["id"],
            "displayed":   {
                "answers": dict(self.displayed["answers"]),
                "correct": self.displayed["correct"],
            },
            "eliminated":  list(self.eliminated),
        }

    @classmethod
    def from_dict(cls, all_questions: list[dict], d: dict) -> "GameState":
        gs = cls.__new__(cls)
        gs.all_questions = all_questions
        gs.current_level  = d["level"]
        gs.used_ids       = set(d["used_ids"])
        gs.lifelines      = dict(d["lifelines"])
        gs.safe_prize     = d["safe_prize"]
        gs.correct_this_game = d.get("correct_this_game", 0)
        gs.game_over      = False
        gs.won            = False
        gs.eliminated     = set(d["eliminated"])
        gs.current_q      = next(q for q in all_questions if q["id"] == d["question_id"])
        gs.displayed      = {
            "answers": dict(d["displayed"]["answers"]),
            "correct": d["displayed"]["correct"],
        }
        return gs

    # ── Props ──

    @property
    def prize_label(self):
        return PRIZE_LADDER[self.current_level - 1]

    @property
    def prize_value(self):
        return PRIZE_VALUES[self.current_level - 1]

    @property
    def safe_label(self):
        return PRIZE_LADDER[self.safe_prize - 1] if self.safe_prize else "0 subs"

    @property
    def safe_value(self):
        return PRIZE_VALUES[self.safe_prize - 1] if self.safe_prize else 0


# ══════════════════════════════════════════════════════════════════
# MAIN APPLICATION  (frame-switcher architecture)
# ══════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Asset generation (creates missing placeholders silently)
        ensure_assets()

        # Sound + image engines
        self.sound  = SoundEngine()
        self.images = ImageLoader()

        # Data
        is_first_run = not os.path.exists(DATA_FILE)
        self.data    = load_data()

        # First-run wizard (before window appears)
        if is_first_run:
            self.withdraw()
            lang, profile_name = run_wizard(list_languages(), self.images)
            self.data["options"]["language"] = lang
            if profile_name:
                self.data["profiles"][profile_name] = {
                    "games_played": 0,
                    "total_subs": 0,
                    "best_game": 0,
                    "correct_answers": 0,
                    "achievements": [], 
                    "scores": [], 
                    "win_streak": 0
                }
                self.data["active_profile"] = profile_name
            save_data(self.data)
            self.deiconify()

        self.ach_defs = load_achievements()
        self._load_lang()
        self._setup_fonts()

        # Apply volume from saved options
        self.sound.volume = self.data["options"].get("volume", 0.7)

        self.title(self.s("title"))
        self.configure(bg=BG_DARK)

        self._container = tk.Frame(self, bg=BG_DARK)
        self._container.pack(fill="both", expand=True)

        self._apply_resolution()
        self.show_menu()

    def _load_lang(self):
        """Load the language file for the currently selected language."""
        lang_name = self.data["options"].get("language", "English")
        self._lang = load_language(lang_name)
        qfile = self._lang.get("questions_file", "en_questions.json")
        self.all_questions = load_questions(qfile)
        self.game_state    = None

    # ── i18n helper ──

    def s(self, key: str, **kw) -> str:
        ui = self._lang.get("ui", {})
        tmpl = ui.get(key, key)
        return tmpl.format(**kw) if kw else tmpl

    # ── Fonts ──

    def _setup_fonts(self):
        fam   = next((f for f in ["Georgia", "Palatino", "Times New Roman"]
                      if f in tkfont.families()), "TkDefaultFont")
        body  = next((f for f in ["Helvetica", "Arial", "TkDefaultFont"]
                      if f in tkfont.families()), "TkDefaultFont")
        self.f_title    = tkfont.Font(family=fam,  size=18, weight="bold")
        self.f_menu_btn = tkfont.Font(family=body, size=13, weight="bold")
        self.f_question = tkfont.Font(family=fam,  size=13, weight="bold")
        self.f_answer   = tkfont.Font(family=body, size=11, weight="bold")
        self.f_prize    = tkfont.Font(family=body, size=9)
        self.f_prize_hl = tkfont.Font(family=body, size=9,  weight="bold")
        self.f_lifeline = tkfont.Font(family=body, size=10, weight="bold")
        self.f_small    = tkfont.Font(family=body, size=9)
        self.f_big      = tkfont.Font(family=fam,  size=22, weight="bold")
        self.f_label    = tkfont.Font(family=body, size=11)

    # ── Resolution ──

    def _apply_resolution(self):
        opts = self.data["options"]
        res_name = opts.get("resolution", "900 × 720")
        fs       = opts.get("fullscreen", False)

        if fs:
            self.attributes("-fullscreen", True)
            self.resizable(True, True)
            return

        self.attributes("-fullscreen", False)
        match = next((r for r in RESOLUTIONS if r[0] == res_name), None)
        if match:
            w, h = match[1], match[2]
        else:
            w, h = 900, 720
        self.resizable(False, False)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Frame switcher ──

    def _clear(self):
        for w in self._container.winfo_children():
            w.destroy()

    # ════════════════════════════════════════════
    # MAIN MENU
    # ════════════════════════════════════════════

    def show_menu(self):
        self._clear()
        self.sound.play_music("menu")
        f = self._container

        # Background image
        bg_img = self.images.background("menu", size=(self.winfo_width() or 900,
                                                       self.winfo_height() or 720))
        if bg_img:
            lbl = tk.Label(f, image=bg_img, bg=BG_DARK)
            lbl.place(x=0, y=0, relwidth=1, relheight=1)
            lbl._img_ref = bg_img
        self.title(self.s("title"))

        tk.Label(f, text="✦  MillionaireQuiz  ✦",
                 bg=BG_DARK, fg=GOLD, font=self.f_title).pack(pady=(40, 6))

        profile = self.data.get("active_profile")
        sub = f"Profile: {profile}" if profile else "No profile selected"
        tk.Label(f, text=sub, bg=BG_DARK, fg=SILVER, font=self.f_small).pack(pady=(0, 30))

        buttons = [
            (self.s("new_game"),   self.start_new_game),
            (self.s("load_game"),  self.load_game),
            (self.s("top_scores"), self.show_top_scores),
            (self.s("profile"),    self.show_profile),
            (self.s("achievements", **{}), self.show_achievements),
            (self.s("options"),    self.show_options),
            (self.s("discord"),    lambda: webbrowser.open(DISCORD_URL)),
            (self.s("quit"),       self.destroy),
        ]
        for text, cmd in buttons:
            self._menu_btn(f, text, cmd)

    def _menu_btn(self, parent, text, cmd, gold=False):
        fg  = GOLD if gold else MENU_BTN_FG
        btn = tk.Button(
            parent, text=text,
            bg=MENU_BTN_BG, fg=fg,
            font=self.f_menu_btn,
            relief="flat", cursor="hand2",
            width=22, pady=10,
            activebackground=BTN_HOVER, activeforeground=GOLD,
            command=cmd
        )
        btn.pack(pady=4)
        return btn

    # ════════════════════════════════════════════
    # OPTIONS
    # ════════════════════════════════════════════

    def show_options(self):
        self._clear()
        f = self._container
        opts = self.data["options"]

        tk.Label(f, text=self.s("options"), bg=BG_DARK, fg=GOLD,
                 font=self.f_title).pack(pady=(30, 20))

        # Language — with flag thumbnails
        tk.Label(f, text=self.s("lang_label"), bg=BG_DARK, fg=SILVER,
                 font=self.f_label).pack()
        lang_var = tk.StringVar(value=opts.get("language", "English"))
        lang_frame = tk.Frame(f, bg=BG_DARK)
        lang_frame.pack(pady=(4, 16))
        for lng in list_languages():
            row = tk.Frame(lang_frame, bg=BG_DARK)
            row.pack(side="left", padx=10)
            code = lng[:2].lower()
            flag_img = self.images.flag(code, size=(32, 20))
            if flag_img:
                lbl = tk.Label(row, image=flag_img, bg=BG_DARK)
                lbl.pack(side="left", padx=(0, 4))
                lbl._img_ref = flag_img
            tk.Radiobutton(
                row, text=lng, variable=lang_var, value=lng,
                bg=BG_DARK, fg=WHITE, selectcolor=BG_MID,
                activebackground=BG_DARK, activeforeground=GOLD,
                font=self.f_label
            ).pack(side="left")

        # Volume slider
        tk.Label(f, text=self.s("vol_label", **{}) if "vol_label" in self._lang.get("ui",{})
                 else "🔊  Volume",
                 bg=BG_DARK, fg=SILVER, font=self.f_label).pack(pady=(8, 0))
        vol_var = tk.DoubleVar(value=opts.get("volume", 0.7))
        vol_frame = tk.Frame(f, bg=BG_DARK)
        vol_frame.pack(pady=(4, 16))
        tk.Scale(
            vol_frame, from_=0.0, to=1.0, resolution=0.05,
            orient="horizontal", variable=vol_var,
            bg=BG_DARK, fg=GOLD, troughcolor=BG_MID,
            highlightthickness=0, length=200,
            command=lambda v: self.sound.__setattr__("volume", float(v))
        ).pack()

        # Resolution
        tk.Label(f, text=self.s("res_label"), bg=BG_DARK, fg=SILVER,
                 font=self.f_label).pack()
        res_var = tk.StringVar(value=opts.get("resolution", "900 × 720"))
        fs_var  = tk.BooleanVar(value=opts.get("fullscreen", False))
        res_frame = tk.Frame(f, bg=BG_DARK)
        res_frame.pack(pady=(4, 4))
        for name, *_ in RESOLUTIONS:
            tk.Radiobutton(
                res_frame, text=name, variable=res_var, value=name,
                bg=BG_DARK, fg=WHITE, selectcolor=BG_MID,
                activebackground=BG_DARK, activeforeground=GOLD,
                font=self.f_small
            ).pack(anchor="w", padx=40)
        tk.Checkbutton(
            f, text="Fullscreen", variable=fs_var,
            bg=BG_DARK, fg=WHITE, selectcolor=BG_MID,
            activebackground=BG_DARK, activeforeground=GOLD,
            font=self.f_small
        ).pack(pady=(4, 16))

        def apply():
            self.data["options"]["language"]   = lang_var.get()
            self.data["options"]["resolution"] = res_var.get()
            self.data["options"]["fullscreen"] = fs_var.get()
            self.data["options"]["volume"]     = vol_var.get()
            self.sound.volume = vol_var.get()
            save_data(self.data)
            self._load_lang()
            self._setup_fonts()
            self._apply_resolution()
            self.show_menu()

        tk.Button(f, text=self.s("apply"),
                  bg=GOLD, fg=BG_DARK, font=self.f_lifeline,
                  relief="flat", cursor="hand2", padx=20, pady=8,
                  command=apply).pack(pady=6)
        tk.Button(f, text=self.s("back_menu"),
                  bg=MENU_BTN_BG, fg=SILVER, font=self.f_small,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self.show_menu).pack(pady=4)

    # ════════════════════════════════════════════
    # PROFILE
    # ════════════════════════════════════════════

    def show_profile(self):
        self._clear()
        f = self._container
        profiles = self.data["profiles"]
        active   = self.data.get("active_profile")

        tk.Label(f, text=self.s("profile_title"), bg=BG_DARK, fg=GOLD,
                 font=self.f_title).pack(pady=(30, 6))

        # Profile list
        list_frame = tk.Frame(f, bg=BG_DARK)
        list_frame.pack(pady=8)
        if profiles:
            for name in sorted(profiles.keys()):
                marker = "▶ " if name == active else "   "
                color  = GOLD if name == active else WHITE
                tk.Button(
                    list_frame,
                    text=f"{marker}{name}",
                    bg=BTN_DEFAULT, fg=color,
                    font=self.f_label,
                    relief="flat", cursor="hand2",
                    width=22, pady=6,
                    command=lambda n=name: self._select_profile(n)
                ).pack(pady=2)
        else:
            tk.Label(list_frame, text="—", bg=BG_DARK, fg=SILVER,
                     font=self.f_label).pack()

        # Stats of active profile
        if active and active in profiles:
            p = profiles[active]
            stats_frame = tk.Frame(f, bg=BG_PANEL)
            stats_frame.pack(pady=12, padx=40, fill="x")
            rows = [
                (self.s("stats_games"),   p.get("games_played", 0)),
                (self.s("stats_subs"),    p.get("total_subs", 0)),
                (self.s("stats_best"),    p.get("best_game", 0)),
                (self.s("stats_correct"), p.get("correct_answers", 0)),
            ]
            for label, val in rows:
                row = tk.Frame(stats_frame, bg=BG_PANEL)
                row.pack(fill="x", padx=12, pady=3)
                tk.Label(row, text=label, bg=BG_PANEL, fg=SILVER,
                         font=self.f_small, anchor="w").pack(side="left")
                tk.Label(row, text=str(val), bg=BG_PANEL, fg=GOLD,
                         font=self.f_prize_hl, anchor="e").pack(side="right")

        # Buttons
        btn_frame = tk.Frame(f, bg=BG_DARK)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text=self.s("new_profile"),
                  bg=LIFELINE_ON, fg=GOLD, font=self.f_small,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=self._new_profile).pack(side="left", padx=6)
        if active:
            tk.Button(btn_frame, text=self.s("delete_profile"),
                      bg=BTN_WRONG, fg=WHITE, font=self.f_small,
                      relief="flat", cursor="hand2", padx=10, pady=6,
                      command=lambda: self._delete_profile(active)).pack(side="left", padx=6)

        tk.Button(f, text=self.s("back_menu"),
                  bg=MENU_BTN_BG, fg=SILVER, font=self.f_small,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self.show_menu).pack(pady=8)

    def _select_profile(self, name: str):
        self.data["active_profile"] = name
        save_data(self.data)
        self.show_profile()

    def _new_profile(self):
        name = simpledialog.askstring(
            self.s("profile_title"), self.s("enter_name"), parent=self
        )
        if name is None:
            return
        name = name.strip()
        if not name:
            messagebox.showerror("", self.s("name_empty"), parent=self)
            return
        if name in self.data["profiles"]:
            messagebox.showerror("", self.s("name_taken"), parent=self)
            return
        self.data["profiles"][name] = {
            "games_played": 0, "total_subs": 0,
            "best_game": 0, "correct_answers": 0,
            "scores": []
        }
        self.data["active_profile"] = name
        save_data(self.data)
        self.show_profile()

    def _delete_profile(self, name: str):
        if not messagebox.askyesno(
            "", self.s("confirm_delete", name=name), parent=self
        ):
            return
        del self.data["profiles"][name]
        if self.data["active_profile"] == name:
            remaining = list(self.data["profiles"].keys())
            self.data["active_profile"] = remaining[0] if remaining else None
        save_data(self.data)
        self.show_profile()

    # ════════════════════════════════════════════
    # ACHIEVEMENTS
    # ════════════════════════════════════════════

    def show_achievements(self):
        self._clear()
        f = self._container
        lang = self._lang.get("code", "en")
        profile = self.data.get("active_profile")
        unlocked = set()
        if profile and profile in self.data["profiles"]:
            unlocked = set(self.data["profiles"][profile].get("achievements", []))

        tk.Label(f, text=self.s("achievements"), bg=BG_DARK, fg=GOLD,
                 font=self.f_title).pack(pady=(24, 12))

        frame = tk.Frame(f, bg=BG_DARK)
        frame.pack(fill="both", expand=True, padx=30)

        if not self.ach_defs:
            tk.Label(frame, text=self.s("no_achievements"), bg=BG_DARK,
                     fg=SILVER, font=self.f_label).pack(pady=20)
        else:
            for ach in self.ach_defs:
                is_unlocked = ach["id"] in unlocked
                is_secret   = ach.get("secret", False) and not is_unlocked
                icon  = ach.get("icon", "🎖") if is_unlocked else ("❓" if is_secret else "🔒")
                name  = ach["name"].get(lang, ach["name"].get("en", ach["id"])) if is_unlocked or not is_secret else "???"
                desc  = ach["description"].get(lang, ach["description"].get("en", "")) if is_unlocked or not is_secret else "???"
                row_bg = BG_MID if is_unlocked else BG_PANEL
                fg_col = GOLD if is_unlocked else SILVER

                row = tk.Frame(frame, bg=row_bg)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f" {icon} ", bg=row_bg, fg=fg_col,
                         font=self.f_label).pack(side="left", padx=4)
                info = tk.Frame(row, bg=row_bg)
                info.pack(side="left", fill="x", expand=True, padx=4, pady=4)
                tk.Label(info, text=name, bg=row_bg, fg=fg_col,
                         font=self.f_prize_hl, anchor="w").pack(fill="x")
                tk.Label(info, text=desc, bg=row_bg, fg=SILVER,
                         font=self.f_small, anchor="w", wraplength=500).pack(fill="x")

        tk.Button(f, text=self.s("back_menu"),
                  bg=MENU_BTN_BG, fg=SILVER, font=self.f_small,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self.show_menu).pack(pady=12)

    def _check_achievements(self, subs_won: int, level_reached: int,
                             won: bool, walked: bool, lifelines_used: dict,
                             win_streak: int):
        """Evaluate all achievement triggers and unlock new ones. Returns list of newly unlocked."""
        profile = self.data.get("active_profile")
        if not profile or profile not in self.data["profiles"]:
            return []
        p = self.data["profiles"][profile]
        already = set(p.get("achievements", []))
        newly   = []

        def unlock(ach_id):
            if ach_id not in already:
                already.add(ach_id)
                newly.append(ach_id)

        games   = p.get("games_played", 0)
        total   = p.get("total_subs", 0)

        for ach in self.ach_defs:
            aid = ach["id"]
            if aid in already:
                continue
            t = ach.get("trigger", {})
            tt, tv = t.get("type"), t.get("value")
            if tt == "games_played"      and games  >= tv:              unlock(aid)
            elif tt == "level_reached"   and level_reached >= tv:       unlock(aid)
            elif tt == "win"             and tv and won:                 unlock(aid)
            elif tt == "win_no_lifeline" and tv and won and not any(lifelines_used.values()): unlock(aid)
            elif tt == "win_no_fifty"    and tv and won and not lifelines_used.get("fifty"):  unlock(aid)
            elif tt == "walk_away_with_safe" and tv and walked and self.game_state and self.game_state.safe_prize > 0: unlock(aid)
            elif tt == "total_subs"      and total  >= tv:              unlock(aid)
            elif tt == "fail_at_level"   and not won and not walked and level_reached == tv: unlock(aid)
            elif tt == "win_streak"      and win_streak >= tv:          unlock(aid)

        p["achievements"] = list(already)
        save_data(self.data)
        return newly

    def _show_achievement_popups(self, newly_unlocked: list[str]):
        """Show a small toast-style popup for each new achievement."""
        self.sound.play_jingle("achievement")
        lang = self._lang.get("code", "en")
        for ach_id in newly_unlocked:
            ach = next((a for a in self.ach_defs if a["id"] == ach_id), None)
            if not ach:
                continue
            name   = ach["name"].get(lang, ach["name"].get("en", ach_id))
            msg    = self.s("ach_unlocked", name=f"{ach.get('icon','🎖')} {name}")
            ov = tk.Toplevel(self)
            ov.configure(bg=GOLD)
            ov.resizable(False, False)
            ov.overrideredirect(True)
            tk.Label(ov, text=msg, bg=GOLD, fg=BG_DARK,
                     font=self.f_lifeline, padx=20, pady=10).pack()
            ov.update_idletasks()
            x = self.winfo_x() + self.winfo_width()  - ov.winfo_width()  - 20
            y = self.winfo_y() + self.winfo_height() - ov.winfo_height() - 20
            ov.geometry(f"+{x}+{y}")
            ov.after(2800, ov.destroy)

    # ════════════════════════════════════════════
    # TOP SCORES
    # ════════════════════════════════════════════

    def show_top_scores(self):
        self._clear()
        f = self._container

        tk.Label(f, text=self.s("top_scores"), bg=BG_DARK, fg=GOLD,
                 font=self.f_title).pack(pady=(30, 16))

        profiles = self.data["profiles"]
        # Gather all scores across all profiles, keep top 10
        all_scores = []
        for pname, pdata in profiles.items():
            for sc in pdata.get("scores", []):
                all_scores.append((pname, sc["subs"], sc["level"], sc.get("won", False)))
        all_scores.sort(key=lambda x: x[1], reverse=True)
        top = all_scores[:10]

        if not top:
            tk.Label(f, text=self.s("no_scores"), bg=BG_DARK, fg=SILVER,
                     font=self.f_label).pack(pady=20)
        else:
            tbl = tk.Frame(f, bg=BG_PANEL)
            tbl.pack(padx=40, pady=4, fill="x")
            headers = ["#", "Profile", "Subs", "Level", ""]
            widths  = [3, 14, 8, 6, 4]
            for col, (h, w) in enumerate(zip(headers, widths)):
                tk.Label(tbl, text=h, bg=BG_PANEL, fg=GOLD,
                         font=self.f_prize_hl, width=w, anchor="w"
                         ).grid(row=0, column=col, padx=4, pady=4, sticky="w")
            for i, (pname, subs, level, won) in enumerate(top):
                row_bg = BG_MID if i % 2 == 0 else BG_PANEL
                for col, (val, w) in enumerate(zip(
                    [i + 1, pname, subs, level, "🏆" if won else ""],
                    widths
                )):
                    tk.Label(tbl, text=str(val), bg=row_bg, fg=WHITE,
                             font=self.f_small, width=w, anchor="w"
                             ).grid(row=i + 1, column=col, padx=4, pady=2, sticky="w")

        tk.Button(f, text=self.s("back_menu"),
                  bg=MENU_BTN_BG, fg=SILVER, font=self.f_small,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self.show_menu).pack(pady=20)

    # ════════════════════════════════════════════
    # GAME — start / load
    # ════════════════════════════════════════════

    def start_new_game(self):
        self.game_state = GameState(self.all_questions)
        self._show_game()

    def load_game(self):
        sv = self.data.get("save")
        if not sv:
            messagebox.showinfo("", self.s("no_save"), parent=self)
            return
        self.game_state = GameState.from_dict(self.all_questions, sv)
        self._show_game()

    # ════════════════════════════════════════════
    # GAME SCREEN
    # ════════════════════════════════════════════

    def _show_game(self):
        self._clear()
        s = self.game_state

        # Music for this level
        self.sound.play_music(SoundEngine.music_key_for_level(s.current_level))

        f = self._container

        # Background image
        bg_key = ImageLoader.bg_key_for_level(s.current_level)
        bg_img = self.images.background(bg_key,
                                        size=(self.winfo_width() or 900,
                                              self.winfo_height() or 720))
        if bg_img:
            lbl = tk.Label(f, image=bg_img, bg=BG_DARK)
            lbl.place(x=0, y=0, relwidth=1, relheight=1)
            lbl._img_ref = bg_img

        # ── Title bar ──
        top = tk.Frame(f, bg=BG_DARK)
        top.pack(fill="x", padx=16, pady=(10, 0))
        tk.Label(top, text="✦  MillionaireQuiz  ✦",
                 bg=BG_DARK, fg=GOLD, font=self.f_question).pack(side="left", expand=True)

        # ── Main area ──
        main = tk.Frame(f, bg=BG_DARK)
        main.pack(fill="both", expand=True, padx=16, pady=6)

        # LEFT
        left = tk.Frame(main, bg=BG_DARK)
        left.pack(side="left", fill="both", expand=True)

        # Question box
        q_outer = tk.Frame(left, bg=GOLD)
        q_outer.pack(fill="x", pady=(0, 8))
        q_inner = tk.Frame(q_outer, bg=BG_MID)
        q_inner.pack(fill="x", padx=2, pady=2)
        self._lbl_level = tk.Label(q_inner, text="", bg=BG_MID, fg=GOLD,
                                   font=self.f_small, anchor="e")
        self._lbl_level.pack(fill="x", padx=14, pady=(6, 0))
        self._lbl_question = tk.Label(q_inner, text="", wraplength=520,
                                      bg=BG_MID, fg=WHITE, font=self.f_question,
                                      justify="center")
        self._lbl_question.pack(fill="x", padx=16, pady=(4, 12))

        # Answers
        self._ans_btns: dict[str, tk.Button] = {}
        grid = tk.Frame(left, bg=BG_DARK)
        grid.pack(fill="x", pady=(0, 8))
        for idx, (label, row, col) in enumerate(
            [("A", 0, 0), ("B", 0, 1), ("C", 1, 0), ("D", 1, 1)]
        ):
            fr = tk.Frame(grid, bg=GOLD)
            fr.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            btn = tk.Button(
                fr, text=f"  {label}:  ",
                bg=BTN_DEFAULT, fg=WHITE, font=self.f_answer,
                relief="flat", bd=0,
                activebackground=BTN_HOVER, activeforeground=WHITE,
                cursor="hand2", anchor="w", wraplength=210,
                justify="left", padx=10, pady=10,
                command=lambda l=label: self._on_answer(l)
            )
            btn.pack(fill="both", expand=True, padx=2, pady=2)
            self._ans_btns[label] = btn
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # Lifelines
        ll_frame = tk.Frame(left, bg=BG_DARK)
        ll_frame.pack(fill="x", pady=(0, 6))
        self._btn_fifty  = self._lifeline_btn(ll_frame, self.s("fifty"),  self._use_fifty)
        self._btn_vote   = self._lifeline_btn(ll_frame, self.s("vote"),   self._use_vote)
        self._btn_switch = self._lifeline_btn(ll_frame, self.s("switch"), self._use_switch)
        for b in (self._btn_fifty, self._btn_vote, self._btn_switch):
            b.pack(side="left", padx=3, expand=True, fill="x")

        # Vote result
        self._lbl_vote = tk.Label(left, text="", bg=BG_DARK, fg=GOLD, font=self.f_small)
        self._lbl_vote.pack(pady=(0, 3))

        # Bottom buttons
        bot = tk.Frame(left, bg=BG_DARK)
        bot.pack(fill="x", pady=(2, 0))
        tk.Button(bot, text=self.s("walk_away"),
                  bg=BG_PANEL, fg=SILVER, font=self.f_small,
                  relief="flat", cursor="hand2", padx=8, pady=5,
                  command=self._walk_away).pack(side="left", padx=3)
        tk.Button(bot, text=self.s("save_btn"),
                  bg=BG_PANEL, fg=SILVER, font=self.f_small,
                  relief="flat", cursor="hand2", padx=8, pady=5,
                  command=self._save_game).pack(side="left", padx=3)
        tk.Button(bot, text=self.s("menu_btn"),
                  bg=BG_PANEL, fg=SILVER, font=self.f_small,
                  relief="flat", cursor="hand2", padx=8, pady=5,
                  command=self.show_menu).pack(side="left", padx=3)
        tk.Button(bot, text=self.s("new_game_btn"),
                  bg=BG_PANEL, fg=GOLD, font=self.f_small,
                  relief="flat", cursor="hand2", padx=8, pady=5,
                  command=self.start_new_game).pack(side="right", padx=3)

        # RIGHT — ladder
        right = tk.Frame(main, bg=BG_PANEL, width=150)
        right.pack(side="right", fill="y", padx=(12, 0))
        right.pack_propagate(False)
        tk.Label(right, text=self.s("prize_ladder"),
                 bg=BG_PANEL, fg=GOLD, font=self.f_small).pack(pady=(8, 4))
        self._ladder_lbls: list[tk.Label] = []
        for i in range(14, -1, -1):
            is_safe = (i + 1) in SAFE_HAVENS
            icon    = "🔒 " if is_safe else "   "
            lbl = tk.Label(right,
                           text=f"{icon}{i+1:>2}.  {PRIZE_LADDER[i]}",
                           bg=BG_PANEL,
                           fg=GOLD_DARK if is_safe else SILVER,
                           font=self.f_prize, anchor="w", padx=6)
            lbl.pack(fill="x", pady=1)
            self._ladder_lbls.insert(0, lbl)

        self._game_refresh()

    def _lifeline_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text,
                         bg=LIFELINE_ON, fg=LIFELINE_TEXT_ON,
                         font=self.f_lifeline, relief="flat",
                         cursor="hand2", padx=6, pady=7,
                         command=cmd)

    # ── Game refresh ──

    def _game_refresh(self):
        s = self.game_state
        d = s.displayed
        self._lbl_level.config(
            text=self.s("question_lbl", lvl=s.current_level, prize=s.prize_label))
        self._lbl_question.config(text=s.current_q["question"])

        for label in ANSWER_LABELS:
            btn = self._ans_btns[label]
            if label in s.eliminated:
                btn.config(text=f"  {label}:  —",
                           bg=BTN_DISABLED, fg=TEXT_DISABLED,
                           state="disabled", cursor="arrow")
            else:
                btn.config(text=f"  {label}:  {d['answers'][label]}",
                           bg=BTN_DEFAULT, fg=WHITE,
                           state="normal", cursor="hand2")

        for btn, key in [(self._btn_fifty, "fifty"),
                         (self._btn_vote,  "vote"),
                         (self._btn_switch,"switch")]:
            if s.lifelines[key]:
                btn.config(bg=LIFELINE_ON, fg=LIFELINE_TEXT_ON,
                           state="normal", cursor="hand2")
            else:
                btn.config(bg=LIFELINE_OFF, fg=LIFELINE_TEXT_OFF,
                           state="disabled", cursor="arrow")

        self._lbl_vote.config(text="")

        for i, lbl in enumerate(self._ladder_lbls):
            level   = i + 1
            is_safe = level in SAFE_HAVENS
            if level == s.current_level:
                lbl.config(bg=GOLD, fg=BG_DARK, font=self.f_prize_hl)
            elif level < s.current_level:
                lbl.config(bg=BG_PANEL, fg=BTN_CORRECT, font=self.f_prize)
            else:
                lbl.config(bg=BG_PANEL,
                           fg=GOLD_DARK if is_safe else SILVER,
                           font=self.f_prize)

    # ── Answer flow ──

    def _on_answer(self, label: str):
        self._set_ans_state("disabled")
        self._disable_lifelines()
        self.sound.play_jingle("answer_selected")
        self._ans_btns[label].config(bg=BTN_SELECTED)
        self.update()
        self.after(ANIMATION_MS, lambda: self._reveal(label))

    def _reveal(self, chosen: str):
        correct = self.game_state.displayed["correct"]
        if chosen == correct:
            self._ans_btns[chosen].config(bg=BTN_CORRECT)
            self.sound.play_jingle("correct")
        else:
            self._ans_btns[chosen].config(bg=BTN_WRONG)
            self._ans_btns[correct].config(bg=BTN_CORRECT)
            self.sound.play_jingle("wrong")
        self.update()
        self.after(1000, lambda: self._advance(chosen))

    def _advance(self, chosen: str):
        prev_level = self.game_state.current_level
        ok = self.game_state.answer(chosen)
        if self.game_state.game_over:
            if self.game_state.won:
                self.sound.play_jingle("win")
            self._record_score(ok)
            self._show_end(ok)
        else:
            # Safe haven jingle when leaving level 5 or 10
            if prev_level in SAFE_HAVENS:
                self.sound.play_jingle("safe_haven")
            # Update music if level range changed
            self.sound.play_music(SoundEngine.music_key_for_level(self.game_state.current_level))
            self._game_refresh()

    # ── Lifeline actions ──

    def _use_fifty(self):
        self.game_state.fifty_fifty()
        self._game_refresh()

    def _use_vote(self):
        results = self.game_state.chat_vote()
        parts   = "  ".join(f"{k}: {results[k]}%" for k in ANSWER_LABELS)
        self._lbl_vote.config(text=self.s("vote_result", parts=parts))
        for btn, key in [(self._btn_fifty, "fifty"),
                         (self._btn_vote,  "vote"),
                         (self._btn_switch,"switch")]:
            if self.game_state.lifelines[key]:
                btn.config(bg=LIFELINE_ON, fg=LIFELINE_TEXT_ON,
                           state="normal", cursor="hand2")
            else:
                btn.config(bg=LIFELINE_OFF, fg=LIFELINE_TEXT_OFF,
                           state="disabled", cursor="arrow")

    def _use_switch(self):
        self.game_state.switch()
        self._lbl_vote.config(text="")
        self._game_refresh()

    # ── Walk away ──

    def _walk_away(self):
        if self.game_state.game_over:
            return
        self.game_state.walk_away()
        subs_won = self.game_state.prize_value
        self._record_score_raw(subs_won, self.game_state.current_level, won=False, walked=True)
        self._show_walk_away_overlay(self.game_state.prize_label)

    def _show_walk_away_overlay(self, prize: str):
        ov = self._make_overlay()
        tk.Label(ov, text=self.s("walk_away_title"),
                 bg=BG_DARK, fg=GOLD, font=self.f_big, padx=40, pady=20).pack()
        tk.Label(ov, text=self.s("walk_away_sub", prize=prize),
                 bg=BG_DARK, fg=WHITE, font=self.f_question, padx=40, pady=4).pack()
        self._overlay_buttons(ov)
        self._center_overlay(ov)

    # ── Save / Load ──

    def _save_game(self):
        profile = self.data.get("active_profile")
        sv = self.game_state.to_dict()
        sv["profile"] = profile
        self.data["save"] = sv
        save_data(self.data)
        messagebox.showinfo("", self.s("save_ok"), parent=self)

    # ── End screen ──

    def _record_score(self, was_correct: bool):
        s = self.game_state
        if s.won:
            subs = s.prize_value          # 100
            level = 15
        elif not was_correct:
            subs  = s.safe_value
            level = s.current_level
        else:
            subs  = s.prize_value
            level = s.current_level
        self._record_score_raw(subs, level, s.won)

    def _record_score_raw(self, subs: int, level: int, won: bool, walked: bool = False):
        profile = self.data.get("active_profile")
        if not profile or profile not in self.data["profiles"]:
            return
        p = self.data["profiles"][profile]
        p["games_played"]    = p.get("games_played", 0) + 1
        p["total_subs"]      = p.get("total_subs", 0) + subs
        p["best_game"]       = max(p.get("best_game", 0), subs)
        p["correct_answers"] = p.get("correct_answers", 0) + self.game_state.correct_this_game

        # Win streak tracking
        streak = p.get("win_streak", 0)
        if won:
            streak += 1
        else:
            streak = 0
        p["win_streak"] = streak

        entry = {"subs": subs, "level": level, "won": won}
        scores = p.get("scores", [])
        scores.append(entry)
        scores.sort(key=lambda x: x["subs"], reverse=True)
        p["scores"] = scores[:20]
        self.data["save"] = None
        save_data(self.data)

        # Lifelines used = those that are now False (started as True)
        lifelines_used = {k: not v for k, v in self.game_state.lifelines.items()}

        newly = self._check_achievements(
            subs_won=subs,
            level_reached=level,
            won=won,
            walked=walked,
            lifelines_used=lifelines_used,
            win_streak=streak,
        )
        if newly:
            self.after(1200, lambda: self._show_achievement_popups(newly))

    def _show_end(self, was_correct: bool):
        s = self.game_state
        ov = self._make_overlay()
        if s.won:
            headline = self.s("win_title")
            sub      = self.s("win_sub", prize=PRIZE_LADDER[14])
            color    = GOLD
        elif was_correct:
            headline = self.s("win_title")
            sub      = ""
            color    = BTN_CORRECT
        else:
            headline = self.s("wrong_title")
            sub      = self.s("wrong_sub", prize=s.safe_label)
            color    = "#e05050"

        tk.Label(ov, text=headline, bg=BG_DARK, fg=color,
                 font=self.f_big, padx=40, pady=20).pack()
        if sub:
            tk.Label(ov, text=sub, bg=BG_DARK, fg=WHITE,
                     font=self.f_question, padx=40, pady=4).pack()
        self._overlay_buttons(ov)
        self._center_overlay(ov)

    # ── Overlay helpers ──

    def _make_overlay(self) -> tk.Toplevel:
        ov = tk.Toplevel(self)
        ov.title("")
        ov.configure(bg=BG_DARK)
        ov.resizable(False, False)
        ov.grab_set()
        return ov

    def _overlay_buttons(self, ov: tk.Toplevel):
        fr = tk.Frame(ov, bg=BG_DARK)
        fr.pack(pady=16)
        tk.Button(fr, text=self.s("play_again"),
                  bg=GOLD, fg=BG_DARK, font=self.f_lifeline,
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  command=lambda: [ov.destroy(), self.start_new_game()]
                  ).pack(side="left", padx=8)
        tk.Button(fr, text=self.s("back_menu"),
                  bg=MENU_BTN_BG, fg=SILVER, font=self.f_small,
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  command=lambda: [ov.destroy(), self.show_menu()]
                  ).pack(side="left", padx=8)

    def _center_overlay(self, ov: tk.Toplevel):
        ov.update_idletasks()
        mw, mh = self.winfo_width(), self.winfo_height()
        mx, my = self.winfo_x(),     self.winfo_y()
        ow, oh = ov.winfo_width(),   ov.winfo_height()
        ov.geometry(f"+{mx + (mw - ow)//2}+{my + (mh - oh)//2}")

    # ── Helpers ──

    def _set_ans_state(self, state: str):
        for btn in self._ans_btns.values():
            btn.config(state=state)

    def _disable_lifelines(self):
        for btn in (self._btn_fifty, self._btn_vote, self._btn_switch):
            btn.config(state="disabled")


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()
