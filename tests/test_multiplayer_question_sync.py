import unittest

from game.game_state import GameState


class MultiplayerQuestionSyncTests(unittest.TestCase):
    def test_question_index_is_shared_across_languages(self):
        english_questions = [
            {"id": "en_Q001", "level_easy": 1, "level_normal": 1, "theme": "general", "question": "Q1", "right_answer": "A", "other_answers": ["B", "C", "D"]},
            {"id": "en_Q002", "level_easy": 1, "level_normal": 1, "theme": "general", "question": "Q2", "right_answer": "A", "other_answers": ["B", "C", "D"]},
        ]
        french_questions = [
            {"id": "fr_Q001", "level_easy": 1, "level_normal": 1, "theme": "general", "question": "Q1 FR", "right_answer": "A", "other_answers": ["B", "C", "D"]},
            {"id": "fr_Q002", "level_easy": 1, "level_normal": 1, "theme": "general", "question": "Q2 FR", "right_answer": "A", "other_answers": ["B", "C", "D"]},
        ]

        state_en = GameState(english_questions, mode="normal")
        state_fr = GameState(french_questions, mode="normal")

        self.assertEqual(state_en.current_q["id"], "en_Q001")
        self.assertEqual(state_fr.current_q["id"], "fr_Q001")

        # The shared slot index should resolve to the same slot in both languages.
        self.assertEqual(state_en.current_q["id"].split("_")[-1], state_fr.current_q["id"].split("_")[-1])


if __name__ == "__main__":
    unittest.main()
