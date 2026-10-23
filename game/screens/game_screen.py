"""
screens/game_screen.py — Sub Ladder
In-game screen: question box, answer buttons, lifelines, timer, pause overlay.
"""

import time
import tkinter as tk

from constants import (
    ANSWER_LABELS, ANIMATION_MS, QUESTION_TIME, SAFE_HAVENS,
    PRIZE_LADDER, GAME_MODES,
    player_level_from_xp, player_title, xp_for_correct,
    # ── Colors ──────────────────────────────────────────────────
    BG_DARK, BG_MID, BG_PANEL,
    GOLD, GOLD_DARK, SILVER, WHITE, TEXT_DISABLED,
    BTN_DEFAULT, BTN_HOVER, BTN_SELECTED, BTN_CORRECT, BTN_WRONG, BTN_DISABLED,
    LIFELINE_ON, LIFELINE_OFF, LIFELINE_TEXT_ON, LIFELINE_TEXT_OFF,
    MENU_BTN_BG,
)


def build(app):
    """Build the game screen inside app._container."""
    app._clear()
    app._current_screen = "game"
    s = app.game_state

    # Music for this level
    from asset_manager import SoundEngine
    app.sound.play_music(SoundEngine.music_key_for_level(s.current_level))

    f = app._container

    # Background image
    from asset_manager import ImageLoader
    bg_key = ImageLoader.bg_key_for_level(s.current_level)
    bg_img = app.images.background(
        bg_key, size=(app.winfo_width() or 900, app.winfo_height() or 720))
    if bg_img:
        lbl = tk.Label(f, image=bg_img, bg=app.BG_DARK)
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        lbl._img_ref = bg_img

    # Title bar
    top = tk.Frame(f, bg=app.BG_DARK)
    top.pack(fill="x", padx=16, pady=(10, 0))
    tk.Label(top, text="✦  Sub Ladder  ✦",
             bg=app.BG_DARK, fg=app.GOLD, font=app.f_question).pack(side="left", expand=True)

    # Main area
    main = tk.Frame(f, bg=app.BG_DARK)
    main.pack(fill="both", expand=True, padx=16, pady=6)

    left = tk.Frame(main, bg=app.BG_DARK)
    left.pack(side="left", fill="both", expand=True)

    # ── Question box ──────────────────────────────────────────────
    q_outer = tk.Frame(left, bg=app.GOLD)
    q_outer.pack(fill="x", pady=(0, 8))
    q_inner = tk.Frame(q_outer, bg=app.BG_MID)
    q_inner.pack(fill="x", padx=2, pady=2)

    level_row = tk.Frame(q_inner, bg=app.BG_MID)
    level_row.pack(fill="x", padx=14, pady=(6, 0))
    app._lbl_level = tk.Label(level_row, text="", bg=app.BG_MID, fg=app.GOLD,
                               font=app.f_small, anchor="w")
    app._lbl_level.pack(side="left")
    app._lbl_timer = tk.Label(level_row, text="", bg=app.BG_MID, fg=app.GOLD,
                               font=app.f_small, anchor="e", width=14)
    app._lbl_timer.pack(side="right")

    app._lbl_question = tk.Label(q_inner, text="", wraplength=520,
                                  bg=app.BG_MID, fg=app.WHITE, font=app.f_question,
                                  justify="center")
    app._lbl_question.pack(fill="x", padx=16, pady=(4, 6))

    app._timer_canvas = tk.Canvas(q_inner, height=6, bg=app.BG_MID,
                                   highlightthickness=0)
    app._timer_canvas.pack(fill="x", padx=16, pady=(0, 8))
    app._timer_bar   = None
    app._timer_after = None
    app._timer_secs  = 0

    # ── Answer buttons ────────────────────────────────────────────
    app._ans_btns: dict = {}
    grid = tk.Frame(left, bg=app.BG_DARK)
    grid.pack(fill="x", pady=(0, 8))
    for label, row, col in [("A",0,0),("B",0,1),("C",1,0),("D",1,1)]:
        fr = tk.Frame(grid, bg=app.MENU_BTN_ACT)
        fr.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        btn = tk.Button(
            fr, text=f"  {label}:  ",
            bg=app.BTN_DEFAULT, fg=app.WHITE, font=app.f_answer,
            relief="flat", bd=0,
            activebackground=app.BTN_HOVER, activeforeground=app.WHITE,
            cursor="hand2", anchor="w", wraplength=210,
            justify="left", padx=10, pady=10,
            highlightbackground=app.BTN_DEFAULT, highlightthickness=1,
            command=lambda l=label: _on_answer(app, l)
        )
        btn.pack(fill="both", expand=True, padx=2, pady=2)
        
        def _make_ans_hover(button, label_key):
            def _on_enter(e=None):
                button.config(
                    bg=app.BTN_HOVER,
                    highlightbackground=app.MENU_BTN_ACT,
                    highlightthickness=2
                )
            def _on_leave(e=None):
                button.config(
                    bg=app.BTN_DEFAULT,
                    highlightbackground=app.BTN_DEFAULT,
                    highlightthickness=1
                )
            return _on_enter, _on_leave
        
        enter_h, leave_h = _make_ans_hover(btn, label)
        btn.bind("<Enter>", enter_h)
        btn.bind("<Leave>", leave_h)
        app._ans_btns[label] = btn
    grid.columnconfigure(0, weight=1)
    grid.columnconfigure(1, weight=1)

    # ── Lifelines ─────────────────────────────────────────────────
    ll_frame = tk.Frame(left, bg=app.BG_DARK)
    ll_frame.pack(fill="x", pady=(0, 6))
    app._btn_fifty  = _lifeline_btn(app, ll_frame, app.s("fifty"),  lambda: _use_fifty(app))
    app._btn_vote   = _lifeline_btn(app, ll_frame, app.s("vote"),   lambda: _use_vote(app))
    app._btn_switch = _lifeline_btn(app, ll_frame, app.s("switch"), lambda: _use_switch(app))
    for b in (app._btn_fifty, app._btn_vote, app._btn_switch):
        b.pack(side="left", padx=3, expand=True, fill="x")

    app._lbl_vote = tk.Label(left, text="", bg=app.BG_DARK, fg=app.GOLD, font=app.f_small)
    app._lbl_vote.pack(pady=(0, 3))

    # ── Bottom buttons ────────────────────────────────────────────
    bot = tk.Frame(left, bg=app.BG_DARK)
    bot.pack(fill="x", pady=(2, 0))

    def _make_bot_btn(text, cmd, fg_color=None):
        if fg_color is None:
            fg_color = app.MENU_BTN_FG
        b = tk.Button(bot, text=text,
              bg=app.BG_PANEL, fg=app.WHITE, font=app.f_small,
              relief="flat", cursor="hand2", padx=8, pady=5,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.BG_PANEL, highlightthickness=0,
              command=cmd)
        b.pack(side="left", padx=3)
        orig_bg = app.BG_PANEL
        orig_fg = fg_color
        def _bot_enter(e=None, btn=b):
            btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=1)
        def _bot_leave(e=None, btn=b):
            btn.config(bg=orig_bg, highlightbackground=orig_bg, highlightthickness=0)
        b.bind("<Enter>", _bot_enter)
        b.bind("<Leave>", _bot_leave)
        return b

    _make_bot_btn(app.s("walk_away"), lambda: _walk_away(app))
    _make_bot_btn(app.s("save_btn"), lambda: _save_game(app))
    _make_bot_btn("⏸  " + ("Pause" if app._lang.get("code","en")=="en" else "Pause"),
                  lambda: _show_pause(app))
    _make_bot_btn(app.s("new_game_btn"), app.start_new_game, fg_color=app.GOLD)

    # ── Prize ladder ──────────────────────────────────────────────
    right = tk.Frame(main, bg=app.BG_PANEL, width=150)
    right.pack(side="right", fill="y", padx=(12, 0))
    right.pack_propagate(False)
    tk.Label(right, text=app.s("prize_ladder"),
             bg=app.BG_PANEL, fg=app.GOLD, font=app.f_small).pack(pady=(8, 4))
    app._ladder_lbls = []
    for i in range(14, -1, -1):
        is_safe = (i+1) in SAFE_HAVENS
        icon    = "🔒 " if is_safe else "   "
        lbl = tk.Label(right,
                       text=f"{icon}{i+1:>2}.  {PRIZE_LADDER[i]}",
                       bg=app.BG_PANEL,
                       fg=app.GOLD_DARK if is_safe else app.SILVER,
                       font=app.f_prize, anchor="w", padx=6)
        lbl.pack(fill="x", pady=1)
        app._ladder_lbls.insert(0, lbl)

    _game_refresh(app)


