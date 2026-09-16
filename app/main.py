import logging
import os
import uuid

from flask import Flask, jsonify, request, send_from_directory, session
from google import genai
from google.genai import types

from coach_prompt import SYSTEM_PROMPT
from framework_loader import build_framework_prompt, find_framework_dir
from lesson_state import (
    default_lesson_state,
    extract_control_updates,
    merge_lesson_state,
    state_for_prompt,
)
from state_store import SessionStateStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("english-coach")

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

VERSION = "2.0.0"

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

MAX_HISTORY_ITEMS = 40  # Max 20 pairs of messages to keep context focused and fast
MAX_MESSAGE_LENGTH = 4000

DEFAULT_PREFERENCES = {
    "pace": "four-pass",
    "focus": "it-support",
    "correction_style": "brief",
}
ALLOWED_PREFERENCES = {
    "pace": {"four-pass", "slow", "natural"},
    "focus": {"it-support", "general", "interview"},
    "correction_style": {"brief", "detailed"},
}

FRAMEWORK_PROMPT = build_framework_prompt()
FRAMEWORK_DIR = str(find_framework_dir())

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


# Conversation history and UI preferences remain lightweight session caches.
# Pedagogical lesson state is stored separately and can persist in Firestore.
CONVERSATIONS: dict[str, list[types.Content]] = {}
SESSION_PREFERENCES: dict[str, dict[str, str]] = {}
LESSON_STATES = SessionStateStore()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Session-ID, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def get_session_id(req_data: dict = None) -> str:
    req_data = req_data or {}
    sid = req_data.get("session_id") or request.headers.get("X-Session-ID")
    if sid:
        return sid
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


def get_preferences(sid: str) -> dict[str, str]:
    return SESSION_PREFERENCES.setdefault(sid, dict(DEFAULT_PREFERENCES))


def update_preferences(sid: str, payload: dict) -> tuple[dict[str, str], list[str]]:
    current = get_preferences(sid)
    errors = []
    for key, allowed_values in ALLOWED_PREFERENCES.items():
        if key not in payload:
            continue
        value = payload[key]
        if value not in allowed_values:
            errors.append(f"{key} must be one of: {', '.join(sorted(allowed_values))}")
            continue
        current[key] = value
    return current, errors


def get_lesson_state(sid: str) -> dict:
    state = LESSON_STATES.get(sid)
    if state is None:
        state = default_lesson_state()
        LESSON_STATES.set(sid, state)
    return state


def save_lesson_updates(sid: str, state_update: dict | None, student_update: dict | None) -> dict:
    state = get_lesson_state(sid)
    if state_update:
        state = merge_lesson_state(state, state_update)
    if student_update:
        state = merge_lesson_state(state, student_update)
    LESSON_STATES.set(sid, state)
    return state


def build_system_prompt(sid: str) -> str:
    prefs = get_preferences(sid)
    lesson_state = get_lesson_state(sid)
    return (
        f"{FRAMEWORK_PROMPT}\n\n"
        f"{SYSTEM_PROMPT}\n\n"
        "SESSION PRACTICE PROFILE (follow unless the learner explicitly asks otherwise):\n"
        f"- pace: {prefs['pace']}\n"
        f"- focus: {prefs['focus']}\n"
        f"- correction style: {prefs['correction_style']}\n\n"
        "CURRENT LESSON STATE — continue from here; do not restart without a learner request:\n"
        f"{state_for_prompt(lesson_state)}\n"
    )


def process_model_reply(sid: str, raw_text: str) -> tuple[str, dict]:
    visible_text, state_update, student_update = extract_control_updates(raw_text)
    lesson_state = save_lesson_updates(sid, state_update, student_update)
    if not visible_text:
        visible_text = "Please continue with the current lesson phase."
    return visible_text, lesson_state


@app.route("/", methods=["GET"])
def index():
    if os.path.exists(os.path.join(app.static_folder, "index.html")):
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"status": "ok", "service": "english-coach", "version": VERSION})


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "english-coach",
            "version": VERSION,
            "framework_loaded": True,
        }
    )


