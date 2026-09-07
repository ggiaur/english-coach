import tempfile
import unittest
from pathlib import Path

import learner_state


class LearnerStatePersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        learner_state.STATE_PATH = Path(self.tmp.name) / "learner-state.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_progress_round_trip_survives_in_memory_reset(self):
        sid = "learner-42"
        learner_state.save_learner_state(sid, {
            "preferences": {"pace": "slow", "focus": "it-support"},
            "session_summaries": ["Needs more practice asking users to restart Excel politely."],
            "review_items": [{
                "phrase": "Please restart the Excel",
                "correction": "Please restart Excel",
                "note": "No article before the application name here.",
            }],
            "practice_count": 3,
        })

        restored = learner_state.load_learner_state(sid)

        self.assertEqual(restored["practice_count"], 3)
        self.assertEqual(restored["preferences"]["pace"], "slow")
        self.assertIn("restart Excel", restored["session_summaries"][0])
        self.assertEqual(restored["review_items"][0]["correction"], "Please restart Excel")

    def test_only_five_recent_session_summaries_are_kept(self):
        sid = "learner-43"
        learner_state.save_learner_state(sid, {
            "session_summaries": [f"session-{i}" for i in range(8)],
            "practice_count": 8,
        })
        restored = learner_state.load_learner_state(sid)
        self.assertEqual(restored["session_summaries"], ["session-3", "session-4", "session-5", "session-6", "session-7"])

    def test_review_memory_is_bounded_and_invalid_items_are_discarded(self):
        sid = "learner-44"
        learner_state.save_learner_state(sid, {
            "review_items": [
                {"phrase": f"wrong-{i}", "correction": f"right-{i}", "note": ""}
                for i in range(10)
            ] + [{"phrase": "missing correction"}],
        })
        restored = learner_state.load_learner_state(sid)
        self.assertEqual(len(restored["review_items"]), 7)
        self.assertEqual(restored["review_items"][0]["phrase"], "wrong-3")
        self.assertEqual(restored["review_items"][-1]["correction"], "right-9")


if __name__ == "__main__":
    unittest.main()
