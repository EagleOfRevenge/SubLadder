"""
main.py — Sub Ladder v2.4
Main application class. Thin orchestrator that delegates all screen
rendering to the screens/ package and all game logic to singleplayer/.

To run: python run.py  (from project root)
"""

import os
import sys
import tkinter as tk
from tkinter import font as tkfont, messagebox

from .constants import RESOLUTIONS, GAME_VERSION, apply_theme
from .constants import GOLD, BG_DARK, SILVER, WHITE
from .utils import (
    load_data, save_data, load_language, list_languages,
    load_achievements, validate_assets,
)
from .game_state import GameState, load_questions
from .asset_manager import SoundEngine, ImageLoader, ensure_assets
from .auth import APIClient, TokenManager

# ── Path helpers ──────────────────────────────────────────────────
# Nuitka (and PyInstaller) set sys.frozen to True when running a
# compiled / frozen executable.  In that case __file__ points inside
# the temporary extraction directory (or the exe location) and we
# must derive all paths from sys.executable / sys._MEIPASS instead.
if getattr(sys, "frozen", False):
    _frozen_base = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
    ROOT_DIR = _frozen_base
    GAME_DIR = os.path.join(_frozen_base, "game")
    DATA_DIR = os.path.join(_frozen_base, "data")
else:
    GAME_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(GAME_DIR)
    DATA_DIR = os.path.join(ROOT_DIR, "data")


