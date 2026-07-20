import os
import logging
import uuid

from flask import Flask, request, jsonify, session, send_from_directory
from google import genai
from google.genai import types

from coach_prompt import SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("english-coach")

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

# Initialize client lazily or with graceful fallback for testing/dev
_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
    return _client

# In-memory conversation store, keyed by session id.
CONVERSATIONS: dict[str, list[types.Content]] = {}


def get_session_id(req_data: dict = None) -> str:
    req_data = req_data or {}
    sid = req_data.get("session_id") or request.headers.get("X-Session-ID")
    if sid:
        return sid
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@app.route("/", methods=["GET"])
def index():
    if os.path.exists(os.path.join(app.static_folder, "index.html")):
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"status": "ok", "service": "english-coach"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "english-coach"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    sid = get_session_id(data)
    history = CONVERSATIONS.setdefault(sid, [])

    history.append(
        types.Content(role="user", parts=[types.Part(text=user_message)])
    )

    try:
        genai_client = get_client()
        response = genai_client.models.generate_content(
            model=MODEL_NAME,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.8,
            ),
        )

        reply_text = getattr(response, "text", None) or "I'm sorry, I could not generate a response. Please try again."

        history.append(
            types.Content(role="model", parts=[types.Part(text=reply_text)])
        )

        return jsonify({"reply": reply_text, "session_id": sid})
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        # Remove failed user message from history to keep it clean
        if history and history[-1].role == "user" and history[-1].parts[0].text == user_message:
            history.pop()
        return jsonify({"error": "Failed to communicate with AI model", "details": str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json(silent=True) or {}
    sid = get_session_id(data)
    CONVERSATIONS.pop(sid, None)
    return jsonify({"status": "reset", "session_id": sid})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

