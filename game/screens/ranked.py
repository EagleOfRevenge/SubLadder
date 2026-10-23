"""
screens/ranked.py — Sub Ladder
Ranked mode screen: ELO rating, rank tier, leaderboard, matchmaking.
"""

import json
import tkinter as tk
from tkinter import messagebox
import threading

from ..auth.client import APIClient
from ..constants import (
    GOLD, BG_DARK, BG_MID, BG_PANEL, SILVER, WHITE, TEXT_DISABLED,
    MENU_BTN_BG, BTN_DEFAULT, BTN_WRONG,
    BTN_CORRECT, BTN_SELECTED, TEXT_YELLOW,
)
from ui_helpers import create_scrollable_frame


def build(app):
    """Build the Ranked screen with ELO stats, rank info, and leaderboard."""
    app._clear()
    
    f = app._container
    
    # Header
    header = tk.Frame(f, bg=app.BG_DARK)
    header.pack(fill="x", padx=0, pady=0)
    tk.Label(header, text="⚔️  RANKED", bg=app.BG_DARK, fg=app.GOLD,
             font=app.f_title).pack(pady=(24, 6))
    
    # Get current profile name
    active_profile = app.data.get("active_profile", "default")
    token = app.data.get("access_token") or getattr(app, "access_token", None)
    
    # Create tabs for different sections
    tab_frame = tk.Frame(f, bg=app.BG_MID)
    tab_frame.pack(fill="x", padx=0, pady=0)
    
    current_tab = tk.StringVar(value="stats")
    
    def switch_tab(tab_name):
        current_tab.set(tab_name)
        _update_content(app, content_frame, tab_name, active_profile, token)
    
    # Tab buttons
    tabs = [
        ("📊 My Stats", "stats"),
        ("🏆 Leaderboard", "leaderboard"),
        ("⚡ Matchmaking", "matchmaking"),
    ]
    
    for label, tab_id in tabs:
        btn_bg = app.BTN_SELECTED if tab_id == "stats" else app.BTN_DEFAULT
        tk.Button(
            tab_frame, text=label,
            bg=btn_bg, fg=app.GOLD if tab_id == "stats" else app.WHITE,
            font=app.f_label, relief="flat", cursor="hand2",
            padx=15, pady=8,
            command=lambda t=tab_id: switch_tab(t)
        ).pack(side="left", fill="x", expand=True, padx=1, pady=1)
    
    # Content area
    content_frame = tk.Frame(f, bg=app.BG_DARK)
    content_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    # Initial content
    _update_content(app, content_frame, "stats", active_profile, token)

def _update_content(app, content_frame, tab_name, profile_name, token):
    """Update content frame based on selected tab."""
    # Clear content
    for widget in content_frame.winfo_children():
        widget.destroy()
    
    if tab_name == "stats":
        _build_stats_tab(app, content_frame, profile_name, token)
    elif tab_name == "leaderboard":
        _build_leaderboard_tab(app, content_frame, token)
    elif tab_name == "matchmaking":
        _build_matchmaking_tab(app, content_frame, profile_name, token)

def _build_stats_tab(app, parent, profile_name, token):
    """Build the 'My Stats' tab."""
    canvas, content = create_scrollable_frame(parent, app.BG_DARK)
    
    # Show loading message while fetching
    loading_lbl = tk.Label(content, text="⏳ Loading stats...",
                          bg=app.BG_DARK, fg=app.SILVER, font=app.f_label)
    loading_lbl.pack(pady=20)
    
    # Fetch stats in background
    def fetch_stats():
        try:
            api = APIClient()
            if not token:
                raise RuntimeError("No auth token available")
            result = api.get_ranked_stats(profile_name, token)
            if result.get("error"):
                raise RuntimeError(result["error"])
            loading_lbl.destroy()
            _display_stats(app, content, result)
        except Exception as e:
            loading_lbl.config(text=f"❌ Error: {str(e)}")
    
    thread = threading.Thread(target=fetch_stats, daemon=True)
    thread.start()

