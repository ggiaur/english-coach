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
            self.assertEqual(res.get_json(), {"status": "ok", "service": "english-coach"})

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

