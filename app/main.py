import os
import logging
import uuid

from flask import Flask, request, jsonify, session, send_from_directory
from google import genai
from google.genai import types

from coach_prompt import SYSTEM_PROMPT
from learner_state import load_learner_state, save_learner_state, delete_learner_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("english-coach")

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

VERSION = "1.4.0"

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

MAX_HISTORY_ITEMS = 40
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

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    return _client


CONVERSATIONS: dict[str, list[types.Content]] = {}
SESSION_PREFERENCES: dict[str, dict[str, str]] = {}


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
    if sid not in SESSION_PREFERENCES:
        saved = load_learner_state(sid).get("preferences", {})
        prefs = dict(DEFAULT_PREFERENCES)
        prefs.update({key: value for key, value in saved.items() if key in ALLOWED_PREFERENCES and value in ALLOWED_PREFERENCES[key]})
        SESSION_PREFERENCES[sid] = prefs
    return SESSION_PREFERENCES[sid]


def persist_preferences(sid: str) -> None:
    state = load_learner_state(sid)
    state["preferences"] = dict(get_preferences(sid))
    save_learner_state(sid, state)


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
    if not errors:
        persist_preferences(sid)
    return current, errors


def build_system_prompt(sid: str) -> str:
    prefs = get_preferences(sid)
    learner_state = load_learner_state(sid)
    summaries = learner_state.get("session_summaries", [])
    memory_section = ""
    if summaries:
        numbered = "\n".join(f"{index + 1}. {text}" for index, text in enumerate(summaries[-3:]))
        memory_section = (
            "\nLEARNER PROGRESS MEMORY FROM PREVIOUS SESSIONS:\n"
            f"{numbered}\n"
            "Use this memory actively: revisit recurring mistakes, recycle useful vocabulary, "
            "avoid unnecessary repetition of already-mastered material, and make today's practice "
            "a clear next step from the learner's previous work. Do not merely quote the memory back.\n"
        )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "SESSION PRACTICE PROFILE (follow unless the learner explicitly asks otherwise):\n"
        f"- pace: {prefs['pace']}\n"
        f"- focus: {prefs['focus']}\n"
        f"- correction style: {prefs['correction_style']}\n"
        f"- completed practice sessions: {learner_state.get('practice_count', 0)}\n"
        f"{memory_section}"
    )


def progress_payload(sid: str) -> dict:
    state = load_learner_state(sid)
    return {
        "session_id": sid,
        "practice_count": state.get("practice_count", 0),
        "recent_session_summaries": state.get("session_summaries", [])[-3:],
        "preferences": get_preferences(sid),
    }


@app.route("/", methods=["GET"])
def index():
    if os.path.exists(os.path.join(app.static_folder, "index.html")):
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"status": "ok", "service": "english-coach", "version": VERSION})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "english-coach", "version": VERSION})


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


@app.route("/progress", methods=["GET", "OPTIONS"])
def progress():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    sid = get_session_id({})
    return jsonify(progress_payload(sid))


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
    if len(history) > MAX_HISTORY_ITEMS:
        CONVERSATIONS[sid] = history[-MAX_HISTORY_ITEMS:]
        history = CONVERSATIONS[sid]

    try:
        response = get_client().models.generate_content(
            model=MODEL_NAME,
            contents=history,
            config=types.GenerateContentConfig(system_instruction=build_system_prompt(sid), temperature=0.8),
        )
        reply_text = getattr(response, "text", None) or "I'm sorry, I could not generate a response. Please try again."
        history.append(types.Content(role="model", parts=[types.Part(text=reply_text)]))
        return jsonify({"reply": reply_text, "session_id": sid, "preferences": get_preferences(sid), "progress": progress_payload(sid)})
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
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
        "Please provide the final session summary now: 1) Biggest improvement today, "
        "2) 2-3 key mistakes to remember with corrections, 3) 3-5 useful new IT expressions "
        "from our talk, 4) A small homework task for tomorrow."
    )
    temp_contents = list(history) + [types.Content(role="user", parts=[types.Part(text=summary_prompt)])]

    try:
        response = get_client().models.generate_content(
            model=MODEL_NAME,
            contents=temp_contents,
            config=types.GenerateContentConfig(system_instruction=build_system_prompt(sid), temperature=0.7),
        )
        summary_text = getattr(response, "text", None) or "Session summary generated."
        history.append(types.Content(role="user", parts=[types.Part(text=summary_prompt)]))
        history.append(types.Content(role="model", parts=[types.Part(text=summary_text)]))

        learner_state = load_learner_state(sid)
        summaries = learner_state.setdefault("session_summaries", [])
        summaries.append(summary_text)
        learner_state["session_summaries"] = summaries[-5:]
        learner_state["practice_count"] = learner_state.get("practice_count", 0) + 1
        learner_state["preferences"] = dict(get_preferences(sid))
        save_learner_state(sid, learner_state)

        return jsonify({"summary": summary_text, "session_id": sid, "preferences": get_preferences(sid), "progress": progress_payload(sid)})
    except Exception as e:
        logger.error(f"Error generating session summary: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate session summary", "details": str(e)}), 500


@app.route("/reset", methods=["POST", "OPTIONS"])
def reset():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    sid = get_session_id(data)
    clear_progress = bool(data.get("clear_progress", False))
    CONVERSATIONS.pop(sid, None)
    SESSION_PREFERENCES.pop(sid, None)
    if clear_progress:
        delete_learner_state(sid)
    else:
        learner_state = load_learner_state(sid)
        learner_state["preferences"] = {}
        save_learner_state(sid, learner_state)
    return jsonify({"status": "reset", "session_id": sid, "progress_preserved": not clear_progress})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
