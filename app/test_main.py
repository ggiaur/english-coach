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
        self.assertEqual(main.MODEL_NAME, "gemini-2.0-flash")

    @patch("google.genai.Client")
    def test_health_endpoint(self, mock_genai_client):
        import main
        with main.app.test_client() as client:
            res = client.get("/health")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.get_json(), {"status": "ok", "service": "english-coach", "version": "1.2.0"})

    @patch("google.genai.Client")
    def test_chat_endpoint_uses_correct_model(self, mock_genai_client):
        import main
        mock_instance = MagicMock()
        mock_genai_client.return_value = mock_instance
        main._client = mock_instance
        mock_response = MagicMock()
        mock_response.text = "Hello! Ready for standup practice?"
        mock_instance.models.generate_content.return_value = mock_response

        with main.app.test_client() as client:
            res = client.post("/chat", json={"message": "Hi!", "session_id": "test-session-123"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["reply"], "Hello! Ready for standup practice?")
            self.assertEqual(data["session_id"], "test-session-123")

            mock_instance.models.generate_content.assert_called_once()
            call_kwargs = mock_instance.models.generate_content.call_args.kwargs
            self.assertEqual(call_kwargs.get("model"), "gemini-2.0-flash")

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
            # First send a chat message
            client.post("/chat", json={"message": "I worked on CI/CD yesterday.", "session_id": "test-sum-1"})
            # Request summary
            res = client.post("/summary", json={"session_id": "test-sum-1"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["summary"], "Summary: 1) Great standup progress!")

    @patch("google.genai.Client")
    def test_reset_endpoint(self, mock_genai_client):
        import main
        with main.app.test_client() as client:
            res = client.post("/reset", json={"session_id": "test-session-123"})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["status"], "reset")
            self.assertEqual(data["session_id"], "test-session-123")

if __name__ == "__main__":
    unittest.main()


