import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add app directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))


class TestEnglishCoach(unittest.TestCase):
    @patch("google.genai.Client")
    def test_model_name_default(self, mock_genai_client):
        import main

        self.assertEqual(main.MODEL_NAME, "gemini-2.5-flash")

    def test_runtime_prompt_enforces_state_machine(self):
        from coach_prompt import SYSTEM_PROMPT

        required_phrases = [
            "vocab_pass_1",
            "vocab_pass_4",
            "story_round_1",
            "story_round_4",
            "story_expansion_teacher_qa",
            "active_yes_no",
            "guided_variation",
            "supported_roleplay",
            "[[LESSON_STATE:",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, SYSTEM_PROMPT)

    def test_control_markers_are_hidden_and_update_state(self):
        from lesson_state import default_lesson_state, extract_control_updates, merge_lesson_state

        raw = (
            "Very slow vocabulary input.\n"
            '[[LESSON_STATE:{"phase":"vocab_pass_2","topic":"Account access",'
            '"target_chunks":["locked account"]}]]\n'
            '[[STUDENT_UPDATE:{"understood_chunks":["locked account"]}]]'
        )
        visible, lesson_update, student_update = extract_control_updates(raw)
        self.assertEqual(visible, "Very slow vocabulary input.")
        state = merge_lesson_state(default_lesson_state(), lesson_update)
        state = merge_lesson_state(state, student_update)
        self.assertEqual(state["phase"], "vocab_pass_2")
        self.assertEqual(state["topic"], "Account access")
        self.assertIn("locked account", state["understood_chunks"])

    @patch("google.genai.Client")
    def test_health_endpoint(self, mock_genai_client):
        import main

        with main.app.test_client() as client:
            res = client.get("/health")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["service"], "english-coach")
            self.assertEqual(data["version"], "2.0.0")
            self.assertTrue(data["framework_loaded"])

    @patch("google.genai.Client")
    def test_preferences_default_and_update_are_session_scoped(self, mock_genai_client):
        import main

        main.SESSION_PREFERENCES.clear()
        with main.app.test_client() as client:
            default_res = client.get("/preferences", headers={"X-Session-ID": "prefs-a"})
            self.assertEqual(default_res.status_code, 200)
            self.assertEqual(
                default_res.get_json()["preferences"],
                {"pace": "four-pass", "focus": "it-support", "correction_style": "brief"},
            )

            update_res = client.post(
                "/preferences",
                json={
                    "session_id": "prefs-a",
                    "pace": "slow",
                    "focus": "interview",
                    "correction_style": "detailed",
                },
            )
            self.assertEqual(update_res.status_code, 200)
            self.assertEqual(update_res.get_json()["preferences"]["pace"], "slow")

            other_res = client.get("/preferences", headers={"X-Session-ID": "prefs-b"})
            self.assertEqual(other_res.get_json()["preferences"]["pace"], "four-pass")

    @patch("google.genai.Client")
    def test_preferences_reject_invalid_values(self, mock_genai_client):
        import main

        with main.app.test_client() as client:
            res = client.post(
                "/preferences",
                json={"session_id": "prefs-invalid", "pace": "extreme"},
            )
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.get_json()["error"], "invalid preferences")

    @patch("google.genai.Client")
    def test_chat_uses_framework_and_persists_lesson_state(self, mock_genai_client):
        import main

        sid = "test-session-123"
        main.CONVERSATIONS.clear()
        main.SESSION_PREFERENCES.clear()
        main.LESSON_STATES.delete(sid)

        mock_instance = MagicMock()
        mock_genai_client.return_value = mock_instance
        main._client = mock_instance
        mock_response = MagicMock()
        mock_response.text = (
            "Locked means you cannot enter the account right now.\n"
            '[[LESSON_STATE:{"phase":"vocab_pass_2","topic":"Account access",'
            '"practical_situation":"A user is locked out after wrong password attempts",'
            '"target_chunks":["account is locked","reset the password"]}]]'
        )
        mock_instance.models.generate_content.return_value = mock_response

        with main.app.test_client() as client:
            res = client.post("/chat", json={"message": "Start.", "session_id": sid})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["reply"], "Locked means you cannot enter the account right now.")
            self.assertEqual(data["lesson_state"]["phase"], "vocab_pass_2")
            self.assertEqual(data["lesson_state"]["topic"], "Account access")

            call_kwargs = mock_instance.models.generate_content.call_args.kwargs
            system_instruction = call_kwargs["config"].system_instruction
            self.assertIn("SYSTEM.md", system_instruction)
            self.assertIn("STUDENT_STATE.md", system_instruction)
            self.assertIn("LESSON_TEMPLATE.md", system_instruction)
            self.assertIn("QUALITY_CHECKLIST.md", system_instruction)
            self.assertIn("CURRENT LESSON STATE", system_instruction)

            state_res = client.get("/lesson-state", headers={"X-Session-ID": sid})
            self.assertEqual(state_res.get_json()["lesson_state"]["phase"], "vocab_pass_2")

    @patch("google.genai.Client")
    def test_chat_endpoint_error_handling(self, mock_genai_client):
        import main

        mock_instance = MagicMock()
        mock_genai_client.return_value = mock_instance
        main._client = mock_instance
        mock_instance.models.generate_content.side_effect = Exception("API quota exceeded")

        with main.app.test_client() as client:
            res = client.post("/chat", json={"message": "Hi!", "session_id": "test-session-err"})
            self.assertEqual(res.status_code, 500)
            data = res.get_json()
            self.assertIn("Failed to communicate with AI model", data["error"])

    @patch("google.genai.Client")
    def test_chat_message_length_limit(self, mock_genai_client):
        import main

        with main.app.test_client() as client:
            long_msg = "a" * 4001
            res = client.post("/chat", json={"message": long_msg})
            self.assertEqual(res.status_code, 400)
            self.assertIn("exceeds maximum length", res.get_json()["error"])

    @patch("google.genai.Client")
    def test_summary_empty_history(self, mock_genai_client):
        import main

        with main.app.test_client() as client:
            res = client.post("/summary", json={"session_id": "non-existent-session"})
            self.assertEqual(res.status_code, 400)
            self.assertIn("No conversation history found", res.get_json()["error"])

    @patch("google.genai.Client")
    def test_reset_clears_history_preferences_and_lesson_state(self, mock_genai_client):
        import main

        sid = "test-reset-123"
        main.CONVERSATIONS[sid] = []
        main.SESSION_PREFERENCES[sid] = {
            "pace": "slow",
            "focus": "general",
            "correction_style": "brief",
        }
        state = main.get_lesson_state(sid)
        state["phase"] = "active_yes_no"
        main.LESSON_STATES.set(sid, state)

        with main.app.test_client() as client:
            res = client.post("/reset", json={"session_id": sid})
            self.assertEqual(res.status_code, 200)
            self.assertNotIn(sid, main.CONVERSATIONS)
            self.assertNotIn(sid, main.SESSION_PREFERENCES)
            self.assertEqual(main.get_lesson_state(sid)["phase"], "vocab_pass_1")


if __name__ == "__main__":
    unittest.main()
