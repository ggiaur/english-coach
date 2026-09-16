import logging
import os
import threading
from copy import deepcopy

logger = logging.getLogger("english-coach.state")


class SessionStateStore:
    """Persistent lesson-state storage with safe in-memory fallback.

    STATE_BACKEND=firestore forces Firestore attempts.
    STATE_BACKEND=memory disables Firestore.
    STATE_BACKEND=auto (default) uses Firestore when GCP_PROJECT_ID is present.
    """

    def __init__(self):
        self._memory: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._firestore = None
        self._collection = os.environ.get("STATE_COLLECTION", "english_coach_sessions")
        backend = os.environ.get("STATE_BACKEND", "auto").lower()

        should_try_firestore = backend == "firestore" or (
            backend == "auto" and bool(os.environ.get("GCP_PROJECT_ID"))
        )
        if should_try_firestore:
            try:
                from google.cloud import firestore

                self._firestore = firestore.Client(project=os.environ.get("GCP_PROJECT_ID"))
                logger.info("Lesson-state backend: Firestore")
            except Exception as exc:  # pragma: no cover - depends on GCP runtime
                logger.warning("Firestore unavailable; using in-memory state: %s", exc)
                self._firestore = None
        else:
            logger.info("Lesson-state backend: in-memory")

    def _memory_get(self, sid: str):
        with self._lock:
            value = self._memory.get(sid)
            return deepcopy(value) if value is not None else None

    def _memory_set(self, sid: str, value: dict):
        with self._lock:
            self._memory[sid] = deepcopy(value)

    def _memory_delete(self, sid: str):
        with self._lock:
            self._memory.pop(sid, None)

    def get(self, sid: str):
        if self._firestore is not None:
            try:
                snap = self._firestore.collection(self._collection).document(sid).get()
                if snap.exists:
                    value = snap.to_dict()
                    self._memory_set(sid, value)
                    return value
            except Exception as exc:  # pragma: no cover - depends on GCP runtime
                logger.warning("Firestore read failed; disabling Firestore for this process: %s", exc)
                self._firestore = None
        return self._memory_get(sid)

    def set(self, sid: str, value: dict):
        self._memory_set(sid, value)
        if self._firestore is not None:
            try:
                self._firestore.collection(self._collection).document(sid).set(value)
            except Exception as exc:  # pragma: no cover - depends on GCP runtime
                logger.warning("Firestore write failed; disabling Firestore for this process: %s", exc)
                self._firestore = None

    def delete(self, sid: str):
        self._memory_delete(sid)
        if self._firestore is not None:
            try:
                self._firestore.collection(self._collection).document(sid).delete()
            except Exception as exc:  # pragma: no cover - depends on GCP runtime
                logger.warning("Firestore delete failed; disabling Firestore for this process: %s", exc)
                self._firestore = None
