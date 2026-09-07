import json
import os
import threading
from copy import deepcopy
from pathlib import Path


STATE_PATH = Path(os.environ.get("LEARNER_STATE_PATH", "/tmp/english-coach-learner-state.json"))
_LOCK = threading.Lock()
_DEFAULT_STATE = {
    "preferences": {},
    "session_summaries": [],
    "practice_count": 0,
}


def _read_all() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        with STATE_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_all(data: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(tmp_path, STATE_PATH)


def load_learner_state(session_id: str) -> dict:
    with _LOCK:
        state = _read_all().get(session_id, {})
    merged = deepcopy(_DEFAULT_STATE)
    if isinstance(state, dict):
        if isinstance(state.get("preferences"), dict):
            merged["preferences"].update(state["preferences"])
        if isinstance(state.get("session_summaries"), list):
            merged["session_summaries"] = [str(item) for item in state["session_summaries"][-5:]]
        if isinstance(state.get("practice_count"), int):
            merged["practice_count"] = max(0, state["practice_count"])
    return merged


def save_learner_state(session_id: str, state: dict) -> None:
    clean = {
        "preferences": dict(state.get("preferences", {})),
        "session_summaries": [str(item) for item in state.get("session_summaries", [])[-5:]],
        "practice_count": max(0, int(state.get("practice_count", 0))),
    }
    with _LOCK:
        all_states = _read_all()
        all_states[session_id] = clean
        _write_all(all_states)


def delete_learner_state(session_id: str) -> None:
    with _LOCK:
        all_states = _read_all()
        if session_id in all_states:
            del all_states[session_id]
            _write_all(all_states)
