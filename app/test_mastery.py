import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

import main


class TestMasteryRetirement(unittest.TestCase):
    def test_extracts_mastered_marker_without_showing_machine_lines(self):
        visible, review_items, mastered = main.extract_review_items(
            "Good progress today.\n"
            "MEMORY_ITEM: I work in server || I work on the server || Use the right preposition.\n"
            "MASTERED_ITEM: I have a problem with Excel"
        )
        self.assertEqual(visible, "Good progress today.")
        self.assertEqual(review_items[0]["correction"], "I work on the server")
        self.assertEqual(mastered, ["I have a problem with Excel"])

    def test_mastered_item_is_removed_from_next_session_review_memory(self):
        items = [
            {"phrase": "I have problem with Excel", "correction": "I have a problem with Excel", "note": "article"},
            {"phrase": "I work in server", "correction": "I work on the server", "note": "preposition"},
        ]
        remaining = main.retire_mastered_items(items, ["I have a problem with Excel"])
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["correction"], "I work on the server")


if __name__ == "__main__":
    unittest.main()
