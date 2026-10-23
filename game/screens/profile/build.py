"""
game/screens/profile/build.py — Écran de profil utilisateur.
Affiche un profil complet avec résumé, stats, historique et onglets online.
"""

import tkinter as tk
from tkinter import messagebox

from ...constants import (
    BG_DARK, BG_PANEL, BG_MID, GOLD, SILVER, WHITE,
    BTN_DEFAULT, BTN_CORRECT, BTN_SELECTED, BTN_WRONG,
    LIFELINE_ON, LIFELINE_TEXT_ON, MENU_BTN_BG,
    GAME_MODES, player_level_from_xp, player_title,
)
from ...ui_helpers import create_scrollable_frame

try:
    from ...auth.client import APIClient
except Exception:
    from ...auth.client import APIClient

from .actions.avatar import change_avatar
from .actions.export import export_profile
from .actions.profiles import delete_profile, select_profile
from .submenus.create_offline import show_create_offline
from .ui.avatar import load_profile_avatar
from .ui.profile_list import build_profile_list
from .ui.sync_status import build_sync_section
from .ui.tabs.achievements_tab import build_achievements_tab
from .ui.tabs.matches_tab import build_matches_tab
from .ui.tabs.overview_tab import build_overview_tab
from .ui.tabs.ranked_tab import build_ranked_tab
from .ui.tabs.ranking_tab import build_ranking_tab
from .ui.tabs.stats_tab import build_stats_tab
from .ui.tabs.top_players_tab import build_top_players_tab


def build(app):
    """Construire l'écran de profil avec les sections manquantes de l'ancien profil."""
    app._clear()
    f = app._container
    target_profile = getattr(app, "_profile_view_target", None)
    app._profile_view_target = None

    header = tk.Frame(f, bg=app.BG_DARK)
    header.pack(fill="x", padx=0, pady=0)
    tk.Label(header, text=app.s("profile_title") if hasattr(app, "s") else "Profile",
             bg=app.BG_DARK, fg=app.GOLD if hasattr(app, "GOLD") else GOLD,
             font=app.f_title if hasattr(app, "f_title") else ("Arial", 24, "bold")).pack(pady=(24, 6))

    _, content_frame = create_scrollable_frame(f, app.BG_DARK)
    profiles = app.data.get("profiles", {})
    active_name = app.data.get("active_profile")
    viewed_name = target_profile if target_profile in profiles else active_name

    if len(profiles) > 1:
        build_profile_list(content_frame, app, on_select=lambda name: select_profile(app, name))
    elif not profiles:
        empty_frame = tk.Frame(content_frame, bg=app.BG_DARK)
        empty_frame.pack(pady=24, fill="x")
        tk.Label(empty_frame, text="No profiles yet",
                 bg=app.BG_DARK, fg=SILVER, font=app.f_small).pack()

    if viewed_name and viewed_name in profiles:
        profile = profiles[viewed_name]
        _build_profile_details(content_frame, app, viewed_name, profile)
    elif viewed_name:
        _build_remote_profile_details(content_frame, app, viewed_name)
    else:
        _build_empty_state(content_frame, app)

    profile_actions_name = active_name if viewed_name == active_name else None

    footer = tk.Frame(f, bg=app.BG_DARK)
    footer.pack(fill="x", padx=0, pady=8)
    btn_frame = tk.Frame(footer, bg=app.BG_DARK)
    btn_frame.pack()

    tk.Button(btn_frame, text="➕  New profile",
              bg=LIFELINE_ON, fg=LIFELINE_TEXT_ON, font=app.f_small,
              relief="flat", cursor="hand2", padx=10, pady=6,
              command=lambda: show_create_offline(app)).pack(side="left", padx=4)

    if profile_actions_name:
        tk.Button(btn_frame, text="🖼️  Change avatar",
                  bg=BTN_DEFAULT, fg=SILVER, font=app.f_small,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=lambda: change_avatar(app, profile_actions_name)).pack(side="left", padx=4)

    tk.Button(footer, text=app.s("back_menu") if hasattr(app, "s") else "Back",
              bg=MENU_BTN_BG, fg=SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=6,
              command=lambda: _go_back(app)).pack(pady=8)


