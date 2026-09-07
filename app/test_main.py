import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add app directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))


class TestEnglishCoach(unittest.TestCase):

    @patch("google.genai.Client")
    def test_model_name_default(self, mock_genai_client):
        import main
        self.assertEqual(main.MODEL_NAME, "gemini-2.5-flash")

    def test_coach_prompt_enforces_four_pass_speaking_drill(self):
        from coach_prompt import SYSTEM_PROMPT
        required_phrases = [
            "Very slow pass 1",
            "Very slow pass 2",
            "Medium-speed pass",
            "Natural-speed pass",
            "affirmative statement",
            "negative statement",
            "question-and-answer mini-story drills",
            "definition in simple English",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, SYSTEM_PROMPT)

    def test_coach_prompt_prioritizes_realistic_it_support_language(self):
        from coach_prompt import SYSTEM_PROMPT
        self.assertIn("Excel problems", SYSTEM_PROMPT)
        self.assertIn("password resets", SYSTEM_PROMPT)
        self.assertIn("remote assistance", SYSTEM_PROMPT)
        self.assertIn("what error message the user sees", SYSTEM_PROMPT)
        self.assertIn("requesting a restart", SYSTEM_PROMPT)

    @patch("google.genai.Client")
    def test_health_endpoint(self, mock_genai_client):
        import main
        with main.app.test_client() as client:
            res = client.get("/health")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.get_json(), {"status": "ok", "service": "english-coach", "version": "1.3.0"})

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
    def test_chat_endpoint_uses_correct_model_and_session_preferences(self, mock_genai_client):
        import main
        main.CONVERSATIONS.clear()
        main.SESSION_PREFERENCES.clear()
        mock_instance = MagicMock()
        mock_genai_client.return_value = mock_instance
        main._client = mock_instance
        mock_response = MagicMock()
        mock_response.text = "Hello! Ready for standup practice?"
        mock_instance.models.generate_content.return_value = mock_response

        with main.app.test_client() as client:
            client.post(
                "/preferences",
                json={"session_id": "test-session-123", "pace": "slow", "focus": "interview"},
            )
            res = client.post("/chat", json={"message": "Hi!", "session_id": "test-session-123"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["reply"], "Hello! Ready for standup practice?")
            self.assertEqual(data["session_id"], "test-session-123")
            self.assertEqual(data["preferences"]["pace"], "slow")

            mock_instance.models.generate_content.assert_called_once()
            call_kwargs = mock_instance.models.generate_content.call_args.kwargs
            self.assertEqual(call_kwargs.get("model"), "gemini-2.5-flash")
            system_instruction = call_kwargs["config"].system_instruction
            self.assertIn("pace: slow", system_instruction)
            self.assertIn("focus: interview", system_instruction)

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
    def test_summary_success(self, mock_genai_client):
        import main
        mock_instance = MagicMock()
        mock_genai_client.return_value = mock_instance
        main._client = mock_instance

        mock_resp = MagicMock()
        mock_resp.text = "Hello!"
        mock_summary_resp = MagicMock()
        mock_summary_resp.text = "Summary: 1) Great standup progress!"
        mock_instance.models.generate_content.side_effect = [mock_resp, mock_summary_resp]

        with main.app.test_client() as client:
            client.post("/chat", json={"message": "I worked on CI/CD yesterday.", "session_id": "test-sum-1"})
            res = client.post("/summary", json={"session_id": "test-sum-1"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["summary"], "Summary: 1) Great standup progress!")

    @patch("google.genai.Client")
    def test_reset_endpoint_clears_history_and_preferences(self, mock_genai_client):
        import main
        main.CONVERSATIONS["test-session-123"] = []
        main.SESSION_PREFERENCES["test-session-123"] = {"pace": "slow", "focus": "general", "correction_style": "brief"}
        with main.app.test_client() as client:
            res = client.post("/reset", json={"session_id": "test-session-123"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["status"], "reset")
            self.assertEqual(data["session_id"], "test-session-123")
            self.assertNotIn("test-session-123", main.CONVERSATIONS)
            self.assertNotIn("test-session-123", main.SESSION_PREFERENCES)


if __name__ == "__main__":
    unittest.main()
