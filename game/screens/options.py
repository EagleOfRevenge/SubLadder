"""
screens/options.py — Sub Ladder
Options screen: language, resolution, fullscreen, volume, color theme.
"""

import tkinter as tk

from ..constants import RESOLUTIONS, COLOR_THEMES, GOLD, BG_DARK, BG_MID, SILVER, WHITE, MENU_BTN_BG


def build(app):
    """Build the Options screen inside app._container."""
    app._clear()
    f    = app._container
    opts = app.data["options"]

    tk.Label(f, text=app.s("options"), bg=app.BG_DARK, fg=app.GOLD,
             font=app.f_title).pack(pady=(30, 20))

    # ── Language ──────────────────────────────────────────────────
    from ..utils import list_languages
    tk.Label(f, text=app.s("lang_label"), bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_label).pack()
    lang_var    = tk.StringVar(value=opts.get("language", "English"))
    lang_frame  = tk.Frame(f, bg=app.BG_DARK)
    lang_frame.pack(pady=(4, 16))

    for lng in list_languages():
        row  = tk.Frame(lang_frame, bg=app.BG_DARK)
        row.pack(side="left", padx=10)
        code = lng[:2].lower()
        flag_img = app.images.flag(code, size=(32, 20))
        if flag_img:
            lbl = tk.Label(row, image=flag_img, bg=app.BG_DARK)
            lbl.pack(side="left", padx=(0, 4))
            lbl._img_ref = flag_img
        tk.Radiobutton(
            row, text=lng, variable=lang_var, value=lng,
            bg=app.BG_DARK, fg=app.WHITE, selectcolor=app.BG_MID,
            activebackground=app.BG_DARK, activeforeground=app.GOLD,
            font=app.f_label
        ).pack(side="left")

    # ── Color theme ───────────────────────────────────────────────
    tk.Label(f, text="🎨  " + ("Color theme" if app._lang.get("code","en") == "en"
             else "Thème de couleur"),
             bg=app.BG_DARK, fg=app.SILVER, font=app.f_label).pack()
    theme_var  = tk.StringVar(value=opts.get("theme", "Dark Navy"))
    theme_frame = tk.Frame(f, bg=app.BG_DARK)
    theme_frame.pack(pady=(4, 16))
    for name in COLOR_THEMES:
        tk.Radiobutton(
            theme_frame, text=name, variable=theme_var, value=name,
            bg=app.BG_DARK, fg=app.WHITE, selectcolor=app.BG_MID,
            activebackground=app.BG_DARK, activeforeground=app.GOLD,
            font=app.f_small
        ).pack(side="left", padx=10)

    # ── Resolution ────────────────────────────────────────────────
    tk.Label(f, text=app.s("res_label"), bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_label).pack()
    res_var = tk.StringVar(value=opts.get("resolution", "900 × 720"))
    fs_var  = tk.BooleanVar(value=opts.get("fullscreen", False))
    res_frame = tk.Frame(f, bg=app.BG_DARK)
    res_frame.pack(pady=(4, 4))
    for name, *_ in RESOLUTIONS:
        tk.Radiobutton(
            res_frame, text=name, variable=res_var, value=name,
            bg=app.BG_DARK, fg=app.WHITE, selectcolor=app.BG_MID,
            activebackground=app.BG_DARK, activeforeground=app.GOLD,
            font=app.f_small
        ).pack(anchor="w", padx=40)
    tk.Checkbutton(
        f, text=app.s("fullscreen"), variable=fs_var,
        bg=app.BG_DARK, fg=app.WHITE, selectcolor=app.BG_MID,
        activebackground=app.BG_DARK, activeforeground=app.GOLD,
        font=app.f_small
    ).pack(pady=(4, 16))

    # ── Volume sliders ────────────────────────────────────────────
    lang_code = app._lang.get("code", "en")
    for lbl_key, opt_key, default in [
        ("🎵  " + ("Music volume"  if lang_code == "en" else "Volume musique"),  "music_volume",  0.7),
        ("🔊  " + ("Sound effects" if lang_code == "en" else "Effets sonores"),   "sfx_volume",    0.7),
    ]:
        tk.Label(f, text=lbl_key, bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack()
        var = tk.DoubleVar(value=opts.get(opt_key, default))
        tk.Scale(
            f, from_=0.0, to=1.0, resolution=0.05,
            orient="horizontal", variable=var,
            bg=app.BG_DARK, fg=app.GOLD, troughcolor=app.BG_MID,
            highlightthickness=0, length=200,
        ).pack(pady=(0, 8))
        # store var reference so apply() can read it
        setattr(app, f"_opt_{opt_key}", var)

    # ── Apply ─────────────────────────────────────────────────────
    def apply():
        app.data["options"]["language"]     = lang_var.get()
        app.data["options"]["resolution"]   = res_var.get()
        app.data["options"]["fullscreen"]   = fs_var.get()
        app.data["options"]["theme"]        = theme_var.get()
        app.data["options"]["music_volume"] = app._opt_music_volume.get()
        app.data["options"]["sfx_volume"]   = app._opt_sfx_volume.get()
        app.sound.music_volume = app._opt_music_volume.get()
        app.sound.sfx_volume   = app._opt_sfx_volume.get()
        from ..utils import save_data
        save_data(app.data)
        app._load_lang()
        app._setup_fonts()
        app._apply_theme_colors()
        app.configure(bg=app.BG_DARK)
        app._container.configure(bg=app.BG_DARK)
        app._apply_resolution()
        
        # Vider le cache des images pour forcer le rechargement avec les nouvelles couleurs
        app.images._cache.clear()
        
        # Reconstruire l'écran actuel avec les nouvelles couleurs
        current = getattr(app, "_current_screen", "menu")
        app._clear()
        if current == "game":
            from .game_screen import build as game_build
            game_build(app)
        else:
            from .menu import build as menu_build
            menu_build(app)

    apply_btn = tk.Button(f, text=app.s("apply"),
              bg=app.MENU_BTN_ACT, fg=app.BG_DARK, font=app.f_lifeline,
              relief="flat", cursor="hand2", padx=20, pady=8,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_ACT, highlightthickness=0,
              command=apply)
    apply_btn.pack(pady=6)
    
    def _apply_enter(e=None):
        apply_btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)
    def _apply_leave(e=None):
        apply_btn.config(bg=app.MENU_BTN_ACT, highlightbackground=app.MENU_BTN_ACT, highlightthickness=0)
    apply_btn.bind("<Enter>", _apply_enter)
    apply_btn.bind("<Leave>", _apply_leave)
    
    back_btn = tk.Button(f, text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=6,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
              command=app.show_menu)
    back_btn.pack(pady=4)
    
    def _back_enter(e=None):
        back_btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)
    def _back_leave(e=None):
        back_btn.config(bg=app.MENU_BTN_BG, highlightbackground=app.MENU_BTN_BG, highlightthickness=0)
    back_btn.bind("<Enter>", _back_enter)
    back_btn.bind("<Leave>", _back_leave)