# ══════════════════════════════════════════════════════════════════
# REFRESH
# ══════════════════════════════════════════════════════════════════

def _game_refresh(app):
    s          = app.game_state
    d          = s.displayed
    lang       = app._lang.get("code", "en")
    mode_info  = GAME_MODES.get(s.mode, GAME_MODES["normal"])
    mode_label = mode_info.get(f"label_{lang}", mode_info["label_en"])
    mode_color = mode_info["color"]

    app._lbl_level.config(
        text=app.s("question_lbl", lvl=s.current_level, prize=s.prize_label))
    app._lbl_timer.config(fg=mode_color)

    app._lbl_question.config(text=s.current_q["question"])

    for label in ANSWER_LABELS:
        btn = app._ans_btns[label]
        if label in s.eliminated:
            btn.config(text=f"  {label}:  —", bg=app.BTN_DISABLED,
                       fg=app.TEXT_DISABLED, state="disabled", cursor="arrow")
        else:
            btn.config(text=f"  {label}:  {d['answers'][label]}",
                       bg=app.BTN_DEFAULT, fg=app.WHITE,
                       state="normal", cursor="hand2")

    for btn, key in [(app._btn_fifty,"fifty"),(app._btn_vote,"vote"),(app._btn_switch,"switch")]:
        if s.lifelines[key]:
            btn.config(bg=app.LIFELINE_ON, fg=app.LIFELINE_TEXT_ON,
                       state="normal", cursor="hand2")
        else:
            btn.config(bg=app.LIFELINE_OFF, fg=app.LIFELINE_TEXT_OFF,
                       state="disabled", cursor="arrow")

    app._lbl_vote.config(text="")

    for i, lbl in enumerate(app._ladder_lbls):
        level   = i + 1
        is_safe = level in SAFE_HAVENS
        if level == s.current_level:
            lbl.config(bg=app.GOLD, fg=app.BG_DARK, font=app.f_prize_hl)
        elif level < s.current_level:
            lbl.config(bg=app.BG_PANEL, fg=app.BTN_CORRECT, font=app.f_prize)
        else:
            lbl.config(bg=app.BG_PANEL, fg=app.GOLD_DARK if is_safe else app.SILVER,
                       font=app.f_prize)

    app._q_start_time = time.time()
    _timer_start(app)


