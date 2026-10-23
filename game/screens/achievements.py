"""
screens/achievements.py — Sub Ladder
Achievements screen: shows all achievements, locked/unlocked/secret.
"""

import tkinter as tk

from constants import (
    GOLD, BG_DARK, BG_MID, BG_PANEL, SILVER, WHITE,
    MENU_BTN_BG, TEXT_DISABLED,
)


def build(app):
    app._clear()
    f    = app._container
    lang = app._lang.get("code", "en")

    profile  = app.data.get("active_profile")
    unlocked = set()
    if profile and profile in app.data["profiles"]:
        unlocked = set(app.data["profiles"][profile].get("achievements", []))

    tk.Label(f, text=app.s("achievements"), bg=BG_DARK, fg=GOLD,
             font=app.f_title).pack(pady=(24, 12))

    # Stats line
    total = len(app.ach_defs)
    done  = len(unlocked)
    pct   = int(done / max(total, 1) * 100)
    tk.Label(f, text=f"{done} / {total}  ({pct}%)",
             bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack(pady=(0, 8))

    # Scrollable list
    outer = tk.Frame(f, bg=app.BG_DARK)
    outer.pack(fill="both", expand=True, padx=24)

    canvas    = tk.Canvas(outer, bg=app.BG_DARK, highlightthickness=0)
    scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = tk.Frame(canvas, bg=app.BG_DARK)
    win   = canvas.create_window((0, 0), window=inner, anchor="nw")

    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
    inner.bind("<Configure>", lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")))
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    if not app.ach_defs:
        tk.Label(inner, text=app.s("no_achievements"),
                 bg=app.BG_DARK, fg=app.SILVER, font=app.f_label).pack(pady=20)
    else:
        for ach in app.ach_defs:
            is_unlocked = ach["id"] in unlocked
            is_secret   = ach.get("secret", False) and not is_unlocked
            icon        = ach.get("icon", "🎖") if is_unlocked else ("❓" if is_secret else "🔒")
            name        = (ach["name"].get(lang, ach["name"].get("en", ach["id"]))
                           if not is_secret else "???")
            desc        = (ach["description"].get(lang, ach["description"].get("en", ""))
                           if not is_secret else "???")
            row_bg      = app.BG_MID if is_unlocked else app.BG_PANEL
            fg_col      = app.GOLD   if is_unlocked else app.SILVER

            row = tk.Frame(inner, bg=row_bg)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=f" {icon} ", bg=row_bg, fg=fg_col,
                     font=app.f_label).pack(side="left", padx=4)

            info = tk.Frame(row, bg=row_bg)
            info.pack(side="left", fill="x", expand=True, padx=4, pady=4)
            tk.Label(info, text=name, bg=row_bg, fg=fg_col,
                     font=app.f_prize_hl, anchor="w").pack(fill="x")
            tk.Label(info, text=desc, bg=row_bg, fg=app.SILVER,
                     font=app.f_small, anchor="w",
                     wraplength=500).pack(fill="x")

    back_btn = tk.Button(f, text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=6,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
              command=app.show_menu)
    back_btn.pack(pady=12)
    
    def _back_enter(e=None):
        back_btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)
    def _back_leave(e=None):
        back_btn.config(bg=app.MENU_BTN_BG, highlightbackground=app.MENU_BTN_BG, highlightthickness=0)
    back_btn.bind("<Enter>", _back_enter)
    back_btn.bind("<Leave>", _back_leave)