def _build_profile_details(content_frame, app, profile_name, profile):
    lang = app._lang.get("code", "en") if hasattr(app, "_lang") else "en"
    active_name = app.data.get("active_profile")
    is_self_view = profile_name == active_name
    summary = compute_profile_summary(profile, lang)
    ptype = profile.get("profile_type", "offline")
    dashboard = tk.Frame(content_frame, bg=app.BG_DARK)
    dashboard.pack(fill="x", padx=24, pady=(8, 8))

    _build_profile_nav(dashboard, app, lang)
    _build_profile_banner(dashboard, app, profile_name, profile, summary, lang)
    _build_quick_stats_cards(dashboard, app, profile, lang)
    _build_profile_tabs(dashboard, app, profile_name, profile, is_self_view, ptype, lang)

    build_sync_section(content_frame, app, profile_name, profile)
    _build_flags_panel(content_frame, app, profile.get("anticheat_flags", []), lang)


def _build_remote_profile_details(content_frame, app, profile_name):
    lang = app._lang.get("code", "en") if hasattr(app, "_lang") else "en"

    remote_frame = tk.Frame(content_frame, bg=app.BG_DARK)
    remote_frame.pack(pady=(16, 0), fill="x", anchor="center")

    tk.Label(
        remote_frame,
        text=profile_name,
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_title,
    ).pack(pady=(0, 4), anchor="center")
    tk.Label(
        remote_frame,
        text=("Remote profile view" if lang == "en" else "Consultation du profil distant"),
        bg=app.BG_DARK,
        fg=SILVER,
        font=app.f_small,
    ).pack(anchor="center")
    tk.Label(
        remote_frame,
        text=("This profile is not stored locally, so data is loaded directly from the server." if lang == "en"
              else "Ce profil n'est pas stocké localement, les données sont chargées depuis le serveur."),
        bg=app.BG_DARK,
        fg=SILVER,
        font=app.f_small,
        wraplength=520,
        justify="center",
    ).pack(pady=(8, 10), anchor="center")

    _build_profile_tabs(content_frame, app, profile_name, {}, False, "online", lang)


def _open_online_upgrade(app, profile_name: str):
    """Open the link-account submenu to upgrade an offline profile to online."""
    from .submenus.link_account import show_link_account
    show_link_account(app)


def _build_empty_state(content_frame, app):
    tk.Label(content_frame, text="Select or create a profile to see its stats.",
             bg=app.BG_DARK, fg=SILVER, font=app.f_small).pack(pady=16)


def _build_summary_panel(content_frame, app, summary, lang):
    panel = tk.Frame(content_frame, bg=BG_PANEL)
    panel.pack(fill="x", padx=30, pady=(4, 8))

    tk.Label(panel, text=f"Level {summary['player_level']}  ✦  {summary['title']}",
             bg=BG_PANEL, fg=GOLD, font=app.f_title).pack(pady=(8, 2), anchor="center")
    tk.Label(panel, text=f"{summary['total_xp']:,} XP  ·  {summary['xp_in']} / {summary['xp_need']} XP {'to next level' if lang == 'en' else 'pour le prochain niveau'}",
             bg=BG_PANEL, fg=SILVER, font=app.f_small).pack(anchor="center")

    bar_outer = tk.Frame(panel, bg=BG_MID, height=10)
    bar_outer.pack(fill="x", padx=10, pady=(4, 8))
    bar_outer.update_idletasks()
    bw = bar_outer.winfo_width() or 300
    fill = max(4, int(bw * summary['xp_in'] / max(summary['xp_need'], 1)))
    tk.Frame(bar_outer, bg=GOLD, width=fill, height=10).place(x=0, y=0)

    rows = [
        ("Games", str(summary["games"])),
        ("Subs", str(summary["total_subs"])),
        ("Best", f"{summary['best_game']} subs"),
        ("Correct", str(summary["correct_answers"])),
        ("Win rate", f"{summary['win_pct']}%"),
        ("Avg score", f"{summary['avg_score']} subs"),
        ("Win streak", str(summary["win_streak"])),
    ]
    for idx, (label, value) in enumerate(rows):
        row_bg = BG_MID if idx % 2 == 0 else BG_PANEL
        row = tk.Frame(panel, bg=row_bg)
        row.pack(fill="x", padx=2, pady=1)
        tk.Label(row, text=label, bg=row_bg, fg=SILVER, font=app.f_small, anchor="w", padx=10, pady=4).pack(side="left")
        tk.Label(row, text=value, bg=row_bg, fg=GOLD, font=app.f_small, anchor="e", padx=10).pack(side="right")