# ══════════════════════════════════════════════════════════════════
# TIMER
# ══════════════════════════════════════════════════════════════════

def _timer_start(app):
    _timer_stop(app)
    if QUESTION_TIME <= 0:
        return
    app._timer_secs = QUESTION_TIME
    _timer_tick(app)


def _timer_stop(app):
    if hasattr(app, "_timer_after") and app._timer_after is not None:
        app.after_cancel(app._timer_after)
        app._timer_after = None


def _timer_tick(app):
    secs = app._timer_secs
    mode_info  = GAME_MODES.get(app.game_state.mode, GAME_MODES["normal"])
    mode_label = mode_info.get(f"label_{app._lang.get('code','en')}", mode_info["label_en"])
    mode_color = mode_info["color"]

    try:
        app._lbl_timer.config(
            text=f"[{mode_label}]  ⏱ {secs}s",
            fg=mode_color)
        app._timer_canvas.update_idletasks()
        total_w = app._timer_canvas.winfo_width()
    except tk.TclError:
        return

    ratio = secs / QUESTION_TIME
    bar_w = max(0, int(total_w * ratio))

    if ratio > 0.5:
        t = (1 - ratio) * 2
        r = int(0x1a + (0xc8 - 0x1a) * t)
        g = int(0x7a + (0x78 - 0x7a) * t)
        b = int(0x3a + (0x00 - 0x3a) * t)
    else:
        t = (0.5 - ratio) * 2
        r = int(0xc8 + (0x7a - 0xc8) * t)
        g = int(0x78 + (0x1a - 0x78) * t)
        b = int(0x00 + (0x1a - 0x00) * t)
    color = f"#{r:02x}{g:02x}{b:02x}"

    app._timer_canvas.delete("all")
    if bar_w > 0:
        h = app._timer_canvas.winfo_height() or 6
        app._timer_canvas.create_rectangle(0, 0, bar_w, h,
                                            fill=color, outline="")

    if secs > 0:
        app._timer_secs -= 1
        app._timer_after = app.after(1000, lambda: _timer_tick(app))
    else:
        app._lbl_timer.config(text="⏱ 0s", fg="#7a1a1a")


