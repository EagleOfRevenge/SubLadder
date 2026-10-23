"""
game/screens/profile/actions/export.py — Export JSON du profil.
"""

import json
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

from constants import GOLD, BG_DARK, BG_PANEL, SILVER, WHITE


def export_profile(app, name: str):
    """Exporter les données du profil en JSON."""
    p = app.data["profiles"].get(name)
    if not p:
        messagebox.showerror("", "Profile not found.", parent=app)
        return

    scores = p.get("scores", [])
    wins = [s for s in scores if s.get("won")]
    games = p.get("games_played", 0)

    export = {
        "profile": name,
        "exported_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "game_version": "2.5",
        "stats": {
            "games_played": games,
            "total_subs": p.get("total_subs", 0),
            "best_game_subs": p.get("best_game", 0),
            "correct_answers": p.get("correct_answers", 0),
            "wins": len(wins),
            "win_rate_pct": round(len(wins) / max(games, 1) * 100, 1),
            "avg_score_subs": round(p.get("total_subs", 0) / max(games, 1), 1),
            "win_streak": p.get("win_streak", 0),
            "total_xp": p.get("total_xp", 0),
            "player_level": p.get("player_level", 1),
            "profile_type": p.get("profile_type", "offline"),
        },
        "top_scores": scores[:10],
        "achievements": p.get("achievements", []),
    }

    path = filedialog.asksaveasfilename(
        parent=app, title="Export profile",
        defaultextension=".json",
        initialfile=f"subladder_{name}.json",
        filetypes=[("JSON file", "*.json"), ("All files", "*.*")],
    )
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f_out:
            json.dump(export, f_out, indent=2, ensure_ascii=False)
        messagebox.showinfo("", f"Profile exported to:\n{path}", parent=app)
    except OSError as e:
        messagebox.showerror("", f"Export failed:\n{e}", parent=app)