def _build_level_stats(content_frame, app, level_stats, lang):
    if not level_stats:
        return
    tk.Label(content_frame, text="— " + ("Success rate per level" if lang == "en" else "Taux de réussite par niveau") + " —",
             bg=app.BG_DARK, fg=SILVER, font=app.f_small).pack(pady=(6, 2), anchor="center")
    bar_frame = tk.Frame(content_frame, bg=BG_PANEL)
    bar_frame.pack(fill="x", padx=30, pady=(0, 6))
    for lvl in range(1, 16):
        st = level_stats.get(str(lvl), {})
        tot = st.get("total", 0)
        cor = st.get("correct", 0)
        pct = int(cor / tot * 100) if tot else 0
        col = tk.Frame(bar_frame, bg=BG_PANEL)
        col.pack(side="left", expand=True)
        bar_h = max(2, int(pct / 100 * 40))
        tk.Frame(col, bg=BG_PANEL, height=40 - bar_h).pack()
        color = BTN_CORRECT if pct >= 60 else (BTN_SELECTED if pct >= 30 else BTN_WRONG)
        tk.Frame(col, bg=color, width=12, height=bar_h).pack()
        tk.Label(col, text=str(lvl), bg=BG_PANEL, fg=SILVER, font=app.f_small).pack()


def _build_mode_stats(content_frame, app, mode_stats, lang):
    if not mode_stats:
        return
    tk.Label(content_frame, text="— " + ("Stats per mode" if lang == "en" else "Stats par mode") + " —",
             bg=app.BG_DARK, fg=SILVER, font=app.f_small).pack(pady=(8, 2), anchor="center")
    mode_frame = tk.Frame(content_frame, bg=app.BG_DARK)
    mode_frame.pack(fill="x", padx=30, pady=(0, 6))
    for mid, info in GAME_MODES.items():
        ms = mode_stats.get(mid)
        if not ms:
            continue
        lbl = info.get(f"label_{lang}", info["label_en"])
        color = info["color"]
        col = tk.Frame(mode_frame, bg=BG_PANEL)
        col.pack(side="left", expand=True, padx=3, pady=2)
        tk.Label(col, text=lbl, bg=BG_PANEL, fg=color, font=app.f_small).pack()
        tk.Label(col, text=f"{ms['played']} played" if lang == "en" else f"{ms['played']} parties",
                 bg=BG_PANEL, fg=SILVER, font=app.f_small).pack()
        tk.Label(col, text=f"{ms['won']} won" if lang == "en" else f"{ms['won']} victoires",
                 bg=BG_PANEL, fg=WHITE, font=app.f_small).pack()
        tk.Label(col, text=f"Best: {ms['best']} subs",
                 bg=BG_PANEL, fg=GOLD, font=app.f_small).pack()


