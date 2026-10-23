"""
screens/top_scores.py — Sub Ladder
Top Scores screen with mode filter tabs.
"""

import tkinter as tk

from constants import (
    GOLD, BG_DARK, BG_MID, BG_PANEL, SILVER, WHITE,
    MENU_BTN_BG, BTN_DEFAULT, TEXT_DISABLED,
    GAME_MODES,
)


def build(app):
    app._clear()
    f    = app._container
    lang = app._lang.get("code", "en")

    tk.Label(f, text=app.s("top_scores"), bg=app.BG_DARK, fg=app.GOLD,
             font=app.f_title).pack(pady=(24, 8))

    profiles = app.data["profiles"]
    all_scores = []
    for pname, pdata in profiles.items():
        for sc in pdata.get("scores", []):
            all_scores.append({
                "profile": pname,
                "subs":    sc["subs"],
                "level":   sc["level"],
                "won":     sc.get("won", False),
                "mode":    sc.get("mode", "normal"),
            })
    all_scores.sort(key=lambda x: x["subs"], reverse=True)

    # ── Mode filter tabs ──────────────────────────────────────────
    tab_frame     = tk.Frame(f, bg=app.BG_DARK)
    tab_frame.pack(pady=(0, 8))
    selected_mode = tk.StringVar(value="all")

    tbl_outer  = tk.Frame(f, bg=app.BG_PANEL)
    tbl_outer.pack(padx=32, pady=4, fill="x")

    headers = ["#", "Profile", "Subs", "Level", "Mode", ""]
    widths  = [3, 12, 7, 5, 10, 3]
    for col, (h, w) in enumerate(zip(headers, widths)):
        tk.Label(tbl_outer, text=h, bg=app.BG_PANEL, fg=app.GOLD,
                 font=app.f_prize_hl, width=w, anchor="w"
                 ).grid(row=0, column=col, padx=4, pady=4, sticky="w")

    row_widgets = []

    def refresh_table():
        for wlist in row_widgets:
            for widget in wlist:
                widget.destroy()
        row_widgets.clear()

        mode_filter = selected_mode.get()
        filtered    = [s for s in all_scores
                       if mode_filter == "all" or s["mode"] == mode_filter]
        top = filtered[:10]

        if not top:
            lbl = tk.Label(tbl_outer, text=app.s("no_scores"),
                           bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small)
            lbl.grid(row=1, column=0, columnspan=6, pady=10)
            row_widgets.append([lbl])
            return

        for i, sc in enumerate(top):
            row_bg     = app.BG_MID if i % 2 == 0 else app.BG_PANEL
            mode_info  = GAME_MODES.get(sc["mode"], GAME_MODES["normal"])
            mode_label = mode_info.get(f"label_{lang}", mode_info["label_en"])
            mode_color = mode_info["color"]
            vals       = [i+1, sc["profile"], sc["subs"],
                          sc["level"], mode_label, "🏆" if sc["won"] else ""]
            colors     = [app.WHITE, app.WHITE, app.WHITE, app.WHITE, mode_color, app.GOLD]
            row_w = []
            for col, (val, w, color) in enumerate(zip(vals, widths, colors)):
                lbl = tk.Label(tbl_outer, text=str(val), bg=row_bg,
                               fg=color, font=app.f_small, width=w, anchor="w")
                lbl.grid(row=i+1, column=col, padx=4, pady=2, sticky="w")
                row_w.append(lbl)
            row_widgets.append(row_w)

    def make_tab(mode_id, label, color):
        def cmd():
            selected_mode.set(mode_id)
            refresh_table()
        tk.Button(tab_frame, text=label, bg=app.BTN_DEFAULT, fg=color,
                  font=app.f_small, relief="flat", cursor="hand2",
                  padx=10, pady=4, command=cmd).pack(side="left", padx=3)

    make_tab("all", "All" if lang == "en" else "Tous", app.GOLD)
    for mid, info in GAME_MODES.items():
        lbl = info.get(f"label_{lang}", info["label_en"])
        make_tab(mid, lbl, info["color"])

    refresh_table()

    back_btn = tk.Button(f, text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=6,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
              command=app.show_menu)
    back_btn.pack(pady=16)
    
    def _back_enter(e=None):
        back_btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)
    def _back_leave(e=None):
        back_btn.config(bg=app.MENU_BTN_BG, highlightbackground=app.MENU_BTN_BG, highlightthickness=0)
    back_btn.bind("<Enter>", _back_enter)
    back_btn.bind("<Leave>", _back_leave)
