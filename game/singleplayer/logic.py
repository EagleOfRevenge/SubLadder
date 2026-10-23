"""
singleplayer/logic.py — Sub Ladder
Score recording, XP awarding, achievement evaluation for solo games.
"""

from constants import (
    GAME_MODES, PRIZE_LADDER, PRIZE_VALUES,
    xp_for_correct, player_level_from_xp, XP_WIN_BONUS,
    player_title,
)
from utils import load_achievements, save_data


def record_score(data: dict, game_state, won: bool,
                 walked: bool = False) -> tuple:
    """
    Record end-of-game result into the active profile.
    Returns (xp_gained, leveled_up, new_level, newly_unlocked_achievements).
    """
    profile = data.get("active_profile")
    if not profile or profile not in data["profiles"]:
        return 0, False, 1, []

    p       = data["profiles"][profile]
    history = game_state.history if game_state else []

    # ── Basic stats ───────────────────────────────────────────────
    if walked:
        if game_state.current_level == 1:
            subs = 0
            level = 0
        else:
            subs = PRIZE_VALUES[game_state.current_level - 2]
            level = game_state.current_level - 1

    elif won:
        subs  = PRIZE_VALUES[14]
        level = 15
    else:
        subs  = game_state.safe_value
        level = game_state.current_level - 1

    p["games_played"]    = p.get("games_played", 0) + 1
    p["total_subs"]      = p.get("total_subs", 0) + subs
    p["best_game"]       = max(p.get("best_game", 0), subs)
    p["correct_answers"] = p.get("correct_answers", 0) + game_state.correct_this_game

    # ── XP ────────────────────────────────────────────────────────
    xp_gained = sum(
        xp_for_correct(game_state.mode, e["level"])
        for e in history if e["was_correct"]
    )
    if won:
        xp_gained += XP_WIN_BONUS.get(game_state.mode, 100)

    old_xp = p.get("total_xp", 0)
    new_xp = old_xp + xp_gained
    p["total_xp"]      = new_xp
    p["xp_last_game"]  = xp_gained
    old_lvl, _, _      = player_level_from_xp(old_xp)
    new_lvl, _, _      = player_level_from_xp(new_xp)
    p["player_level"]  = new_lvl
    leveled_up         = new_lvl > old_lvl

    # ── Avg response time ─────────────────────────────────────────
    if history:
        times      = [e["time_secs"] for e in history]
        avg        = sum(times) / len(times)
        prev_avg   = p.get("avg_response_time", 0)
        prev_games = max(p.get("games_played", 1) - 1, 1)
        p["avg_response_time"] = round(
            (prev_avg * prev_games + avg) / (prev_games + 1), 1
        )

    # ── Per-level stats ───────────────────────────────────────────
    level_stats = p.get("level_stats", {})
    for entry in history:
        lk = str(entry["level"])
        if lk not in level_stats:
            level_stats[lk] = {"correct": 0, "total": 0}
        level_stats[lk]["total"] += 1
        if entry["was_correct"]:
            level_stats[lk]["correct"] += 1
    p["level_stats"] = level_stats

    # ── Win streak + legendary unlock ─────────────────────────────
    streak = p.get("win_streak", 0)
    if won:
        streak += 1
        if game_state.mode == "hard" and not p.get("legendary_unlocked"):
            p["legendary_unlocked"] = True
    else:
        streak = 0
    p["win_streak"] = streak

    # ── Scores history ────────────────────────────────────────────
    entry = {"subs": subs, "level": level, "won": won,
             "mode": game_state.mode, "walked": walked}
    scores = p.get("scores", [])
    scores.append(entry)
    scores.sort(key=lambda x: x["subs"], reverse=True)
    p["scores"] = scores[:20]

    # ── Clear save slot ───────────────────────────────────────────
    data["save"] = None
    save_data(data, silent=True)

    # ── Achievements ──────────────────────────────────────────────
    newly = check_achievements(data, p, game_state, won, walked,
                               level, subs, streak, new_lvl)

    return xp_gained, leveled_up, new_lvl, newly


def check_achievements(data: dict, p: dict, game_state,
                        won: bool, walked: bool,
                        level_reached: int, subs_won: int,
                        win_streak: int, player_lvl: int) -> list:
    """Evaluate all achievement triggers. Returns list of newly unlocked IDs."""
    ach_defs = load_achievements()
    already  = set(p.get("achievements", []))
    newly    = []

    def unlock(aid):
        if aid not in already:
            already.add(aid)
            newly.append(aid)

    games = p.get("games_played", 0)
    total = p.get("total_subs", 0)
    lf    = {k: not v for k, v in game_state.lifelines.items()}

    for ach in ach_defs:
        aid = ach["id"]
        if aid in already:
            continue
        t, tv = ach.get("trigger", {}).get("type"), ach.get("trigger", {}).get("value")

        if   t == "games_played"       and games >= tv:                    unlock(aid)
        elif t == "level_reached"      and level_reached >= tv:            unlock(aid)
        elif t == "win"                and tv and won:                     unlock(aid)
        elif t == "win_no_lifeline"    and tv and won and not any(lf.values()): unlock(aid)
        elif t == "win_no_fifty"       and tv and won and not lf.get("fifty"):  unlock(aid)
        elif t == "walk_away_with_safe" and tv and walked and game_state.safe_prize > 0: unlock(aid)
        elif t == "total_subs"         and total >= tv:                    unlock(aid)
        elif t == "fail_at_level"      and not won and not walked and level_reached == tv: unlock(aid)
        elif t == "win_streak"         and win_streak >= tv:               unlock(aid)
        elif t == "legendary_unlocked" and tv and p.get("legendary_unlocked"): unlock(aid)
        elif t == "win_legendary"      and tv and won and game_state.mode == "legendary": unlock(aid)
        elif t == "player_level"       and player_lvl >= tv:               unlock(aid)
        elif t == "total_xp"           and p.get("total_xp", 0) >= tv:    unlock(aid)
        elif t == "win_all_modes":
            won_modes = {sc.get("mode") for sc in p.get("scores", []) if sc.get("won")}
            if all(m in won_modes for m in GAME_MODES):
                unlock(aid)

    p["achievements"] = list(already)
    save_data(data, silent=True)
    return newly