def _build_recent_games(content_frame, app, recent_scores, lang):
    if not recent_scores:
        return
    tk.Label(content_frame, text="— " + ("Last 10 games" if lang == "en" else "10 dernières parties") + " —",
             bg=app.BG_DARK, fg=SILVER, font=app.f_small).pack(pady=(8, 2), anchor="center")
    hist_frame = tk.Frame(content_frame, bg=BG_PANEL)
    hist_frame.pack(fill="x", padx=30, pady=(0, 6))
    for col_i, (hdr, w) in enumerate(zip(["#", "Mode", "Level", "Subs", ""], [3, 10, 5, 6, 3])):
        tk.Label(hist_frame, text=hdr, bg=BG_PANEL, fg=GOLD, font=app.f_small, width=w, anchor="w").grid(row=0, column=col_i, padx=4, pady=2, sticky="w")
    for i, sc in enumerate(recent_scores):
        row_bg = BG_MID if i % 2 == 0 else BG_PANEL
        mid = sc.get("mode", "normal")
        minfo = GAME_MODES.get(mid, GAME_MODES["normal"])
        mlbl = minfo.get(f"label_{lang}", minfo["label_en"])
        mcolor = minfo["color"]
        icon = "🏆" if sc.get("won") else ("🚶" if sc.get("walked") else "❌")
        vals = [len(recent_scores) - i, mlbl, sc.get("level", "?"), sc.get("subs", 0), icon]
        colors = [SILVER, mcolor, WHITE, GOLD, WHITE]
        for col_i, (val, color, w) in enumerate(zip(vals, colors, [3, 10, 5, 6, 3])):
            tk.Label(hist_frame, text=str(val), bg=row_bg, fg=color, font=app.f_small, width=w, anchor="w").grid(row=i + 1, column=col_i, padx=4, pady=1, sticky="w")


def _build_flags_panel(content_frame, app, flags, lang):
    if not flags:
        return
    panel = tk.Frame(content_frame, bg=BG_PANEL)
    panel.pack(fill="x", padx=30, pady=(6, 8))
    tk.Label(panel, text="🚨 Suspicious profile flags" if lang == "en" else "🚨 Drapeaux anti-triche",
             bg=BG_PANEL, fg=GOLD, font=app.f_small).pack(anchor="w", padx=10, pady=(8, 4))
    for flag in flags[-5:]:
        reason = flag.get("reason", "Unknown reason")
        stamp = flag.get("timestamp", "")
        label_text = f"• {reason}"
        if stamp:
            label_text += f"  ({stamp})"
        tk.Label(panel, text=label_text, bg=BG_PANEL, fg=SILVER, font=app.f_small, anchor="w").pack(fill="x", padx=14, pady=1)


def _build_profile_nav(parent, app, lang):
    nav = tk.Frame(parent, bg=app.BG_DARK)
    nav.pack(fill="x", pady=(2, 8))

    back_label = "Retour au menu" if lang == "fr" else "Back to menu"
    tk.Button(
        nav,
        text=f"←  {back_label}",
        bg="#f6e08f",
        fg="#1e1f28",
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=8,
        command=lambda: _go_back(app),
    ).pack(anchor="w")


