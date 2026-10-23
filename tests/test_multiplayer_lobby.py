import unittest

from game.multiplayer.p2p import NormalLobby, RankedMatchmaker
from game.screens.multiplayer_normal import format_table_summary


class MultiplayerLobbyTests(unittest.TestCase):
    def test_normal_lobby_creates_visible_table_and_join_flow(self):
        lobby = NormalLobby()
        table = lobby.create_table("Friends Arena", "alice")

        self.assertEqual(table["table_name"], "Friends Arena")
        self.assertEqual(table["host_player"], "alice")
        self.assertFalse(table["locked"])
        self.assertEqual(len(lobby.list_tables()), 1)

        joined = lobby.join_table(table["table_id"], "bob")
        self.assertEqual(joined["status"], "joined")
        self.assertEqual(joined["player_name"], "bob")

    def test_ranked_matchmaker_pairs_players_and_picks_a_host(self):
        matcher = RankedMatchmaker()
        matcher.enqueue_player("alice", 1180, connection_quality=95)
        matcher.enqueue_player("bob", 1210, connection_quality=80)

        match = matcher.find_match()
        self.assertIsNotNone(match)
        self.assertEqual(set(match["players"]), {"alice", "bob"})
        self.assertEqual(match["host"], "alice")

    def test_format_table_summary_includes_player_count_and_lock_state(self):
        table = {
            "table_name": "Friends Arena",
            "host_player": "alice",
            "player_count": 2,
            "locked": True,
            "players": ["alice", "bob"],
            "status": "waiting",
        }

        summary = format_table_summary(table)
        self.assertIn("Friends Arena", summary)
        self.assertIn("2 players", summary)
        self.assertIn("locked", summary.lower())


if __name__ == "__main__":
    unittest.main()