def _display_stats(app, parent, stats):
    """Display player stats."""
    # Rank display
    rank_frame = tk.Frame(parent, bg=app.BG_PANEL)
    rank_frame.pack(fill="x", padx=20, pady=12)
    
    rank = stats["current_rank"]
    rank_display = rank["display"]
    
    tk.Label(rank_frame, text="CURRENT RANK",
            bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(anchor="w", padx=8, pady=(8, 2))
    
    tk.Label(rank_frame, text=rank_display,
            bg=app.BG_PANEL, fg=app.GOLD, font=("Arial", 28, "bold")).pack(anchor="w", padx=8, pady=2)
    
    # ELO display
    tk.Label(rank_frame, text=f"ELO: {stats['elo']} pts",
            bg=app.BG_PANEL, fg=app.WHITE, font=app.f_label).pack(anchor="w", padx=8, pady=(2, 8))
    
    # Win rate and games
    stats_frame = tk.Frame(parent, bg=app.BG_PANEL)
    stats_frame.pack(fill="x", padx=20, pady=8)
    
    for label, value, color in [
        (f"Games Played", f"{stats['games_played']}", app.WHITE),
        (f"Games Won", f"{stats['games_won']}", app.GOLD),
        (f"Win Rate", f"{stats['win_rate']:.1f}%", app.GOLD),
    ]:
        row = tk.Frame(stats_frame, bg=app.BG_PANEL)
        row.pack(fill="x", padx=8, pady=4)
        tk.Label(row, text=label, bg=app.BG_PANEL, fg=app.SILVER,
                font=app.f_label).pack(side="left", expand=True)
        tk.Label(row, text=value, bg=app.BG_PANEL, fg=color,
                font=("Arial", 12, "bold")).pack(side="right")
    
    # Progression bar
    prog = stats["progression_to_next"]
    if prog["next"]:
        prog_frame = tk.Frame(parent, bg=app.BG_PANEL)
        prog_frame.pack(fill="x", padx=20, pady=12)
        
        tk.Label(prog_frame, text=f"Progress to {prog['next']}",
                bg=app.BG_PANEL, fg=app.SILVER, font=app.f_small).pack(anchor="w", padx=8, pady=(8, 2))
        
        # Progress bar
        bar_frame = tk.Frame(prog_frame, bg=app.BG_MID, height=20)
        bar_frame.pack(fill="x", padx=8, pady=4)
        
        progress_width = int((prog['progress_percent'] / 100) * 300)
        tk.Frame(bar_frame, bg=app.GOLD, width=progress_width, height=20).pack(side="left", fill="y")
        
        tk.Label(prog_frame, text=f"{prog['current_elo']}/{prog['current_elo'] + prog['elo_to_next']} ELO (+{prog['elo_to_next']} needed)",
                bg=app.BG_PANEL, fg=app.WHITE, font=app.f_small).pack(anchor="w", padx=8, pady=(2, 8))

def _build_leaderboard_tab(app, parent, token):
    """Build the 'Leaderboard' tab."""
    canvas, content = create_scrollable_frame(parent, app.BG_DARK)
    
    loading_lbl = tk.Label(content, text="⏳ Loading leaderboard...",
                          bg=app.BG_DARK, fg=app.SILVER, font=app.f_label)
    loading_lbl.pack(pady=20)
    
    def fetch_leaderboard():
        try:
            api = APIClient()
            result = api.get_ranked_leaderboard(token=token, limit=20)
            if result.get("error"):
                raise RuntimeError(result["error"])
            leaders = result.get("leaderboard", [])
            loading_lbl.destroy()
            _display_leaderboard(app, content, leaders)
        except Exception as e:
            loading_lbl.config(text=f"❌ Error: {str(e)}")
    
    thread = threading.Thread(target=fetch_leaderboard, daemon=True)
    thread.start()

def _display_leaderboard(app, parent, players):
    """Display the ranked leaderboard."""
    header_frame = tk.Frame(parent, bg=app.BG_PANEL)
    header_frame.pack(fill="x", padx=20, pady=12)
    
    tk.Label(header_frame, text="TOP 50 RANKED PLAYERS",
            bg=app.BG_PANEL, fg=app.GOLD, font=("Arial", 14, "bold")).pack(anchor="w", padx=8, pady=8)
    
    # Column headers
    col_frame = tk.Frame(parent, bg=app.BG_MID)
    col_frame.pack(fill="x", padx=20, pady=(0, 4))
    
    for header, width in [("#", 0.1), ("Player", 0.4), ("Rank", 0.3), ("ELO", 0.2)]:
        tk.Label(col_frame, text=header, bg=app.BG_MID, fg=app.SILVER,
                font=app.f_label, width=int(25 * width)).pack(side="left", padx=2)
    
    # Player rows
    for player in players:
        row_frame = tk.Frame(parent, bg=app.BG_PANEL)
        row_frame.pack(fill="x", padx=20, pady=2)
        
        # Rank medal
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(player["rank"], f"{player['rank']}.")
        
        tk.Label(row_frame, text=medal, bg=app.BG_PANEL, fg=app.GOLD,
                font=("Arial", 12, "bold"), width=4).pack(side="left", padx=2)
        
        # Player name
        tk.Label(row_frame, text=player.get("game_name") or player.get("profile_name"), bg=app.BG_PANEL, fg=app.WHITE,
                font=app.f_label, width=20).pack(side="left", padx=2)
        
        # Rank tier
        tk.Label(row_frame, text=player["rank_display"], bg=app.BG_PANEL, fg=app.TEXT_YELLOW,
                font=app.f_label, width=15).pack(side="left", padx=2)
        
        # ELO
        tk.Label(row_frame, text=str(player["elo"]), bg=app.BG_PANEL, fg=app.GOLD,
                font=("Arial", 12, "bold"), width=10).pack(side="left", padx=2)

def _build_matchmaking_tab(app, parent, profile_name, token):
    """Build the 'Matchmaking' tab."""
    canvas, content = create_scrollable_frame(parent, app.BG_DARK)
    
    info_frame = tk.Frame(content, bg=app.BG_PANEL)
    info_frame.pack(fill="x", padx=20, pady=12)
    
    tk.Label(info_frame, text="RANKED MATCHMAKING",
            bg=app.BG_PANEL, fg=app.GOLD, font=("Arial", 14, "bold")).pack(anchor="w", padx=8, pady=(8, 4))
    
    tk.Label(info_frame, text="Find an opponent within your ELO range and compete for higher ranks!",
            bg=app.BG_PANEL, fg=app.SILVER, font=app.f_label, wraplength=400, justify="left").pack(anchor="w", padx=8, pady=4)
    
    # Search button
    button_frame = tk.Frame(content, bg=app.BG_PANEL)
    button_frame.pack(pady=12)

    tk.Button(button_frame, text="🔍 FIND OPPONENT",
             bg=app.BTN_SELECTED, fg=app.GOLD, font=("Arial", 12, "bold"),
             relief="flat", cursor="hand2", padx=20, pady=10,
             command=lambda: _search_matchmaking(app, profile_name, token, status_label)).pack(side="left", padx=(0, 8))

    tk.Button(button_frame, text="⏹ LEAVE QUEUE",
             bg=app.BTN_DEFAULT, fg=app.WHITE, font=("Arial", 12, "bold"),
             relief="flat", cursor="hand2", padx=20, pady=10,
             command=lambda: _leave_matchmaking(app, token, status_label)).pack(side="left")
    
    # Queue status area
    queue_frame = tk.Frame(content, bg=app.BG_PANEL)
    queue_frame.pack(fill="x", padx=20, pady=8)
    
    status_label = tk.Label(queue_frame, text="Ready to search",
                           bg=app.BG_PANEL, fg=app.SILVER, font=app.f_label)
    status_label.pack(padx=8, pady=8)
    
    # Info about ranked
    info_frame2 = tk.Frame(content, bg=app.BG_PANEL)
    info_frame2.pack(fill="x", padx=20, pady=12)
    
    rules = [
        "• All players in ranked must have 5+ games played",
        "• Opponents are matched within ±200 ELO points",
        "• Winner gains ELO, loser loses ELO",
        "• Seasonal resets happen every 3 months",
    ]
    
    for rule in rules:
        tk.Label(info_frame2, text=rule, bg=app.BG_PANEL, fg=app.WHITE,
                font=app.f_label, justify="left").pack(anchor="w", padx=8, pady=2)

def _search_matchmaking(app, profile_name, token, status_label):
    """Start searching for a ranked opponent."""
    if not token:
        messagebox.showwarning("Matchmaking", "Please log in to use ranked matchmaking.")
        return

    def run_search():
        try:
            api = APIClient()
            result = api.find_ranked_match(token)
            if result.get("error"):
                raise RuntimeError(result["error"])
            if result.get("status") == "match_found":
                msg = f"Match found against {result['opponent']['profile_name']} ({result['opponent']['elo']} ELO)"
            else:
                msg = f"Queued: {result.get('message', 'Waiting for an opponent')} (position {result.get('position', 1)})"
            app.after(0, lambda: status_label.config(text=msg))
        except Exception as e:
            app.after(0, lambda: status_label.config(text=f"Search failed: {e}"))

    status_label.config(text="Searching for an opponent...")
    threading.Thread(target=run_search, daemon=True).start()


def _leave_matchmaking(app, token, status_label):
    """Leave the ranked queue."""
    if not token:
        return

    def run_leave():
        try:
            api = APIClient()
            result = api.leave_ranked_matchmaking(token)
            if result.get("error"):
                raise RuntimeError(result["error"])
            app.after(0, lambda: status_label.config(text="You left the ranked queue."))
        except Exception as e:
            app.after(0, lambda: status_label.config(text=f"Could not leave queue: {e}"))

    threading.Thread(target=run_leave, daemon=True).start()
