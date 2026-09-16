import json
import re
from copy import deepcopy
from datetime import datetime, timezone

PHASES = (
    "vocab_pass_1",
    "vocab_pass_2",
    "vocab_pass_3",
    "vocab_pass_4",
    "story_round_1",
    "story_round_2",
    "story_round_3",
    "story_round_4",
    "story_expansion_paraphrase",
    "story_expansion_contrasts",
    "story_expansion_teacher_qa",
    "story_expansion_viewpoint",
    "active_yes_no",
    "active_either_or",
    "active_wh",
    "active_short_answer",
    "pronunciation_repair",
    "guided_variation",
    "supported_roleplay",
    "freer_use",
    "recap",
)

STATE_RE = re.compile(r"\[\[LESSON_STATE:(\{.*?\})\]\]", re.DOTALL)
STUDENT_RE = re.compile(r"\[\[STUDENT_UPDATE:(\{.*?\})\]\]", re.DOTALL)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_lesson_state() -> dict:
    return {
        "phase": "vocab_pass_1",
        "topic": None,
        "practical_situation": None,
        "target_chunks": [],
        "story_text": None,
        "understood_chunks": [],
        "active_chunks": [],
        "recurring_errors": [],
        "pronunciation_issues": [],
        "next_priorities": [],
        "updated_at": _now(),
    }


def _dedupe_strings(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        if not isinstance(value, str):
            continue
        clean = value.strip()
        if clean and clean.casefold() not in seen:
            result.append(clean)
            seen.add(clean.casefold())
    return result


def merge_lesson_state(current: dict | None, update: dict | None) -> dict:
    state = deepcopy(current or default_lesson_state())
    update = update or {}

    phase = update.get("phase")
    if phase in PHASES:
        state["phase"] = phase

    for key in ("topic", "practical_situation", "story_text"):
        value = update.get(key)
        if isinstance(value, str) and value.strip():
            state[key] = value.strip()

    if "target_chunks" in update:
        state["target_chunks"] = _dedupe_strings(update.get("target_chunks"))

    for key in (
        "understood_chunks",
        "active_chunks",
        "recurring_errors",
        "pronunciation_issues",
        "next_priorities",
    ):
        if key in update:
            state[key] = _dedupe_strings([*(state.get(key) or []), *(update.get(key) or [])])

    state["updated_at"] = _now()
    return state


def extract_control_updates(text: str) -> tuple[str, dict | None, dict | None]:
    state_update = None
    student_update = None

    state_matches = list(STATE_RE.finditer(text or ""))
    if state_matches:
        try:
            state_update = json.loads(state_matches[-1].group(1))
        except json.JSONDecodeError:
            state_update = None

    student_matches = list(STUDENT_RE.finditer(text or ""))
    if student_matches:
        try:
            student_update = json.loads(student_matches[-1].group(1))
        except json.JSONDecodeError:
            student_update = None

    visible = STATE_RE.sub("", text or "")
    visible = STUDENT_RE.sub("", visible).strip()
    return visible, state_update, student_update


def state_for_prompt(state: dict) -> str:
    return json.dumps(state, ensure_ascii=False, indent=2)