# ══════════════════════════════════════════════════════════════════
# ANSWER FLOW
# ══════════════════════════════════════════════════════════════════

def _on_answer(app, label: str):
    _timer_stop(app)
    _set_ans_state(app, "disabled")
    _disable_lifelines(app)
    app.sound.play_jingle("answer_selected")
    app._ans_btns[label].config(bg=app.BTN_SELECTED)
    app.update()
    app.after(ANIMATION_MS, lambda: _reveal(app, label))


def _reveal(app, chosen: str):
    correct = app.game_state.displayed["correct"]
    if chosen == correct:
        app._ans_btns[chosen].config(bg=app.BTN_CORRECT)
        app.sound.play_jingle("correct")
    else:
        app._ans_btns[chosen].config(bg=app.BTN_WRONG)
        app._ans_btns[correct].config(bg=app.BTN_CORRECT)
        app.sound.play_jingle("wrong")
        expl = app.game_state.current_q.get("explanation", "")
        if expl:
            app._lbl_vote.config(text=f"ℹ  {expl}", fg=app.SILVER)
    app.update()
    app.after(1000, lambda: _advance(app, chosen))


def _advance(app, chosen: str):
    import time as _time
    s          = app.game_state
    prev_level = s.current_level
    elapsed    = round(_time.time() - getattr(app, "_q_start_time", _time.time()))
    correct_label = s.displayed["correct"]
    was_correct   = chosen == correct_label

    s.history.append({
        "level":          prev_level,
        "question":       s.current_q["question"],
        "your_label":     chosen,
        "your_answer":    s.displayed["answers"][chosen],
        "correct_label":  correct_label,
        "correct_answer": s.displayed["answers"][correct_label],
        "was_correct":    was_correct,
        "time_secs":      elapsed,
        "source":         s.current_q.get("source", ""),
        "theme":          s.current_q.get("theme", ""),
        "explanation":    s.current_q.get("explanation", ""),
    })

    if was_correct:
        xp = xp_for_correct(s.mode, prev_level)
        app.after(500, lambda x=xp: app._show_xp_toast(x))

    ok = s.answer(chosen)

    if s.game_over:
        if s.won:
            app.sound.play_jingle("win")
        from singleplayer.logic import record_score
        xp_gained, leveled_up, new_lvl, newly = record_score(
            app.data, s, ok, walked=False
        )
        if newly:
            app.after(1200, lambda: app._show_achievement_popups(newly))
        if leveled_up:
            delay = 2800 if newly else 1200
            app.after(delay, lambda lv=new_lvl, xp=xp_gained:
                      app._show_levelup_popup(lv, xp))
        from .recap import build as recap_build
        app.after(1200, lambda: recap_build(app, ok, walked=False))
    else:
        if prev_level in SAFE_HAVENS:
            app.sound.play_jingle("safe_haven")
        from asset_manager import SoundEngine
        app.sound.play_music(SoundEngine.music_key_for_level(s.current_level))
        _game_refresh(app)


# ══════════════════════════════════════════════════════════════════
# LIFELINES
# ══════════════════════════════════════════════════════════════════

def _use_fifty(app):
    app.game_state.fifty_fifty()
    _game_refresh(app)


def _use_vote(app):
    results = app.game_state.chat_vote()
    parts   = "  ".join(f"{k}: {results[k]}%" for k in ANSWER_LABELS)
    app._lbl_vote.config(text=app.s("vote_result", parts=parts))
    for btn, key in [(app._btn_fifty,"fifty"),(app._btn_vote,"vote"),(app._btn_switch,"switch")]:
        if app.game_state.lifelines[key]:
            btn.config(bg=app.LIFELINE_ON, fg=app.LIFELINE_TEXT_ON,
                       state="normal", cursor="hand2")
        else:
            btn.config(bg=app.LIFELINE_OFF, fg=app.LIFELINE_TEXT_OFF,
                       state="disabled", cursor="arrow")


def _use_switch(app):
    app.game_state.switch()
    app._lbl_vote.config(text="")
    _game_refresh(app)


