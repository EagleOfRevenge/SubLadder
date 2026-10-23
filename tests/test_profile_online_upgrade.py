import unittest

from game.screens.profile.submenus.link_account import promote_profile_to_online


class ProfileOnlineUpgradeTests(unittest.TestCase):
    def test_promote_offline_profile_to_online_via_discord(self):
        profile = {
            "profile_type": "offline",
            "linked_accounts": [],
        }

        updated = promote_profile_to_online(profile, "discord", "alice#1234")

        self.assertEqual(updated["profile_type"], "online")
        self.assertTrue(updated["linked_discord"])
        self.assertEqual(updated["discord_id"], "alice#1234")
        self.assertIn("discord", updated["linked_accounts"])

    def test_promote_offline_profile_to_online_via_steam(self):
        profile = {
            "profile_type": "offline",
            "linked_accounts": [],
        }

        updated = promote_profile_to_online(profile, "steam", "steam_12345")

        self.assertEqual(updated["profile_type"], "online")
        self.assertTrue(updated["linked_steam"])
        self.assertEqual(updated["steam_id"], "steam_12345")
        self.assertIn("steam", updated["linked_accounts"])


if __name__ == "__main__":
    unittest.main()
