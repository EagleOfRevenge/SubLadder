import unittest

from game.main import App
from game.screens.pre_menu import _build_online_profile_data


class AppNavigationTests(unittest.TestCase):
    def test_multiplayer_menu_navigation_methods_exist(self):
        self.assertTrue(hasattr(App, "show_multiplayer_submenu"))
        self.assertTrue(hasattr(App, "show_multiplayer_normal"))
        self.assertTrue(hasattr(App, "show_streamer_vs_viewer"))

    def test_pre_menu_navigation_methods_exist(self):
        self.assertTrue(hasattr(App, "show_pre_menu"))
        self.assertTrue(hasattr(App, "show_pre_menu_profiles"))

    def test_online_profile_payload_includes_provider_details(self):
        profile = _build_online_profile_data("discord", "Alice", "user#1234")
        self.assertEqual(profile["profile_type"], "online")
        self.assertEqual(profile["provider"], "discord")
        self.assertEqual(profile["provider_account"], "user#1234")


if __name__ == "__main__":
    unittest.main()