@app.route("/lesson-state", methods=["GET", "OPTIONS"])
def lesson_state_endpoint():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    sid = get_session_id({})
    return jsonify({"session_id": sid, "lesson_state": get_lesson_state(sid)})


@app.route("/preferences", methods=["GET", "POST", "OPTIONS"])
def preferences():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    sid = get_session_id(data)

    if request.method == "GET":
        return jsonify({"session_id": sid, "preferences": get_preferences(sid)})

    updated, errors = update_preferences(sid, data)
    if errors:
        return jsonify({"error": "invalid preferences", "details": errors}), 400
    return jsonify({"session_id": sid, "preferences": updated})


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    if len(user_message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"}), 400

    sid = get_session_id(data)
    history = CONVERSATIONS.setdefault(sid, [])

    history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    # Prune history if it exceeds limit (keep newest items). The persistent lesson
    # state still contains the pedagogical position and core lesson context.
    if len(history) > MAX_HISTORY_ITEMS:
        CONVERSATIONS[sid] = history[-MAX_HISTORY_ITEMS:]
        history = CONVERSATIONS[sid]

    try:
        genai_client = get_client()
        response = genai_client.models.generate_content(
            model=MODEL_NAME,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=build_system_prompt(sid),
                temperature=0.6,
            ),
        )

        raw_reply = getattr(response, "text", None) or ""
        reply_text, lesson_state = process_model_reply(sid, raw_reply)

        history.append(types.Content(role="model", parts=[types.Part(text=reply_text)]))

        return jsonify(
            {
                "reply": reply_text,
                "session_id": sid,
                "preferences": get_preferences(sid),
                "lesson_state": lesson_state,
            }
        )
    except Exception as e:
        logger.error("Error calling Gemini API: %s", e, exc_info=True)
        if history and history[-1].role == "user" and history[-1].parts[0].text == user_message:
            history.pop()
        return jsonify({"error": "Failed to communicate with AI model", "details": str(e)}), 500


@app.route("/summary", methods=["POST", "OPTIONS"])
def summary():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    sid = get_session_id(data)
    history = CONVERSATIONS.get(sid, [])

    if not history:
        return jsonify({"error": "No conversation history found for this session"}), 400

    summary_prompt = (
        "Provide a short session summary in English: 1) biggest improvement, "
        "2) 2-3 important corrected mistakes, 3) useful new chunks with simple English definitions, "
        "4) one small next-practice task. Keep it consistent with the learner state."
    )

    temp_contents = list(history) + [types.Content(role="user", parts=[types.Part(text=summary_prompt)])]

    try:
        genai_client = get_client()
        response = genai_client.models.generate_content(
            model=MODEL_NAME,
            contents=temp_contents,
            config=types.GenerateContentConfig(
                system_instruction=build_system_prompt(sid),
                temperature=0.5,
            ),
        )

        raw_summary = getattr(response, "text", None) or "Session summary generated."
        summary_text, lesson_state = process_model_reply(sid, raw_summary)

        history.append(types.Content(role="user", parts=[types.Part(text=summary_prompt)]))
        history.append(types.Content(role="model", parts=[types.Part(text=summary_text)]))

        return jsonify(
            {
                "summary": summary_text,
                "session_id": sid,
                "preferences": get_preferences(sid),
                "lesson_state": lesson_state,
            }
        )
    except Exception as e:
        logger.error("Error generating session summary: %s", e, exc_info=True)
        return jsonify({"error": "Failed to generate session summary", "details": str(e)}), 500


@app.route("/reset", methods=["POST", "OPTIONS"])
def reset():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    sid = get_session_id(data)
    CONVERSATIONS.pop(sid, None)
    SESSION_PREFERENCES.pop(sid, None)
    LESSON_STATES.delete(sid)
    return jsonify({"status": "reset", "session_id": sid})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
