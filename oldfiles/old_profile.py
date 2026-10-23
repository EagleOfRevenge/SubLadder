"""
screens/profile.py — Sub Ladder
Profile screen: XP/level, stats, per-mode stats, last 10 games, export.
"""

import json
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import datetime
import os
import threading
import time

from constants import (
    GOLD, BG_DARK, BG_MID, BG_PANEL, SILVER, WHITE, TEXT_DISABLED,
    MENU_BTN_BG, BTN_DEFAULT, BTN_WRONG, LIFELINE_ON,
    BTN_CORRECT, BTN_SELECTED,
    GAME_MODES, player_level_from_xp, player_title,
)
from ui_helpers import create_scrollable_frame
from utils import save_data


def build(app):
    """Build the Profile screen with scrollable content."""
    app._clear()
    
    f        = app._container
    profiles = app.data["profiles"]
    active   = app.data.get("active_profile")
    profile_name = getattr(app, "_profile_view_target", None) or active
    app._profile_view_target = None
    lang     = app._lang.get("code", "en")

    # Header (not scrollable)
    header = tk.Frame(f, bg=app.BG_DARK)
    header.pack(fill="x", padx=0, pady=0)
    tk.Label(header, text=app.s("profile_title"), bg=app.BG_DARK, fg=app.GOLD,
             font=app.f_title).pack(pady=(24, 6))

    # Scrollable content area
    canvas, content_frame = create_scrollable_frame(f, app.BG_DARK)
    
    # ── Profile list with avatars ──────────────────────────────────
    list_frame = tk.Frame(content_frame, bg=app.BG_DARK)
    list_frame.pack(pady=8, fill="x", anchor="center")
    if profiles:
        for name in sorted(profiles.keys()):
            marker = "▶ " if name == active else "   "
            color  = app.GOLD if name == active else app.WHITE
            
            profile_row = tk.Frame(list_frame, bg=app.BG_DARK)
            profile_row.pack(pady=2, fill="x", padx=30, anchor="center")
            
            avatar_img = _load_profile_avatar(app, name, size=32)
            if avatar_img:
                avatar_lbl = tk.Label(profile_row, image=avatar_img, bg=app.BG_DARK)
                avatar_lbl.pack(side="left", padx=(0, 8))
                avatar_lbl._img_ref = avatar_img
            
            tk.Button(
                profile_row, text=f"{marker}{name}",
                bg=app.BTN_DEFAULT, fg=color, font=app.f_label,
                relief="flat", cursor="hand2", pady=6,
                command=lambda n=name: _select(app, n)
            ).pack(side="left", fill="x", expand=True)
    else:
        tk.Label(list_frame, text="—", bg=app.BG_DARK, fg=app.SILVER,
                 font=app.f_label).pack(anchor="center")

    # ── Active profile stats ──────────────────────────────────────
    if profile_name and profile_name in profiles:
        p      = profiles[profile_name]
        is_self_view = profile_name == active
        
        # Avatar display + change button
        avatar_section = tk.Frame(content_frame, bg=app.BG_DARK)
        avatar_section.pack(pady=(12, 0), fill="x", anchor="center")
        
        avatar_img = _load_profile_avatar(app, profile_name, size=96)
        if avatar_img:
            avatar_lbl = tk.Label(avatar_section, image=avatar_img, bg=app.BG_DARK)
            avatar_lbl.pack(anchor="center")
            avatar_lbl._img_ref = avatar_img
        else:
            placeholder = tk.Label(avatar_section, text="📷", bg=app.BG_DARK, 
                                 fg=app.SILVER, font=("Arial", 48))
            placeholder.pack(pady=8, anchor="center")
        
        if is_self_view:
            tk.Button(avatar_section, text="🖼️  Change avatar",
                     bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_small,
                     relief="flat", cursor="hand2", padx=10, pady=4,
                     command=lambda: _change_avatar(app, profile_name)).pack(pady=(4, 8), anchor="center")
        
        # Profile type indicator + sync status
        ptype = p.get("profile_type", "offline")
        ptype_icon = "🔒" if ptype == "online" else "📁"
        ptype_label = f"{ptype_icon}  {'Online Profile' if ptype == 'online' else 'Offline Profile'}"
        
        sync_status_frame = tk.Frame(content_frame, bg=app.BG_DARK)
        sync_status_frame.pack(pady=(2, 0), fill="x", anchor="center")
        
        tk.Label(sync_status_frame, text=ptype_label,
                 bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack(side="left", padx=10)
        
        sync_status_label = tk.Label(sync_status_frame, text="", 
                                     bg=app.BG_DARK, fg=app.SILVER, font=app.f_small)
        sync_status_label.pack(side="right", padx=10)
        sync_status_label._sync_status = "idle"  # idle, syncing, synced, error
        
        tk.Button(sync_status_frame, text="🚩 Flag profile" if lang == "en" else "🚩 Signaler",
             bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_small,
             relief="flat", cursor="hand2", padx=8, pady=2,
             command=lambda: _manual_flag_profile(app, profile_name)
             ).pack(side="right", padx=2)

        # For online profiles: trigger sync in background
        if ptype == "online":
            _trigger_profile_sync(app, profile_name, sync_status_label)
            
            # Add "Sync Now" button
            tk.Button(sync_status_frame, text="🔄 Sync",
                     bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_small,
                     relief="flat", cursor="hand2", padx=8, pady=2,
                     command=lambda: _trigger_profile_sync(app, active, sync_status_label, force=True)
                     ).pack(side="right", padx=2)
            
            # Show sync info panel
            sync_info = tk.Frame(content_frame, bg=app.BG_PANEL)
            sync_info.pack(pady=(4, 8), padx=30, fill="x")
            
            last_synced = p.get("last_synced")
            if last_synced:
                import datetime
                import time
                sync_time = datetime.datetime.fromtimestamp(last_synced)
                time_diff = time.time() - last_synced
                
                if time_diff < 60:
                    time_str = "just now"
                elif time_diff < 3600:
                    time_str = f"{int(time_diff/60)}m ago"
                else:
                    time_str = f"{int(time_diff/3600)}h ago"
                
                tk.Label(sync_info, text=f"Last sync: {time_str}",
                        bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small, anchor="center").pack()
            else:
                tk.Label(sync_info, text="Never synced (click Sync button)",
                        bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small, anchor="center").pack()
        else:
            ptype_label += "  (Local backup)"

        # If online profile, add tabs to fetch remote data (Overview / Stats / Matches / Ranked)
        if ptype == "online":
            tabs_frame = tk.Frame(content_frame, bg=app.BG_DARK)
            tabs_frame.pack(pady=(8, 6), padx=30, fill="x")

            remote_panel = tk.Frame(content_frame, bg=app.BG_PANEL)
            remote_panel.pack(fill="x", padx=30, pady=(0, 8))

            def _clear_remote():
                for w in remote_panel.winfo_children():
                    w.destroy()

            def _get_token():
                return app.data.get("auth", {}).get("tokens", {}).get(profile_name)

            def _show_error(msg):
                messagebox.showerror("", msg, parent=app)

            def _fetch_and_show(func, on_result):
                """Run network call in background and call on_result(result) on main thread."""
                def thread_fn():
                    try:
                        api = __import__("game.auth.client", fromlist=["APIClient"]).client.APIClient()
                    except Exception:
                        from game.auth.client import APIClient
                        api = APIClient()
                    token = _get_token()
                    if not token:
                        app.after(0, lambda: _show_error(app.s("no_auth_token") if hasattr(app, 's') else "No auth token"))
                        return
                    try:
                        result = func(api, token)
                        app.after(0, lambda: on_result(result))
                    except Exception as e:
                        app.after(0, lambda: _show_error(str(e)))
                threading.Thread(target=thread_fn, daemon=True).start()

            # Overview tab
            def _on_overview():
                _clear_remote()
                lbl = tk.Label(remote_panel, text=app.s("loading") if hasattr(app,'s') else "Loading...",
                               bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small)
                lbl.pack(pady=8)

                def call(api, token):
                    return api.get_profile_overview(profile_name, token)

                def done(res):
                    _clear_remote()
                    if res.get("error"):
                        _show_error(res.get("error"))
                        return
                    # Display overview
                    ov = res
                    tk.Label(remote_panel, text=f"{ov.get('game_name')} — {ov.get('current_rank', {}).get('display', '')}",
                             bg=app.BG_PANEL, fg=app.GOLD, font=app.f_prize_hl).pack(pady=(8,4))
                    tk.Label(remote_panel, text=f"Ranked wins: {ov.get('ranked_wins')}  ·  Games: {ov.get('games_played')}  ·  Win%: {ov.get('win_rate')}",
                             bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(pady=(0,8))

                _fetch_and_show(call, done)

            # Stats tab
            def _on_stats():
                _clear_remote()
                tk.Label(remote_panel, text=app.s("loading") if hasattr(app,'s') else "Loading...",
                         bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(pady=8)

                def call(api, token):
                    return api.get_profile_stats(profile_name, token)

                def done(res):
                    _clear_remote()
                    if res.get("error"):
                        _show_error(res.get("error"))
                        return
                    off = res.get("offline", {})
                    on = res.get("online", {})
                    tk.Label(remote_panel, text="Offline stats", bg=app.BG_PANEL, fg=app.GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(6,2))
                    tk.Label(remote_panel, text=f"Games: {off.get('games_played')}  ·  Wins: {off.get('games_won')}  ·  Win%: {off.get('win_rate')}",
                             bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(anchor="w", padx=8)
                    tk.Label(remote_panel, text="Online (ranked)", bg=app.BG_PANEL, fg=app.GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8,2))
                    tk.Label(remote_panel, text=f"ELO: {on.get('current_elo')}  ·  Rank: {on.get('current_rank', {}).get('display', '')}  ·  Win%: {on.get('ranked_win_rate')}",
                             bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(anchor="w", padx=8)

                _fetch_and_show(call, done)

            # Matches tab
            def _on_matches():
                _clear_remote()
                tk.Label(remote_panel, text=app.s("loading") if hasattr(app,'s') else "Loading...",
                         bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(pady=8)

                def call(api, token):
                    return api.get_profile_matches(profile_name, token, limit=20, offset=0)

                def done(res):
                    _clear_remote()
                    if res.get("error"):
                        _show_error(res.get("error"))
                        return
                    lst = res
                    if not isinstance(lst, list):
                        _show_error("Unexpected matches response")
                        return
                    for m in lst[:20]:
                        txt = f"{m.get('match_id')}  {m.get('opponent_name')}  {m.get('result')}  ({m.get('elo_change')})  {m.get('match_date')[:19]}"
                        tk.Label(remote_panel, text=txt, bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(anchor="w", padx=8, pady=2)

                _fetch_and_show(call, done)

            # Ranked tab
            def _on_ranked():
                _clear_remote()
                tk.Label(remote_panel, text=app.s("loading") if hasattr(app,'s') else "Loading...",
                         bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(pady=8)

                def call(api, token):
                    return api.get_profile_ranked(profile_name, token)

                def done(res):
                    _clear_remote()
                    if res.get("error"):
                        _show_error(res.get("error"))
                        return
                    pr = res.get('player_rank')
                    gch = res.get('grand_champions', [])
                    ch = res.get('champions', [])
                    if pr:
                        tk.Label(remote_panel, text=f"You: #{pr.get('rank')}  {pr.get('profile_name')}  {pr.get('elo')}",
                                 bg=app.BG_PANEL, fg=app.GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(6,2))
                    tk.Label(remote_panel, text="Grand Champions", bg=app.BG_PANEL, fg=app.GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8,2))
                    for g in gch:
                        tk.Label(remote_panel, text=f"#{g.get('rank')} {g.get('profile_name')} — {g.get('elo')}", bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(anchor="w", padx=12)
                    tk.Label(remote_panel, text="Champions", bg=app.BG_PANEL, fg=app.GOLD, font=app.f_small).pack(anchor="w", padx=8, pady=(8,2))
                    for c in ch:
                        tk.Label(remote_panel, text=f"#{c.get('rank')} {c.get('profile_name')} — {c.get('elo')}", bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(anchor="w", padx=12)

                _fetch_and_show(call, done)

            # Create tab buttons
            tk.Button(tabs_frame, text="Overview", bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_small,
                      relief="flat", cursor="hand2", command=_on_overview).pack(side="left", padx=6)
            tk.Button(tabs_frame, text="Stats", bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_small,
                      relief="flat", cursor="hand2", command=_on_stats).pack(side="left", padx=6)
            tk.Button(tabs_frame, text="Matches", bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_small,
                      relief="flat", cursor="hand2", command=_on_matches).pack(side="left", padx=6)
            tk.Button(tabs_frame, text="Ranked", bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_small,
                      relief="flat", cursor="hand2", command=_on_ranked).pack(side="left", padx=6)

            # Preload overview
            _on_overview()

        flags = p.get("anticheat_flags", [])
        if flags:
            flags_panel = tk.Frame(content_frame, bg=app.BG_PANEL)
            flags_panel.pack(padx=30, pady=(6, 8), fill="x")
            title_text = "🚨 Suspicious profile flags" if lang == "en" else "🚨 Drapeaux anti-triche"
            tk.Label(flags_panel, text=title_text,
                     bg=app.BG_PANEL, fg=app.GOLD, font=app.f_small).pack(anchor="w", padx=10, pady=(8, 4))
            for flag in flags[-5:]:
                reason = flag.get("reason", "Unknown reason")
                stamp = flag.get("timestamp", "")
                label_text = f"• {reason}"
                if stamp:
                    label_text += f"  ({stamp})"
                tk.Label(flags_panel, text=label_text,
                         bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small, anchor="w").pack(fill="x", padx=14, pady=1)

        tk.Label(content_frame, text="",
                 bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack(pady=(0, 8), anchor="center")
        
        scores = p.get("scores", [])
        games  = p.get("games_played", 0)
        wins   = [s for s in scores if s.get("won")]
        win_pct   = int(len(wins) / max(games, 1) * 100)
        avg_score = int(p.get("total_subs", 0) / max(games, 1))

        # XP & level
        total_xp         = p.get("total_xp", 0)
        plvl, xp_in, xp_need = player_level_from_xp(total_xp)
        title            = player_title(plvl, lang)

        xp_panel = tk.Frame(content_frame, bg=app.BG_PANEL)
        xp_panel.pack(fill="x", padx=30, pady=(4, 0))
        tk.Label(xp_panel,
                 text=f"{'Level' if lang=='en' else 'Niveau'} {plvl}  ✦  {title}",
                 bg=app.BG_PANEL, fg=app.GOLD, font=app.f_title).pack(pady=(8, 2), anchor="center")
        tk.Label(xp_panel,
                 text=f"{total_xp:,} XP  ·  {xp_in} / {xp_need} XP {'to next level' if lang=='en' else 'pour le prochain niveau'}",
                 bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(anchor="center")
        bar_outer = tk.Frame(xp_panel, bg=app.BG_MID, height=10)
        bar_outer.pack(fill="x", padx=10, pady=(4, 8))
        bar_outer.update_idletasks()
        bw   = bar_outer.winfo_width() or 300
        fill = max(4, int(bw * xp_in / max(xp_need, 1)))
        tk.Frame(bar_outer, bg=app.GOLD, width=fill, height=10).place(x=0, y=0)

        # Core stats
        stats_frame = tk.Frame(content_frame, bg=app.BG_PANEL)
        stats_frame.pack(pady=6, padx=30, fill="x")
        rows = [
            (app.s("stats_games"),   str(games)),
            (app.s("stats_subs"),    str(p.get("total_subs", 0))),
            (app.s("stats_best"),    f"{p.get('best_game', 0)} subs"),
            (app.s("stats_correct"), str(p.get("correct_answers", 0))),
            ("🏆 " + ("Win rate" if lang=="en" else "Taux de victoire"),  f"{win_pct}%"),
            ("📊 " + ("Avg score" if lang=="en" else "Score moyen"),      f"{avg_score} subs"),
            ("🔥 " + ("Win streak" if lang=="en" else "Série de victoires"), str(p.get("win_streak", 0))),
            ("⏱ " + ("Avg response" if lang=="en" else "Temps moyen"),    f"{p.get('avg_response_time', 0):.1f}s"),
        ]
        for i, (label, val) in enumerate(rows):
            row_bg = app.BG_MID if i % 2 == 0 else app.BG_PANEL
            row = tk.Frame(stats_frame, bg=row_bg)
            row.pack(fill="x", padx=2, pady=1)
            tk.Label(row, text=label, bg=row_bg, fg=app.SILVER,
                     font=app.f_small, anchor="w", padx=10, pady=4).pack(side="left")
            tk.Label(row, text=val, bg=row_bg, fg=app.GOLD,
                     font=app.f_prize_hl, anchor="e", padx=10).pack(side="right")

        # Per-level success rate bar chart
        level_stats = p.get("level_stats", {})
        if level_stats:
            tk.Label(content_frame, text="— " + ("Success rate per level" if lang=="en"
                     else "Taux de réussite par niveau") + " —",
                     bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack(pady=(6, 2), anchor="center")
            bar_frame = tk.Frame(content_frame, bg=app.BG_PANEL)
            bar_frame.pack(fill="x", padx=30, pady=(0, 6))
            for lvl in range(1, 16):
                st  = level_stats.get(str(lvl), {})
                tot = st.get("total", 0)
                cor = st.get("correct", 0)
                pct = int(cor / tot * 100) if tot else 0
                col = tk.Frame(bar_frame, bg=app.BG_PANEL)
                col.pack(side="left", expand=True)
                bar_h = max(2, int(pct / 100 * 40))
                tk.Frame(col, bg=app.BG_PANEL, height=40 - bar_h).pack()
                bc = app.BTN_CORRECT if pct >= 60 else (app.BTN_SELECTED if pct >= 30 else app.BTN_WRONG)
                tk.Frame(col, bg=bc, width=12, height=bar_h).pack()
                tk.Label(col, text=str(lvl), bg=app.BG_PANEL,
                         fg=app.SILVER, font=app.f_small).pack()

        # Per-mode stats
        mode_scores = {}
        for sc in scores:
            m = sc.get("mode", "normal")
            if m not in mode_scores:
                mode_scores[m] = {"played": 0, "won": 0, "best": 0}
            mode_scores[m]["played"] += 1
            if sc.get("won"):
                mode_scores[m]["won"] += 1
            mode_scores[m]["best"] = max(mode_scores[m]["best"], sc["subs"])

        if mode_scores:
            tk.Label(content_frame, text="— " + ("Stats per mode" if lang=="en"
                     else "Stats par mode") + " —",
                     bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack(pady=(8, 2), anchor="center")
            mode_frame = tk.Frame(content_frame, bg=app.BG_DARK)
            mode_frame.pack(fill="x", padx=30, pady=(0, 6))
            for mid, info in GAME_MODES.items():
                ms = mode_scores.get(mid)
                if not ms:
                    continue
                lbl   = info.get(f"label_{lang}", info["label_en"])
                color = info["color"]
                wr    = int(ms["won"] / max(ms["played"], 1) * 100)
                col   = tk.Frame(mode_frame, bg=app.BG_PANEL)
                col.pack(side="left", expand=True, padx=3, pady=2)
                tk.Label(col, text=lbl,                   bg=app.BG_PANEL, fg=color,  font=app.f_prize_hl).pack()
                tk.Label(col, text=f"{ms['played']} played" if lang=="en" else f"{ms['played']} parties",
                         bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack()
                tk.Label(col, text=f"{wr}% wins" if lang=="en" else f"{wr}% victoires",
                         bg=app.BG_PANEL, fg=app.WHITE,  font=app.f_small).pack()
                tk.Label(col, text=f"Best: {ms['best']} subs",
                         bg=app.BG_PANEL, fg=app.GOLD,   font=app.f_small).pack()

        # Last 10 games
        recent = list(reversed(scores))[:10]
        if recent:
            tk.Label(content_frame, text="— " + ("Last 10 games" if lang=="en"
                     else "10 dernières parties") + " —",
                     bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack(pady=(8, 2), anchor="center")
            hist_frame = tk.Frame(content_frame, bg=app.BG_PANEL)
            hist_frame.pack(fill="x", padx=30, pady=(0, 6))
            for col_i, (hdr, w) in enumerate(zip(
                ["#", "Mode", "Level", "Subs", ""],
                [3,    10,     5,       6,      3]
            )):
                tk.Label(hist_frame, text=hdr, bg=app.BG_PANEL, fg=app.GOLD,
                         font=app.f_small, width=w, anchor="w"
                         ).grid(row=0, column=col_i, padx=4, pady=2, sticky="w")
            for i, sc in enumerate(recent):
                row_bg   = app.BG_MID if i % 2 == 0 else app.BG_PANEL
                mid      = sc.get("mode", "normal")
                minfo    = GAME_MODES.get(mid, GAME_MODES["normal"])
                mlbl     = minfo.get(f"label_{lang}", minfo["label_en"])
                mcolor   = minfo["color"]
                icon     = "🏆" if sc.get("won") else ("🚶" if sc.get("walked") else "❌")
                vals     = [len(recent)-i, mlbl, sc["level"], sc["subs"], icon]
                colors   = [app.SILVER, mcolor, app.WHITE, app.GOLD, app.WHITE]
                for col_i, (val, color, w) in enumerate(zip(vals, colors, [3,10,5,6,3])):
                    tk.Label(hist_frame, text=str(val), bg=row_bg,
                             fg=color, font=app.f_small, width=w, anchor="w"
                             ).grid(row=i+1, column=col_i, padx=4, pady=1, sticky="w")

    # ── Footer buttons (not scrollable) ────────────────────────────
    footer = tk.Frame(f, bg=app.BG_DARK)
    footer.pack(fill="x", padx=0, pady=8)
    
    btn_frame = tk.Frame(footer, bg=app.BG_DARK)
    btn_frame.pack()
    new_profile_btn = tk.Button(btn_frame, text=app.s("new_profile"),
              bg=app.LIFELINE_ON, fg=app.LIFELINE_TEXT_ON, font=app.f_small,
              relief="flat", cursor="hand2", padx=10, pady=6,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.LIFELINE_ON, highlightthickness=0,
              command=lambda: _new_profile(app))
    new_profile_btn.pack(side="left", padx=4)
    
    def _new_enter(e=None):
        new_profile_btn.config(bg=app.BTN_HOVER, highlightbackground=app.MENU_BTN_ACT, highlightthickness=2)
    def _new_leave(e=None):
        new_profile_btn.config(bg=app.LIFELINE_ON, highlightbackground=app.LIFELINE_ON, highlightthickness=0)
    new_profile_btn.bind("<Enter>", _new_enter)
    new_profile_btn.bind("<Leave>", _new_leave)
    if active:
        tk.Button(btn_frame, text="📤  Export",
                  bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_small,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=lambda: _export(app, active)).pack(side="left", padx=4)
        tk.Button(btn_frame, text=app.s("delete_profile"),
                  bg=app.BTN_WRONG, fg=app.WHITE, font=app.f_small,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=lambda: _delete(app, active)).pack(side="left", padx=4)

    tk.Button(footer, text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=6,
              command=app.show_menu).pack(pady=8)


# ── Helpers ───────────────────────────────────────────────────────

def _load_profile_avatar(app, profile_name: str, size: int = 32):
    """Load and resize profile avatar image, return PhotoImage or None."""
    try:
        from PIL import Image, ImageTk
        from utils import get_avatar_path
        
        profile = app.data["profiles"].get(profile_name, {})
        avatar_filename = profile.get("avatar")
        if not avatar_filename:
            return None
        
        avatar_path = get_avatar_path(avatar_filename)
        if not os.path.exists(avatar_path):
            return None
        
        img = Image.open(avatar_path).convert("RGBA")
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def _select(app, name):
    app.data["active_profile"] = name
    save_data(app.data, silent=True)
    build(app)


def _manual_flag_profile(app, profile_name: str):
    lang = app._lang.get("code", "en")
    prompt_title = "Flag profile" if lang == "en" else "Signaler le profil"
    prompt_text = "Enter a reason for this flag:" if lang == "en" else "Entrez une raison pour ce signalement :"
    reason = simpledialog.askstring(prompt_title, prompt_text, parent=app)
    if not reason:
        return

    profile = app.data.get("profiles", {}).get(profile_name)
    if not profile:
        messagebox.showerror("", "Profile not found.", parent=app)
        return

    flags = profile.setdefault("anticheat_flags", [])
    flags.append({
        "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "manual": True,
        "reason": reason.strip(),
    })
    save_data(app.data, silent=True)
    messagebox.showinfo("", "Profile flagged successfully." if lang == "en" else "Profil signalé avec succès.", parent=app)
    build(app)


def _new_profile(app):
    lang = app._lang.get("code", "en")
    name = simpledialog.askstring(
        app.s("profile_title"), app.s("enter_name"), parent=app
    )
    if name is None:
        return
    name = name.strip()
    if not name:
        messagebox.showerror("", app.s("name_empty"), parent=app)
        return
    if name in app.data["profiles"]:
        messagebox.showerror("", app.s("name_taken"), parent=app)
        return
    app.data["profiles"][name] = {
        "games_played": 0, "total_subs": 0, "best_game": 0,
        "correct_answers": 0, "achievements": [], "scores": [],
        "win_streak": 0, "total_xp": 0, "player_level": 1,
        "avatar": None,
        "profile_type": "offline",
    }
    app.data["active_profile"] = name
    from utils import save_data
    save_data(app.data, silent=True)
    build(app)

def _delete(app, name):
    if not messagebox.askyesno("", app.s("confirm_delete", name=name), parent=app):
        return
    del app.data["profiles"][name]
    remaining = list(app.data["profiles"].keys())
    app.data["active_profile"] = remaining[0] if remaining else None
    from utils import save_data
    save_data(app.data, silent=True)
    build(app)

def _export(app, name):
    p      = app.data["profiles"].get(name)
    scores = p.get("scores", [])
    wins   = [s for s in scores if s.get("won")]
    games  = p.get("games_played", 0)
    export = {
        "profile":      name,
        "exported_at":  datetime.datetime.now().isoformat(timespec="seconds"),
        "game_version": "2.4",
        "stats": {
            "games_played":    games,
            "total_subs":      p.get("total_subs", 0),
            "best_game_subs":  p.get("best_game", 0),
            "correct_answers": p.get("correct_answers", 0),
            "wins":            len(wins),
            "win_rate_pct":    round(len(wins) / max(games, 1) * 100, 1),
            "avg_score_subs":  round(p.get("total_subs", 0) / max(games, 1), 1),
            "win_streak":      p.get("win_streak", 0),
            "total_xp":        p.get("total_xp", 0),
            "player_level":    p.get("player_level", 1),
        },
        "top_scores":   scores[:10],
        "achievements": p.get("achievements", []),
    }
    path = filedialog.asksaveasfilename(
        parent=app, title="Export profile",
        defaultextension=".json",
        initialfile=f"subladdder_{name}.json",
        filetypes=[("JSON file", "*.json"), ("All files", "*.*")],
    )
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f_out:
            json.dump(export, f_out, indent=2, ensure_ascii=False)
        messagebox.showinfo("", f"✅  Profile exported to:\n{path}", parent=app)
    except OSError as e:
        messagebox.showerror("", f"Export failed:\n{e}", parent=app)


def _change_avatar(app, profile_name):
    """Open file dialog to select and set avatar for profile."""
    from utils import save_avatar, save_data
    
    file_path = filedialog.askopenfilename(
        parent=app,
        title="Select avatar image",
        filetypes=[("PNG/JPG Images", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
    )
    
    if not file_path:
        return
    
    avatar_filename = save_avatar(file_path, profile_name)
    if not avatar_filename:
        messagebox.showerror("", "Invalid image file. Please use PNG or JPG (max 2MB).", parent=app)
        return
    
    old_avatar = app.data["profiles"][profile_name].get("avatar")
    if old_avatar and old_avatar != avatar_filename:
        from utils import delete_avatar
        delete_avatar(old_avatar)
    
    app.data["profiles"][profile_name]["avatar"] = avatar_filename
    save_data(app.data, silent=True)
    messagebox.showinfo("", "✅  Avatar updated!", parent=app)
    build(app)


def _trigger_profile_sync(app, profile_name: str, status_label: tk.Label, force: bool = False):
    """
    Trigger profile data sync from server in background thread.
    Updates status_label with sync status (⏳ syncing, ✓ synced, ✗ error).
    Graceful error handling: uses cached data if server unavailable.
    """
    from game.auth.client import APIClient
    from game.auth.cache import ProfileCache
    from utils import save_data
    import threading
    import traceback
    
    profile = app.data["profiles"].get(profile_name, {})
    ptype = profile.get("profile_type", "offline")
    
    if ptype != "online":
        return  # Only sync online profiles
    
    user_id = profile.get("user_id")
    token = None
    
    # Get token from auth data
    if app.data.get("auth", {}).get("tokens", {}).get(profile_name):
        token = app.data["auth"]["tokens"][profile_name]
    
    if not token:
        status_label.config(text="✗ No auth")
        if not force:
            return
    
    if not user_id:
        status_label.config(text="✗ No user ID")
        return
    
    # Initialize cache if not exists
    if not hasattr(app, '_profile_cache'):
        app._profile_cache = ProfileCache(cache_duration=300)  # 5 minutes
    
    cache = app._profile_cache
    
    # Check if already syncing (prevent concurrent requests)
    if cache.is_syncing(user_id) and not force:
        return
    
    # Check if cache is valid (not expired)
    if not force and cache.get(user_id):
        status_label.config(text="✓")
        return
    
    def sync_thread():
        """Background thread for syncing profile with error handling."""
        error_msg = None
        try:
            cache.start_sync(user_id)
            status_label.config(text="⏳")
            status_label.update()
            
            # Create API client and fetch profile
            api_client = APIClient()
            result = api_client.get_profile(token)
            
            # Check for API errors
            if result.get("error"):
                error_msg = result["error"]
                # Try to use cached data
                cached = cache.get_stale(user_id)
                if cached:
                    # Show error but profile still loaded from cache
                    status_label.config(text="✗", fg=app.BG_PANEL if hasattr(app, 'BG_PANEL') else "#cc4444")
                else:
                    # No cache, can't display profile
                    status_label.config(text="✗")
                    raise Exception(f"Sync failed: {error_msg}")
                return
            
            # Sync successful: update local profile with online data
            profile_data = result.get("profile", {})
            if not profile_data:
                raise Exception("Empty profile data from server")
            
            # Update local profile with server data
            app.data["profiles"][profile_name].update({
                "games_played": profile_data.get("games_played", 0),
                "total_xp": profile_data.get("level", 0) * 1000,  # Rough conversion
                "level": profile_data.get("level", 0),
                "total_score": profile_data.get("total_score", 0),
                "server_username": profile_data.get("game_name"),
                "last_synced": __import__('time').time(),
            })
            
            # Cache the profile data
            cache.set(user_id, profile_data)
            save_data(app.data, silent=True)
            
            # Update UI: show success
            status_label.config(text="✓", fg="#44cc44" if hasattr(app, 'BG_PANEL') else "#ffffff")
            
        except Exception as e:
            error_msg = str(e)
            # Fallback to cached data if available
            cached = cache.get_stale(user_id)
            if cached:
                # Profile data exists in cache, show warning
                status_label.config(text="✗", fg="#cc8844" if hasattr(app, 'BG_PANEL') else "#cc8844")
            else:
                # No cache: show error, profile won't display
                status_label.config(text="✗", fg="#cc4444" if hasattr(app, 'BG_PANEL') else "#cc4444")
                if app.data.get("debug"):
                    print(f"❌ Profile sync error: {error_msg}")
                    traceback.print_exc()
        finally:
            try:
                cache.end_sync(user_id)
                status_label.update()
            except:
                pass
    
    # Start sync in background thread (daemon, non-blocking)
    thread = threading.Thread(target=sync_thread, daemon=True)
    thread.start()
