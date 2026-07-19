import os
import uuid

from flask import Flask, request, jsonify, session
from google import genai
from google.genai import types

from coach_prompt import SYSTEM_PROMPT

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)

# In-memory conversation store, keyed by session id.
# Fine for a single-user personal project. Swap for Firestore later
# if you want persistence across restarts / multiple devices.
CONVERSATIONS: dict[str, list[types.Content]] = {}


def get_session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "english-coach"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    sid = get_session_id()
    history = CONVERSATIONS.setdefault(sid, [])

    history.append(
        types.Content(role="user", parts=[types.Part(text=user_message)])
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.8,
        ),
    )

    reply_text = response.text

    history.append(
        types.Content(role="model", parts=[types.Part(text=reply_text)])
    )

    return jsonify({"reply": reply_text, "session_id": sid})


@app.route("/reset", methods=["POST"])
def reset():
    sid = get_session_id()
    CONVERSATIONS.pop(sid, None)
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
