import unittest

from game.multiplayer.ranked import get_rank_display, get_progression_to_next_rank, new_ratings


class RankedSystemTests(unittest.TestCase):
    def test_champion_rank_has_no_division_suffix(self):
        rank = get_rank_display(2400)
        self.assertEqual(rank["display"], "Champion")
        self.assertIsNone(rank["division"])

    def test_grand_champion_rank_is_reserved_for_top_elo(self):
        rank = get_rank_display(2500)
        self.assertEqual(rank["display"], "Grand Champion")

    def test_progression_to_next_rank_is_exposed_for_champion_players(self):
        progression = get_progression_to_next_rank(2400)
        self.assertEqual(progression["next"], "Grand Champion")
        self.assertEqual(progression["elo_to_next"], 100)

    def test_new_ratings_increase_winner_elo_and_decrease_loser_elo(self):
        winner_elo, loser_elo = new_ratings(1200, 1000)
        self.assertGreater(winner_elo, 1200)
        self.assertLess(loser_elo, 1000)


if __name__ == "__main__":
    unittest.main()
