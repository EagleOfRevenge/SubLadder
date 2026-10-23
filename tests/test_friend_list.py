import unittest

from game.screens.friend_list import filter_friend_list, normalize_friend, sort_friend_list
from game.screens.profile.ui.tabs.overview_tab import build_overview_tab


class FriendListTests(unittest.TestCase):
    def test_friend_list_normalizes_and_sorts_buckets(self):
        friends = [
            {"name": "Charlie", "status": "offline"},
            {"name": "Alice", "status": "ranked_game"},
            {"name": "Bob", "status": "away"},
        ]

        normalized = sort_friend_list(friends)
        self.assertEqual([friend["name"] for friend in normalized], ["Alice", "Bob", "Charlie"])
        self.assertEqual(normalize_friend(friends[0])["bucket"], "offline")
        self.assertEqual(normalize_friend(friends[1])["bucket"], "ingame")

    def test_filter_friend_list_matches_name_and_metadata(self):
        friends = [
            {"name": "Alice", "clan": "Alpha", "tag": "123", "rank": "Gold", "status": "online"},
            {"name": "Bob", "clan": "Beta", "tag": "456", "rank": "Silver", "status": "offline"},
        ]

        filtered = filter_friend_list(friends, "alpha")
        self.assertEqual([friend["name"] for friend in filtered], ["Alice"])

    def test_friend_list_handles_malformed_entries(self):
        friends = [None, "bad-entry", {"name": "Alice", "status": "online"}]

        normalized = sort_friend_list(friends)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["name"], "Alice")
        self.assertEqual(normalize_friend(None)["bucket"], "offline")

    def test_overview_tab_module_can_be_imported(self):
        self.assertTrue(callable(build_overview_tab))


if __name__ == "__main__":
    unittest.main()
