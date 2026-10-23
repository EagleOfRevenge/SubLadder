"""
game_state.py — Sub Ladder
GameState class and question-related helpers.
"""

import json
import os
import sys
import random

from constants import (
    ANSWER_LABELS, GAME_MODES, SAFE_HAVENS,
    xp_for_correct, player_level_from_xp, XP_WIN_BONUS,
)
from utils import load_questions_file

# ══════════════════════════════════════════════════════════════════
# PATHS (relative to data/ directory)
# ══════════════════════════════════════════════════════════════════
# Nuitka / PyInstaller detection — see utils.py / main.py comments.
if getattr(sys, "frozen", False):
    _frozen_base = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
    ROOT_DIR = _frozen_base
    DATA_DIR = os.path.join(_frozen_base, "data")
else:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

Q_DIR    = os.path.join(DATA_DIR, "questions")


# ══════════════════════════════════════════════════════════════════
# QUESTION HELPERS
# ══════════════════════════════════════════════════════════════════

def load_questions(questions_file: str) -> list:
    return load_questions_file(questions_file)


def build_displayed_question(q: dict) -> dict:
    """Pick 3 random wrong answers, shuffle all 4 into A/B/C/D."""
    wrong  = random.sample(q["other_answers"], min(3, len(q["other_answers"])))
    four   = [q["right_answer"]] + wrong
    random.shuffle(four)
    answers = {ANSWER_LABELS[i]: four[i] for i in range(4)}
    correct = next(k for k, v in answers.items() if v == q["right_answer"])
    return {"answers": answers, "correct": correct}


def get_pool(questions: list, level: int, mode: str, exclude: set) -> list:
    field = GAME_MODES.get(mode, GAME_MODES["normal"])["key"]
    pool  = [q for q in questions
             if q.get(field, -1) == level and q["id"] not in exclude]
    if not pool:
        pool = [q for q in questions if q.get(field, -1) == level]
    return pool


# ══════════════════════════════════════════════════════════════════
# GAME STATE
# ══════════════════════════════════════════════════════════════════

class GameState:
    def __init__(self, all_questions: list, mode: str = "normal", question_index: int | None = None):
        self.all_questions     = all_questions
        self.mode              = mode
        self.current_level     = 1
        self.used_ids          = set()
        self.lifelines         = {"fifty": True, "vote": True, "switch": True}
        self.current_q         = None
        self.displayed         = None
        self.eliminated        = set()
        self.safe_prize        = 0
        self.game_over         = False
        self.won               = False
        self.correct_this_game = 0
        self.history: list     = []
        self.question_index    = question_index if question_index is not None else 0
        self._pick()

    # ── Internal ──────────────────────────────────────────────────

    def _pick(self):
        pool = get_pool(self.all_questions, self.current_level,
                        self.mode, self.used_ids)
        if not pool:
            pool = [q for q in self.all_questions if q.get("level_easy", -1) == self.current_level or q.get("level_normal", -1) == self.current_level or q.get("level_hard", -1) == self.current_level or q.get("level_legendary", -1) == self.current_level]
        if self.question_index is not None and self.question_index < len(pool):
            self.current_q = pool[self.question_index]
        else:
            self.current_q = random.choice(pool)
        self.used_ids.add(self.current_q["id"])
        self.displayed  = build_displayed_question(self.current_q)
        self.eliminated = set()

    # ── Lifelines ─────────────────────────────────────────────────

    def fifty_fifty(self) -> set:
        correct = self.displayed["correct"]
        wrong   = [k for k in ANSWER_LABELS if k != correct]
        removed = set(random.sample(wrong, 2))
        self.eliminated = removed
        self.lifelines["fifty"] = False
        return removed

    def chat_vote(self) -> dict:
        correct = self.displayed["correct"]
        w       = max(35, 75 - (self.current_level - 1) * 3)
        active  = [k for k in ANSWER_LABELS if k not in self.eliminated]
        wrong_a = [k for k in active if k != correct]
        per_w   = (100 - w) // max(len(wrong_a), 1)
        votes   = {k: (0 if k in self.eliminated else (w if k == correct else per_w))
                   for k in ANSWER_LABELS}
        total   = sum(votes.values())
        votes   = {k: round(v / total * 100) for k, v in votes.items()}
        diff    = 100 - sum(votes.values())
        votes[correct] += diff
        self.lifelines["vote"] = False
        return votes

    def switch(self):
        self.lifelines["switch"] = False
        self._pick()

    # ── Answer ────────────────────────────────────────────────────

    def answer(self, label: str) -> bool:
        ok = self.displayed["correct"] == label
        if ok:
            self.correct_this_game += 1
            if self.current_level == 15:
                self.won = self.game_over = True
            else:
                if self.current_level in SAFE_HAVENS:
                    self.safe_prize = self.current_level
                self.current_level += 1
                self._pick()
        else:
            self.game_over = True
        return ok

    def walk_away(self):
        self.game_over = True

    # ── Serialise / Deserialise ───────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "mode":              self.mode,
            "level":             self.current_level,
            "used_ids":          list(self.used_ids),
            "lifelines":         dict(self.lifelines),
            "safe_prize":        self.safe_prize,
            "correct_this_game": self.correct_this_game,
            "question_id":       self.current_q["id"],
            "question_index":    self.question_index,
            "displayed": {
                "answers": dict(self.displayed["answers"]),
                "correct": self.displayed["correct"],
            },
            "eliminated": list(self.eliminated),
        }

    @classmethod
    def from_dict(cls, all_questions: list, d: dict) -> "GameState":
        gs = cls.__new__(cls)
        gs.all_questions     = all_questions
        gs.mode              = d.get("mode", "normal")
        gs.current_level     = d["level"]
        gs.used_ids          = set(d["used_ids"])
        gs.lifelines         = dict(d["lifelines"])
        gs.safe_prize        = d["safe_prize"]
        gs.correct_this_game = d.get("correct_this_game", 0)
        gs.game_over         = False
        gs.won               = False
        gs.eliminated        = set(d["eliminated"])
        gs.history           = []
        gs.question_index = d.get("question_index", 0)
        gs.current_q = next(
            q for q in all_questions if q["id"] == d["question_id"]
        )
        gs.displayed = {
            "answers": dict(d["displayed"]["answers"]),
            "correct": d["displayed"]["correct"],
        }
        return gs

    # ── Properties ────────────────────────────────────────────────

    @property
    def prize_label(self):
        from constants import PRIZE_LADDER
        return PRIZE_LADDER[self.current_level - 1]

    @property
    def prize_value(self):
        from constants import PRIZE_VALUES
        return PRIZE_VALUES[self.current_level - 1]

    @property
    def walkout_prize_value(self):
        """Return the prize the player walks away with (last fully completed level)."""
        from constants import PRIZE_VALUES
        return PRIZE_VALUES[self.current_level - 2] if self.current_level >= 2 else 0

    @property
    def walkout_prize_label(self):
        """Return the label of the prize the player walks away with."""
        from constants import PRIZE_LADDER
        if self.current_level >= 2:
            return PRIZE_LADDER[self.current_level - 2]
        return "0 subs"

    @property
    def safe_label(self):
        from constants import PRIZE_LADDER
        return PRIZE_LADDER[self.safe_prize - 1] if self.safe_prize else "0 subs"

    @property
    def safe_value(self):
        from constants import PRIZE_VALUES
        return PRIZE_VALUES[self.safe_prize - 1] if self.safe_prize else 0
