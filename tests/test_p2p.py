import unittest
import time

from game.multiplayer.p2p import P2PSessionHost, P2PClient


class P2PTests(unittest.TestCase):
    def test_host_session_exposes_shared_question_index(self):
        host = P2PSessionHost(host_ip="127.0.0.1", port=0)
        host.start()

        try:
            session = host.create_session(question_id=7, timer=12, question_index=3)
            self.assertEqual(session["question_index"], 3)

            client = P2PClient()
            joined = client.join_session(host_ip="127.0.0.1", port=session["port"], player_name="bob")

            self.assertEqual(joined["round_state"]["question_index"], 3)
        finally:
            host.stop()
            client.close()

    def test_local_host_and_join_session_syncs_question_and_winner(self):
        host = P2PSessionHost(host_ip="127.0.0.1", port=0)
        host.start()

        try:
            session = host.create_session(question_id=7, timer=12)
            client = P2PClient()
            joined = client.join_session(host_ip="127.0.0.1", port=session["port"], player_name="alice")

            self.assertEqual(joined["status"], "joined")
            self.assertEqual(joined["player_name"], "alice")

            sync = host.sync_round(question_id=7, timer=12)
            self.assertEqual(sync["question_id"], 7)
            self.assertEqual(sync["timer"], 12)

            client.send_answer(level=5, time_taken=1.8)
            host.register_answer(player_name="alice", level=5, time_taken=1.8)

            winner = host.determine_winner()
            self.assertEqual(winner["player_name"], "alice")
            self.assertEqual(winner["level"], 5)
        finally:
            host.stop()
            client.close()


if __name__ == "__main__":
    unittest.main()
