import unittest

from game.screens.menu.profile_display import format_profile_subtitle


class MenuPolishTests(unittest.TestCase):
    def test_format_profile_subtitle_for_online_profile(self):
        profile_data = {"profile_type": "online", "games_played": 5, "level": 3}
        self.assertEqual(format_profile_subtitle(profile_data, "en", 4), "Level 3 • 5 games")

    def test_format_profile_subtitle_for_offline_profile(self):
        profile_data = {"profile_type": "offline", "total_xp": 0}
        self.assertEqual(format_profile_subtitle(profile_data, "fr", 1, title="Novice"), "Niveau 1 ✦ Novice")


if __name__ == "__main__":
    unittest.main()