def _build_profile_banner(parent, app, profile_name, profile, summary, lang):
    banner = tk.Frame(parent, bg="#f3b7bd", bd=2, relief="solid")
    banner.pack(fill="x", pady=(8, 12))

    left = tk.Frame(banner, bg="#f3b7bd")
    left.pack(side="left", fill="both", expand=True, padx=14, pady=12)
    tk.Label(left, text=profile_name, bg="#f3b7bd", fg="#1e1f28", font=app.f_title).pack(anchor="w", pady=(4, 8))

    avatar_holder = tk.Frame(left, bg="#f3b7bd")
    avatar_holder.pack(anchor="w")
    avatar_img = load_profile_avatar(app, profile_name, size=72)
    if avatar_img:
        avatar_lbl = tk.Label(avatar_holder, image=avatar_img, bg="#f3b7bd")
        avatar_lbl.pack(side="left", padx=(0, 8))
        avatar_lbl._img_ref = avatar_img
    else:
        tk.Label(avatar_holder, text="👤", bg="#f3b7bd", fg="#24304a", font=("Arial", 26)).pack(side="left", padx=(0, 8))

    status_txt = "Profil en ligne" if profile.get("profile_type") == "online" and lang == "fr" else (
        "Profil hors-ligne" if lang == "fr" else ("Online profile" if profile.get("profile_type") == "online" else "Offline profile")
    )
    tk.Label(avatar_holder, text=status_txt, bg="#f3b7bd", fg="#313d59", font=app.f_small).pack(side="left", pady=4)

    right = tk.Frame(banner, bg="#f3b7bd")
    right.pack(side="right", fill="y", padx=14, pady=12)
    level_txt = f"Niveau {summary['player_level']}" if lang == "fr" else f"Level {summary['player_level']}"
    tk.Label(right, text=level_txt, bg="#f3b7bd", fg="#1e1f28", font=app.f_label).pack(anchor="e")

    bar_outer = tk.Frame(right, bg="#7bb3da", bd=2, relief="solid")
    bar_outer.pack(anchor="e", pady=(8, 0))
    xp_label = f"{summary['xp_in']} / {summary['xp_need']}"
    tk.Label(bar_outer, text=xp_label, bg="#7bb3da", fg="#1e1f28", font=app.f_label, padx=36, pady=4).pack()


def _build_quick_stats_cards(parent, app, profile, lang):
    cards = tk.Frame(parent, bg=app.BG_DARK)
    cards.pack(fill="x", pady=(4, 12))

    wins_total = sum(1 for sc in profile.get("scores", []) if sc.get("won"))
    ranked_wins = int(profile.get("ranked_wins", 0) or 0)
    if ranked_wins <= 0:
        ranked_wins = sum(1 for sc in profile.get("scores", []) if sc.get("won") and sc.get("mode") == "ranked")

    multiplayer_wins = int(profile.get("multiplayer_wins", 0) or 0)
    if multiplayer_wins <= 0:
        mp_modes = {"multiplayer", "p2p", "multi", "online_multiplayer", "ranked"}
        multiplayer_wins = sum(1 for sc in profile.get("scores", []) if sc.get("won") and sc.get("mode") in mp_modes)

    solo_wins = max(0, wins_total - multiplayer_wins)

    rank_display = profile.get("ranked_rank", {}).get("display", "Unranked")
    rank_elo = profile.get("ranked_rank", {}).get("elo")
    if rank_elo is None:
        rank_elo = profile.get("elo")

    card_data = [
        {
            "title": "Soloplayer",
            "value": f"{solo_wins} victoires" if lang == "fr" else f"{solo_wins} wins",
            "badge": _wins_badge(solo_wins, lang),
        },
        {
            "title": "Multiplayer",
            "value": f"{multiplayer_wins} victoires" if lang == "fr" else f"{multiplayer_wins} wins",
            "badge": _wins_badge(multiplayer_wins, lang),
        },
        {
            "title": "Ranked",
            "value": f"{rank_display} - {rank_elo} MMR" if rank_elo else rank_display,
            "badge": _rank_badge(rank_display),
        },
    ]

    for idx, item in enumerate(card_data):
        card = tk.Frame(cards, bg="#a7ecb6", bd=2, relief="solid")
        card.grid(row=0, column=idx, padx=12, ipadx=8, ipady=8, sticky="nsew")
        cards.grid_columnconfigure(idx, weight=1)

        tk.Label(card, text=item["title"], bg="#a7ecb6", fg="#1f2738", font=app.f_label).pack(anchor="center", pady=(2, 8))

        badge = tk.Frame(card, bg=item["badge"][1], bd=2, relief="solid")
        badge.pack(anchor="center", pady=(0, 10), ipadx=16, ipady=8)
        tk.Label(badge, text=item["badge"][0], bg=item["badge"][1], fg="#1e1f28", font=app.f_small).pack()

        tk.Label(card, text=item["value"], bg="#a7ecb6", fg="#1f2738", font=app.f_label).pack(anchor="center", pady=(4, 2))


