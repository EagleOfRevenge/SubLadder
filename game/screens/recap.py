"""
screens/recap.py — Sub Ladder
End-of-game recap screen: stats, XP progress, scrollable question history.
"""

import tkinter as tk

from constants import (
    GOLD, BG_DARK, BG_MID, BG_PANEL, SILVER, WHITE, TEXT_DISABLED,
    MENU_BTN_BG, BTN_DEFAULT, BTN_CORRECT, BTN_SELECTED, BTN_WRONG,
    PRIZE_LADDER, GAME_MODES,
    player_level_from_xp, player_title,
)


def build(app, was_correct: bool = True, walked: bool = False):
    """Build the recap screen after a game ends."""
    app._clear()
    app._timer_stop()

    s    = app.game_state
    lang = app._lang.get("code", "en")

    # ── Headline ──────────────────────────────────────────────────
    if walked:
        headline = app.s("walk_away_title")
        sub_line = app.s("walk_away_sub", prize=s.walkout_prize_label)
        h_color  = app.GOLD
    elif s.won:
        headline = app.s("win_title")
        sub_line = app.s("win_sub", prize=PRIZE_LADDER[14])
        h_color  = app.GOLD
    else:
        headline = app.s("wrong_title")
        sub_line = app.s("wrong_sub", prize=s.safe_label)
        h_color  = "#e05050"

    # ── Stats ─────────────────────────────────────────────────────
    history   = s.history
    n_total   = len(history)
    n_correct = sum(1 for e in history if e["was_correct"])
    n_wrong   = n_total - n_correct
    avg_time  = (sum(e["time_secs"] for e in history) / n_total) if n_total else 0
    pct       = int(n_correct / n_total * 100) if n_total else 0

    profile     = app.data.get("active_profile")
    p_data      = app.data["profiles"].get(profile, {}) if profile else {}
    xp_earned   = p_data.get("xp_last_game", 0)
    total_xp    = p_data.get("total_xp", 0)
    plvl, xp_in, xp_need = player_level_from_xp(total_xp)
    title       = player_title(plvl, lang)

    # ── Layout ────────────────────────────────────────────────────
    outer = tk.Frame(app._container, bg=app.BG_DARK)
    outer.pack(fill="both", expand=True)

    # Header
    hdr = tk.Frame(outer, bg=app.BG_DARK)
    hdr.pack(fill="x", pady=(18, 4))
    tk.Label(hdr, text=headline, bg=app.BG_DARK, fg=h_color,
             font=app.f_big).pack()
    if sub_line:
        tk.Label(hdr, text=sub_line, bg=app.BG_DARK, fg=app.WHITE,
                 font=app.f_question).pack(pady=(2, 0))

    # Mode badge
    mode_info  = GAME_MODES.get(s.mode, GAME_MODES["normal"])
    mode_label = mode_info.get(f"label_{lang}", mode_info["label_en"])
    mode_color = mode_info["color"]
    tk.Label(hdr, text=f"[{mode_label}]",
             bg=app.BG_DARK, fg=mode_color, font=app.f_small).pack()

    # Stats bar
    stats_frame = tk.Frame(outer, bg=app.BG_PANEL)
    stats_frame.pack(fill="x", padx=24, pady=8)
    for icon, val in [("✅", str(n_correct)), ("❌", str(n_wrong)),
                      ("%",  f"{pct}%"),     ("⏱",  f"{avg_time:.0f}s"),
                      ("✨",  f"+{xp_earned} XP")]:
        col = tk.Frame(stats_frame, bg=app.BG_PANEL)
        col.pack(side="left", expand=True, pady=8)
        tk.Label(col, text=val,  bg=app.BG_PANEL, fg=app.GOLD,
                 font=app.f_prize_hl).pack()
        tk.Label(col, text=icon, bg=app.BG_PANEL, fg=app.SILVER,
                 font=app.f_small).pack()

    # XP progress bar
    xp_frame = tk.Frame(outer, bg=app.BG_PANEL)
    xp_frame.pack(fill="x", padx=24, pady=(0, 8))
    lbl_txt = (f"Lv.{plvl}  {title}  —  {xp_in} / {xp_need} XP"
               if lang == "en" else
               f"Niv.{plvl}  {title}  —  {xp_in} / {xp_need} XP")
    tk.Label(xp_frame, text=lbl_txt, bg=app.BG_PANEL, fg=app.GOLD,
             font=app.f_small).pack(anchor="w", padx=6)
    bar_bg = tk.Frame(xp_frame, bg=app.BG_MID, height=8)
    bar_bg.pack(fill="x", padx=6, pady=(2, 4))
    bar_bg.update_idletasks()
    fill_w = max(4, int((bar_bg.winfo_width() or 300) * xp_in / max(xp_need, 1)))
    tk.Frame(bar_bg, bg=app.GOLD, width=fill_w, height=8).place(x=0, y=0)

    tk.Label(outer, text="─" * 60, bg=app.BG_DARK, fg=app.BG_PANEL).pack()

    # ── Scrollable question history ───────────────────────────────
    list_frame = tk.Frame(outer, bg=app.BG_DARK)
    list_frame.pack(fill="both", expand=True, padx=24, pady=(4, 0))

    canvas    = tk.Canvas(list_frame, bg=app.BG_DARK, highlightthickness=0)
    scrollbar = tk.Scrollbar(list_frame, orient="vertical",
                              command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = tk.Frame(canvas, bg=app.BG_DARK)
    cwin  = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.bind("<Configure>",
                lambda e: canvas.itemconfig(cwin, width=e.width))
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    for entry in history:
        ok     = entry["was_correct"]
        row_bg = "#0e1a10" if ok else "#1a0e0e"
        icon   = "✅" if ok else "❌"

        row = tk.Frame(inner, bg=row_bg)
        row.pack(fill="x", pady=2, padx=2)

        left = tk.Frame(row, bg=row_bg, width=54)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text=f"{icon}\nQ{entry['level']}",
                 bg=row_bg, fg=app.GOLD if ok else "#e05050",
                 font=app.f_small, justify="center").pack(expand=True)

        mid = tk.Frame(row, bg=row_bg)
        mid.pack(side="left", fill="both", expand=True, padx=6, pady=4)
        tk.Label(mid, text=entry["question"], bg=row_bg, fg=app.WHITE,
                 font=app.f_small, anchor="w",
                 wraplength=420, justify="left").pack(fill="x")

        if ok:
            ans_text  = f"✓  {entry['correct_answer']}"
            ans_color = "#4caf50"
        else:
            ans_text  = (f"✗  {entry['your_answer']}   "
                         f"→  {entry['correct_answer']}")
            ans_color = "#ef5350"
        tk.Label(mid, text=ans_text, bg=row_bg, fg=ans_color,
                 font=app.f_small, anchor="w").pack(fill="x")

        # Explanation (if available in question JSON)
        expl = ""
        if app.game_state and app.game_state.current_q:
            pass  # history entries don't hold the full q; explanation shown in-game
        if entry.get("explanation"):
            tk.Label(mid, text=f"ℹ  {entry['explanation']}",
                     bg=row_bg, fg=app.SILVER,
                     font=app.f_small, anchor="w").pack(fill="x")

        src = entry.get("source", "")
        if src:
            tk.Label(mid, text=f"source : {src}", bg=row_bg,
                     fg=app.TEXT_DISABLED, font=app.f_small,
                     anchor="w").pack(fill="x")

        right = tk.Frame(row, bg=row_bg, width=52)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        tk.Label(right, text=f"⏱\n{entry['time_secs']}s",
                 bg=row_bg, fg=app.SILVER,
                 font=app.f_small, justify="center").pack(expand=True)

    # ── Bottom buttons ────────────────────────────────────────────
    btn_frame = tk.Frame(outer, bg=app.BG_DARK)
    btn_frame.pack(fill="x", pady=10, padx=24)

    retry_btn = tk.Button(btn_frame,
              text=f"↺  {mode_label}",
              bg=mode_color, fg=app.BG_DARK, font=app.f_lifeline,
              relief="flat", cursor="hand2", padx=14, pady=8,
              activebackground=app.BTN_HOVER, activeforeground=mode_color,
              highlightbackground=mode_color, highlightthickness=0,
              command=lambda: app.start_new_game(mode=s.mode)
              )
    retry_btn.pack(side="left", padx=4)
    
    def _retry_enter(e=None):
        retry_btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=1)
    def _retry_leave(e=None):
        retry_btn.config(bg=mode_color, highlightbackground=mode_color, highlightthickness=0)
    retry_btn.bind("<Enter>", _retry_enter)
    retry_btn.bind("<Leave>", _retry_leave)

    play_again_btn = tk.Button(btn_frame,
              text=app.s("play_again"),
              bg=app.MENU_BTN_ACT, fg=app.BG_DARK, font=app.f_lifeline,
              relief="flat", cursor="hand2", padx=14, pady=8,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_ACT, highlightthickness=0,
              command=app.start_new_game
              )
    play_again_btn.pack(side="left", padx=4)
    
    def _play_enter(e=None):
        play_again_btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=1)
    def _play_leave(e=None):
        play_again_btn.config(bg=app.MENU_BTN_ACT, highlightbackground=app.MENU_BTN_ACT, highlightthickness=0)
    play_again_btn.bind("<Enter>", _play_enter)
    play_again_btn.bind("<Leave>", _play_leave)

    back_btn = tk.Button(btn_frame,
              text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=app.f_small,
              relief="flat", cursor="hand2", padx=14, pady=8,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
              command=app.show_menu
              )
    back_btn.pack(side="left", padx=4)
    
    def _back_enter(e=None):
        back_btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)
    def _back_leave(e=None):
        back_btn.config(bg=app.MENU_BTN_BG, highlightbackground=app.MENU_BTN_BG, highlightthickness=0)
    back_btn.bind("<Enter>", _back_enter)
    back_btn.bind("<Leave>", _back_leave)
