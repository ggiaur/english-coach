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
    "review_items": [],
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


def _clean_review_items(items) -> list[dict[str, str]]:
    clean: list[dict[str, str]] = []
    if not isinstance(items, list):
        return clean
    for item in items[-8:]:
        if not isinstance(item, dict):
            continue
        phrase = str(item.get("phrase", "")).strip()[:240]
        correction = str(item.get("correction", "")).strip()[:240]
        note = str(item.get("note", "")).strip()[:240]
        if not phrase or not correction:
            continue
        clean.append({"phrase": phrase, "correction": correction, "note": note})
    return clean


def load_learner_state(session_id: str) -> dict:
    with _LOCK:
        state = _read_all().get(session_id, {})
    merged = deepcopy(_DEFAULT_STATE)
    if isinstance(state, dict):
        if isinstance(state.get("preferences"), dict):
            merged["preferences"].update(state["preferences"])
        if isinstance(state.get("session_summaries"), list):
            merged["session_summaries"] = [str(item) for item in state["session_summaries"][-5:]]
        merged["review_items"] = _clean_review_items(state.get("review_items", []))
        if isinstance(state.get("practice_count"), int):
            merged["practice_count"] = max(0, state["practice_count"])
    return merged


def save_learner_state(session_id: str, state: dict) -> None:
    clean = {
        "preferences": dict(state.get("preferences", {})),
        "session_summaries": [str(item) for item in state.get("session_summaries", [])[-5:]],
        "review_items": _clean_review_items(state.get("review_items", [])),
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