class App(tk.Tk):
    """
    Thin UI shell. Each method delegates to a screen module.
    No widget creation happens here — just navigation + shared state.
    """

    def __init__(self, first_run_result: tuple = None):
        super().__init__()

        # ── Asset generation (placeholders if missing) ────────────
        ensure_assets()

        # ── Engines ───────────────────────────────────────────────
        self.sound  = SoundEngine()
        self.images = ImageLoader()
        
        # ── Data ──────────────────────────────────────────────────
        self.data = load_data()
        
        # ── API Client for online profiles ────────────────────────
        self.api = APIClient(
            host=self.data.get("server", {}).get("host", "45.156.84.114"),
            port=self.data.get("server", {}).get("port", 8000),
        )
        self.token_mgr = TokenManager(self.data)

        # First-run result from run.py wizard
        if first_run_result is not None:
            # first_run_result is now a dict with: lang, profile, profile_type, 
            # and optionally: online_email, online_token, online_user_id, online_user_name
            lang = first_run_result.get("lang")
            profile_name = first_run_result.get("profile")
            profile_type = first_run_result.get("profile_type", "offline")
            
            self.data["options"]["language"] = lang
            if profile_name:
                profile_data = {
                    "games_played": 0, "total_subs": 0,
                    "best_game": 0, "correct_answers": 0,
                    "achievements": [], "scores": [],
                    "win_streak": 0, "total_xp": 0, "player_level": 1,
                    "legendary_unlocked": False,
                    "avatar": None,
                    "profile_type": profile_type,  # "offline" or "online"
                }
                
                # For online profiles, store server info
                if profile_type == "online":
                    provider = first_run_result.get("online_provider")
                    provider_account = first_run_result.get("online_provider_id")

                    profile_data["user_id"] = first_run_result.get("online_user_id")
                    profile_data["server_username"] = first_run_result.get("online_user_name")

                    if provider:
                        profile_data["provider"] = provider
                        profile_data["provider_account"] = provider_account
                        profile_data["linked_accounts"] = [provider]
                        if provider == "discord":
                            profile_data["linked_discord"] = True
                            profile_data["discord_id"] = provider_account
                        elif provider == "steam":
                            profile_data["linked_steam"] = True
                            profile_data["steam_id"] = provider_account
                    
                    # Store token
                    token = first_run_result.get("online_token")
                    if token:
                        self.token_mgr.store_token(profile_name, token)
                
                self.data["profiles"][profile_name] = profile_data
                self.data["active_profile"] = profile_name
            save_data(self.data)   # loud on first run

        # ── Language + questions ──────────────────────────────────
        self.ach_defs = load_achievements()
        self._load_lang()

        # ── Startup validation ────────────────────────────────────
        missing = validate_assets(self._lang)
        if missing:
            msg = ("The following required files are missing:\n\n"
                   + "\n".join(f"  • {m}" for m in missing)
                   + "\n\nPlease reinstall Sub Ladder or check your installation.")
            messagebox.showerror("Sub Ladder — Missing files", msg, parent=self)
            self.destroy()
            return

        # ── Volume from saved options ─────────────────────────────
        self.sound.volume       = self.data["options"].get("sfx_volume",   0.7)
        self.sound.music_volume = self.data["options"].get("music_volume", 0.7)

        # ── Fonts + window ────────────────────────────────────────
        self._setup_fonts()
        self._apply_theme_colors()
        self.title(self.s("title"))
        self.configure(bg=self.BG_DARK)

        self._container = tk.Frame(self, bg=self.BG_DARK)
        self._container.pack(fill="both", expand=True)

        # Shared game state (set by start_new_game / load_game)
        self.game_state: GameState | None = None

        # Track current screen for theme reload
        self._current_screen: str = "menu"

        # Timer state (managed by screens/game_screen.py)
        self._timer_after = None
        self._timer_secs  = 0

        self._apply_resolution()
        self.show_pre_menu()

    # ══════════════════════════════════════════════════════════════
    # LANGUAGE
    # ══════════════════════════════════════════════════════════════

    def _load_lang(self):
        lang_name       = self.data["options"].get("language", "English")
        self._lang      = load_language(lang_name)
        qfile           = self._lang.get("questions_file", "en_questions.json")
        self.all_questions = load_questions(qfile)

    def s(self, key: str, **kw) -> str:
        """Translate a UI string key using the active language."""
        ui   = self._lang.get("ui", {})
        tmpl = ui.get(key, key)
        return tmpl.format(**kw) if kw else tmpl

    # ══════════════════════════════════════════════════════════════
    # THEME COLORS
    # ══════════════════════════════════════════════════════════════

    def _apply_theme_colors(self):
        """Apply the currently selected color theme to instance attributes."""
        from constants import (
            BG_DARK as _BG_DARK, BG_MID as _BG_MID, BG_PANEL as _BG_PANEL,
            GOLD as _GOLD, GOLD_DARK as _GOLD_DARK, SILVER as _SILVER,
            WHITE as _WHITE, TEXT_DISABLED as _TEXT_DISABLED,
            BTN_DEFAULT as _BTN_DEFAULT, BTN_HOVER as _BTN_HOVER,
            BTN_SELECTED as _BTN_SELECTED, BTN_CORRECT as _BTN_CORRECT,
            BTN_WRONG as _BTN_WRONG, BTN_DISABLED as _BTN_DISABLED,
            MENU_BTN_BG as _MENU_BTN_BG, MENU_BTN_FG as _MENU_BTN_FG,
            MENU_BTN_ACT as _MENU_BTN_ACT,
            LIFELINE_ON as _LIFELINE_ON, LIFELINE_OFF as _LIFELINE_OFF,
            LIFELINE_TEXT_ON as _LIFELINE_TEXT_ON, LIFELINE_TEXT_OFF as _LIFELINE_TEXT_OFF,
        )
        overrides = apply_theme(self.data["options"].get("theme", "Dark Navy"))
        self.BG_DARK       = overrides.get("BG_DARK", _BG_DARK)
        self.BG_MID        = overrides.get("BG_MID", _BG_MID)
        self.BG_PANEL      = overrides.get("BG_PANEL", _BG_PANEL)
        self.GOLD          = overrides.get("GOLD", _GOLD)
        self.GOLD_DARK     = overrides.get("GOLD_DARK", _GOLD_DARK)
        self.SILVER        = overrides.get("SILVER", _SILVER)
        self.WHITE         = overrides.get("WHITE", _WHITE)
        self.TEXT_DISABLED = overrides.get("TEXT_DISABLED", _TEXT_DISABLED)
        self.BTN_DEFAULT   = overrides.get("BTN_DEFAULT", _BTN_DEFAULT)
        self.BTN_HOVER     = overrides.get("BTN_HOVER", _BTN_HOVER)
        self.BTN_SELECTED  = overrides.get("BTN_SELECTED", _BTN_SELECTED)
        self.BTN_CORRECT   = overrides.get("BTN_CORRECT", _BTN_CORRECT)
        self.BTN_WRONG     = overrides.get("BTN_WRONG", _BTN_WRONG)
        self.BTN_DISABLED  = overrides.get("BTN_DISABLED", _BTN_DISABLED)
        self.MENU_BTN_BG   = overrides.get("MENU_BTN_BG", _MENU_BTN_BG)
        self.MENU_BTN_FG   = overrides.get("MENU_BTN_FG", _MENU_BTN_FG)
        self.MENU_BTN_ACT  = overrides.get("MENU_BTN_ACT", _MENU_BTN_ACT)
        self.LIFELINE_ON   = overrides.get("LIFELINE_ON", _LIFELINE_ON)
        self.LIFELINE_OFF  = overrides.get("LIFELINE_OFF", _LIFELINE_OFF)
        self.LIFELINE_TEXT_ON   = overrides.get("LIFELINE_TEXT_ON", _LIFELINE_TEXT_ON)
        self.LIFELINE_TEXT_OFF  = overrides.get("LIFELINE_TEXT_OFF", _LIFELINE_TEXT_OFF)

    # ══════════════════════════════════════════════════════════════
    # FONTS
    # ══════════════════════════════════════════════════════════════

    def _setup_fonts(self):
        fam  = next((f for f in tkfont.families()
                     if f in ["Georgia", "Palatino"]), "TkDefaultFont")
        body = next((f for f in tkfont.families()
                     if f in ["Helvetica", "Arial"]), "TkDefaultFont")
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

    # ══════════════════════════════════════════════════════════════
    # RESOLUTION
    # ══════════════════════════════════════════════════════════════

    def _apply_resolution(self):
        opts     = self.data["options"]
        res_name = opts.get("resolution", "900 × 720")
        fs       = opts.get("fullscreen", False)

        if fs:
            self.attributes("-fullscreen", True)
            self.resizable(True, True)
            return

        self.attributes("-fullscreen", False)
        match = next((r for r in RESOLUTIONS if r[0] == res_name), None)
        w, h  = (match[1], match[2]) if match else (900, 720)
        self.resizable(False, False)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ══════════════════════════════════════════════════════════════
    # NAVIGATION  (each method delegates to a screen module)
    # ══════════════════════════════════════════════════════════════

    def _clear(self):
        for w in self._container.winfo_children():
            w.destroy()

    def _timer_stop(self):
        """Cancel any running countdown — safe to call from anywhere."""
        if self._timer_after is not None:
            self.after_cancel(self._timer_after)
            self._timer_after = None

    def show_pre_menu(self):
        from .screens.pre_menu import build_intro_screen
        build_intro_screen(self)

    def show_pre_menu_profiles(self):
        from .screens.pre_menu import build_profile_selection_screen
        build_profile_selection_screen(self)

    def show_menu(self):
        self._current_screen = "menu"
        from .screens.menu import build
        build(self)
        
        # Perform server health check in background
        self._check_server_health()

    def show_singleplayer_submenu(self):
        from .screens.menu import build_singleplayer_submenu
        build_singleplayer_submenu(self)

    def show_multiplayer_submenu(self):
        from .screens.menu import build_multiplayer_submenu
        build_multiplayer_submenu(self)

    def show_multiplayer_normal(self):
        from .screens.multiplayer_normal import build
        build(self)

    def show_create_table(self):
        from .screens.create_table import build
        build(self)

    def show_streamer_vs_viewer(self):
        from .screens.streamer_config import build
        build(self)

    def show_options(self):
        from .screens.options import build
        build(self)

    def show_profile(self, profile_name: str | None = None):
        self._profile_view_target = profile_name
        from .screens.profile import build
        build(self)

    def show_top_scores(self):
        from .screens.top_scores import build
        build(self)

    def show_achievements(self):
        from .screens.achievements import build
        build(self)

    def show_ranked(self):
        from .screens.ranked import build
        build(self)

    def start_new_game(self, mode: str = None):
        if mode is None:
            from .screens.menu import build_mode_picker
            build_mode_picker(self)
        else:
            self.game_state = GameState(self.all_questions, mode=mode)
            self._current_screen = "game"
            from .screens.game_screen import build
            build(self)

    def load_game(self):
        sv = self.data.get("save")
        if not sv:
            messagebox.showinfo("", self.s("no_save"), parent=self)
            return
        # Verify save integrity
        from singleplayer.anticheat import verify_save
        if not verify_save(sv, self.all_questions):
            messagebox.showwarning(
                "",
                ("Save file appears to have been modified and cannot be loaded."
                 if self._lang.get("code","en") == "en" else
                 "Le fichier de sauvegarde semble avoir été modifié et ne peut pas être chargé."),
                parent=self
            )
            return
        self.game_state = GameState.from_dict(self.all_questions, sv)
        from .screens.game_screen import build
        build(self)

    # ══════════════════════════════════════════════════════════════
    # POPUP HELPERS  (used by game_screen and singleplayer/logic)
    # ══════════════════════════════════════════════════════════════

    def _show_xp_toast(self, xp: int):
        try:
            ov = tk.Toplevel(self)
            ov.configure(bg=BG_DARK)
            ov.resizable(False, False)
            ov.overrideredirect(True)
            ov.attributes("-alpha", 0.92)
            tk.Label(ov, text=f"+{xp} XP ✨",
                     bg=BG_DARK, fg=GOLD,
                     font=self.f_lifeline, padx=14, pady=6).pack()
            ov.update_idletasks()
            x = self.winfo_x() + self.winfo_width() - ov.winfo_width() - 20
            y = self.winfo_y() + 60
            ov.geometry(f"+{x}+{y}")
            ov.after(1400, ov.destroy)
        except Exception:
            pass

    def _show_levelup_popup(self, new_level: int, xp_gained: int):
        lang  = self._lang.get("code", "en")
        from constants import player_title
        title = player_title(new_level, lang)
        self.sound.play_jingle("safe_haven")

        ov = tk.Toplevel(self)
        ov.configure(bg=GOLD)
        ov.resizable(False, False)
        ov.overrideredirect(True)
        tk.Label(ov, text="🎖  LEVEL UP!", bg=GOLD, fg=BG_DARK,
                 font=self.f_prize_hl, padx=24, pady=6).pack()
        tk.Label(ov,
                 text=f"Level {new_level}!" if lang=="en" else f"Niveau {new_level} !",
                 bg=GOLD, fg=BG_DARK, font=self.f_big, padx=24).pack()
        tk.Label(ov, text=f"✦  {title}  ✦",
                 bg=GOLD, fg=BG_DARK, font=self.f_lifeline, padx=24, pady=4).pack()
        tk.Label(ov,
                 text=f"+{xp_gained} XP this game" if lang=="en" else f"+{xp_gained} XP cette partie",
                 bg=GOLD, fg=BG_DARK, font=self.f_small, padx=24, pady=4).pack()
        ov.update_idletasks()
        mw, mh = self.winfo_width(), self.winfo_height()
        mx, my = self.winfo_x(), self.winfo_y()
        ow, oh = ov.winfo_width(), ov.winfo_height()
        ov.geometry(f"+{mx+(mw-ow)//2}+{my+(mh-oh)//2}")
        ov.after(3200, ov.destroy)

    def _show_achievement_popups(self, newly_unlocked: list):
        self.sound.play_jingle("achievement")
        lang = self._lang.get("code", "en")
        for ach_id in newly_unlocked:
            ach  = next((a for a in self.ach_defs if a["id"] == ach_id), None)
            if not ach:
                continue
            name = ach["name"].get(lang, ach["name"].get("en", ach_id))
            msg  = self.s("ach_unlocked", name=f"{ach.get('icon','🎖')} {name}")
            ov   = tk.Toplevel(self)
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
    
    def _check_server_health(self):
        """Check server health in background and update UI."""
        try:
            import threading
            def _health_check():
                # Check if server is online (non-blocking, 3 sec timeout)
                is_online = self.api.health_check()
                self.data["server"]["is_online"] = is_online
                # Save updated status
                from utils import save_data
                save_data(self.data, silent=True)
            
            # Run check in separate thread to avoid blocking UI
            thread = threading.Thread(target=_health_check, daemon=True)
            thread.start()
        except Exception:
            pass