def _wins_badge(wins, lang):
    if wins >= 600:
        return ("Diamant", "#8ed6ff") if lang == "fr" else ("Diamond", "#8ed6ff")
    if wins >= 300:
        return ("Rubis", "#f59f9f") if lang == "fr" else ("Ruby", "#f59f9f")
    if wins >= 150:
        return ("Emeraude", "#7dd9a0") if lang == "fr" else ("Emerald", "#7dd9a0")
    if wins >= 60:
        return ("Or", "#f3cf7d") if lang == "fr" else ("Gold", "#f3cf7d")
    return ("Bronze", "#d8a074")


def _rank_badge(rank_display):
    rank_name = str(rank_display or "").lower()
    if "champion" in rank_name:
        return ("Champion", "#ffd06b")
    if "diamond" in rank_name or "diamant" in rank_name:
        return ("Diamond", "#8ed6ff")
    if "ruby" in rank_name or "rubis" in rank_name:
        return ("Ruby", "#f59f9f")
    if "emerald" in rank_name or "emeraude" in rank_name:
        return ("Emerald", "#7dd9a0")
    if "platinum" in rank_name:
        return ("Platinum", "#b8e4dd")
    if "gold" in rank_name or "or" in rank_name:
        return ("Gold", "#f3cf7d")
    if "silver" in rank_name or "argent" in rank_name:
        return ("Silver", "#c6cfdb")
    return ("Unranked", "#ef9a5c")


def _build_profile_tabs(content_frame, app, profile_name, profile, is_self_view, ptype, lang):
    tabs_frame = tk.Frame(content_frame, bg=app.BG_DARK)
    tabs_frame.pack(pady=(4, 6), fill="x")

    remote_panel = tk.Frame(content_frame, bg=BG_PANEL)
    remote_panel.pack(fill="x", pady=(0, 8))

    def _clear_remote():
        for w in remote_panel.winfo_children():
            w.destroy()

    def _select_tab(builder):
        _clear_remote()
        builder(remote_panel, app, profile_name)

    labels = {
        "stats": "Statistiques" if lang == "fr" else "Statistics",
        "ranked": "Ranked",
        "history": "Historique" if lang == "fr" else "History",
        "top": "Top Ranked" if lang == "fr" else "Top Ranked",
        "ach": "Succes" if lang == "fr" else "Achievements",
        "overview": "Apercu" if lang == "fr" else "Overview",
        "edit": "Modifier le profil" if lang == "fr" else "Edit profile",
    }

    tab_items = [
        (labels["stats"], lambda: _select_tab(build_stats_tab)),
        (labels["ranked"], lambda: _select_tab(build_ranked_tab)),
        (labels["history"], lambda: _select_tab(build_matches_tab)),
        (labels["top"], lambda: _select_tab(build_top_players_tab)),
        (labels["ach"], lambda: _select_tab(build_achievements_tab)),
        (labels["overview"], lambda: _select_tab(build_overview_tab)),
        (labels["edit"], lambda: _build_manage_tab(remote_panel, app, profile_name, profile, is_self_view, ptype, lang)),
    ]

    max_cols = 5
    for i, (label, action) in enumerate(tab_items):
        row = i // max_cols
        col = i % max_cols
        btn = tk.Button(
            tabs_frame,
            text=label,
            bg="#f6e08f",
            fg="#1e1f28",
            font=app.f_small,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=action,
        )
        btn.grid(row=row, column=col, padx=6, pady=6, sticky="ew")

    for col in range(max_cols):
        tabs_frame.grid_columnconfigure(col, weight=1)

    _select_tab(build_stats_tab)


