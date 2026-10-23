import unittest

from game.screens.profile.build import compute_profile_summary


class ProfileSummaryTests(unittest.TestCase):
    def test_compute_profile_summary_uses_scores_and_level_stats(self):
        profile = {
            "games_played": 3,
            "total_subs": 12,
            "best_game": 7,
            "correct_answers": 5,
            "scores": [
                {"won": True, "subs": 5, "mode": "normal", "level": 1},
                {"won": False, "subs": 3, "mode": "normal", "level": 2},
                {"won": True, "subs": 7, "mode": "ranked", "level": 3},
            ],
            "level_stats": {
                "1": {"total": 2, "correct": 1},
                "2": {"total": 1, "correct": 0},
            },
        }

        summary = compute_profile_summary(profile, "en")

        self.assertEqual(summary["games"], 3)
        self.assertEqual(summary["win_pct"], 67)
        self.assertEqual(summary["avg_score"], 4)
        self.assertEqual(summary["mode_stats"]["normal"]["played"], 2)
        self.assertEqual(summary["mode_stats"]["normal"]["won"], 1)
        self.assertEqual(summary["recent_scores"][0]["subs"], 7)


if __name__ == "__main__":
    unittest.main()