# ══════════════════════════════════════════════════════════════════
# PAUSE
# ══════════════════════════════════════════════════════════════════

def _show_pause(app):
    _timer_stop(app)
    lang = app._lang.get("code", "en")

    ov = tk.Toplevel(app)
    ov.title("")
    ov.configure(bg=app.BG_DARK)
    ov.resizable(False, False)
    ov.grab_set()

    tk.Label(ov,
             text="⏸  " + ("Paused" if lang=="en" else "Pause"),
             bg=app.BG_DARK, fg=app.GOLD, font=app.f_big,
             padx=40, pady=24).pack()

    msg = ("The question is hidden while the game is paused."
           if lang=="en" else
           "La question est masquée pendant la pause.")
    tk.Label(ov, text=msg, bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_small, padx=30).pack(pady=(0, 16))

    btn_frame = tk.Frame(ov, bg=app.BG_DARK)
    btn_frame.pack(pady=12, padx=30)

    def resume():
        ov.destroy()
        if QUESTION_TIME > 0 and app._timer_secs > 0:
            app._timer_after = None
            _timer_tick(app)

    tk.Button(btn_frame,
              text="▶  " + ("Resume" if lang=="en" else "Reprendre"),
              bg=app.GOLD, fg=app.BG_DARK, font=app.f_lifeline,
              relief="flat", cursor="hand2", padx=16, pady=8,
              command=resume).pack(side="left", padx=6)

    tk.Button(btn_frame,
              text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=8,
              command=lambda: [ov.destroy(), app.show_menu()]
              ).pack(side="left", padx=6)

    ov.update_idletasks()
    mw, mh = app.winfo_width(), app.winfo_height()
    mx, my = app.winfo_x(),    app.winfo_y()
    ow, oh = ov.winfo_width(), ov.winfo_height()
    ov.geometry(f"+{mx+(mw-ow)//2}+{my+(mh-oh)//2}")


# ══════════════════════════════════════════════════════════════════
# WALK AWAY
# ══════════════════════════════════════════════════════════════════

def _walk_away(app):
    if app.game_state.game_over:
        return
    lang  = app._lang.get("code", "en")
    prize = app.game_state.walkout_prize_label
    msg   = (f"Walk away and keep {prize}?" if lang=="en"
             else f"Abandonner et repartir avec {prize} ?")
    from tkinter import messagebox
    if not messagebox.askyesno("", msg, parent=app):
        return
    _timer_stop(app)
    app.game_state.walk_away()
    from singleplayer.logic import record_score
    xp_gained, leveled_up, new_lvl, newly = record_score(
        app.data, app.game_state, won=False, walked=True
    )
    if newly:
        app.after(800, lambda: app._show_achievement_popups(newly))
    if leveled_up:
        delay = 2800 if newly else 800
        app.after(delay, lambda lv=new_lvl, xp=xp_gained:
                  app._show_levelup_popup(lv, xp))
    from .recap import build as recap_build
    recap_build(app, was_correct=True, walked=True)


# ══════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════

def _save_game(app):
    from ..singleplayer.anticheat import sign_save
    from ..utils import save_data
    from tkinter import messagebox
    sv = app.game_state.to_dict()
    sv["profile"] = app.data.get("active_profile")
    app.data["save"] = sign_save(sv)
    save_data(app.data, silent=True)
    messagebox.showinfo("", app.s("save_ok"), parent=app)


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _lifeline_btn(app, parent, text, cmd):
    bg = app.LIFELINE_ON
    fg = app.LIFELINE_TEXT_ON
    btn = tk.Button(parent, text=text,
                     bg=bg, fg=fg,
                     font=app.f_lifeline, relief="flat",
                     cursor="hand2", padx=6, pady=7,
                     activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
                     highlightbackground=bg, highlightthickness=1,
                     command=cmd)
    def _ll_enter(e=None, b=btn):
        b.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)
    def _ll_leave(e=None, b=btn):
        b.config(bg=bg, highlightbackground=bg, highlightthickness=1)
    btn.bind("<Enter>", _ll_enter)
    btn.bind("<Leave>", _ll_leave)
    return btn


def _set_ans_state(app, state: str):
    for btn in app._ans_btns.values():
        btn.config(state=state)


def _disable_lifelines(app):
    for btn in (app._btn_fifty, app._btn_vote, app._btn_switch):
        btn.config(state="disabled")