def _build_manage_tab(remote_panel, app, profile_name, profile, is_self_view, ptype, lang):
    for w in remote_panel.winfo_children():
        w.destroy()

    title = "Modifier le profil" if lang == "fr" else "Edit profile"
    tk.Label(remote_panel, text=title, bg=BG_PANEL, fg=GOLD, font=app.f_label).pack(anchor="w", padx=12, pady=(10, 8))

    actions = tk.Frame(remote_panel, bg=BG_PANEL)
    actions.pack(fill="x", padx=12, pady=(0, 10))

    tk.Button(
        actions,
        text="Changer avatar" if lang == "fr" else "Change avatar",
        bg=BTN_DEFAULT,
        fg=SILVER,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=6,
        command=lambda: change_avatar(app, profile_name),
    ).pack(side="left", padx=4, pady=4)

    tk.Button(
        actions,
        text="Exporter" if lang == "fr" else "Export",
        bg=BTN_DEFAULT,
        fg=SILVER,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=6,
        command=lambda: export_profile(app, profile_name),
    ).pack(side="left", padx=4, pady=4)

    if ptype == "offline" and is_self_view:
        tk.Button(
            actions,
            text="Passer online" if lang == "fr" else "Go online",
            bg=BTN_DEFAULT,
            fg=SILVER,
            font=app.f_small,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=lambda: _open_online_upgrade(app, profile_name),
        ).pack(side="left", padx=4, pady=4)

    if is_self_view:
        tk.Button(
            actions,
            text="Supprimer" if lang == "fr" else "Delete",
            bg=BTN_WRONG,
            fg=WHITE,
            font=app.f_small,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=lambda: delete_profile(app, profile_name),
        ).pack(side="left", padx=4, pady=4)


def compute_profile_summary(profile, lang):
    """Calculer un résumé de profil réutilisable par l'écran et les tests."""
    scores = profile.get("scores", [])
    games = int(profile.get("games_played", 0) or len(scores) or 0)
    wins = [s for s in scores if s.get("won")]
    win_pct = round(len(wins) / max(games, 1) * 100)
    avg_score = round(profile.get("total_subs", 0) / max(games, 1))

    mode_stats = {}
    for sc in scores:
        mid = sc.get("mode", "normal")
        if mid not in mode_stats:
            mode_stats[mid] = {"played": 0, "won": 0, "best": 0}
        mode_stats[mid]["played"] += 1
        if sc.get("won"):
            mode_stats[mid]["won"] += 1
        mode_stats[mid]["best"] = max(mode_stats[mid]["best"], int(sc.get("subs", 0)))

    total_xp = int(profile.get("total_xp", 0))
    plvl, xp_in, xp_need = player_level_from_xp(total_xp)
    title = player_title(plvl, lang)

    return {
        "games": games,
        "total_subs": int(profile.get("total_subs", 0)),
        "best_game": int(profile.get("best_game", 0)),
        "correct_answers": int(profile.get("correct_answers", 0)),
        "win_pct": win_pct,
        "avg_score": avg_score,
        "win_streak": int(profile.get("win_streak", 0)),
        "total_xp": total_xp,
        "player_level": plvl,
        "xp_in": xp_in,
        "xp_need": xp_need,
        "title": title,
        "level_stats": profile.get("level_stats", {}),
        "mode_stats": mode_stats,
        "recent_scores": list(reversed(scores))[:10],
    }


def _go_back(app):
    if hasattr(app, "show_menu"):
        app.show_menu()
    elif hasattr(app, "show_start"):
        app.show_start()
    else:
        messagebox.showinfo("", "No navigation target available", parent=app)


def _get_token(app):
    return getattr(app, "access_token", None) or app.data.get("access_token")


def _get_active_profile(app):
    return app.data.get("active_profile", "Joueur")


def _get_profile_data(app, name):
    return app.data.get("profiles", {}).get(name, {})


def _do_logout(app):
    if messagebox.askyesno("", "Se déconnecter ?", parent=app._container):
        app.access_token = None
        app.data["access_token"] = None
        app.data["active_profile"] = None
        if not APIClient().health_check():
            app.show_login()
        else:
            _go_back(app)

