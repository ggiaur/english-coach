# CHANGELOG.md

## 0.2 — 2026-09-16

Runtime implementation aligned with the written Effortless framework.

Added:
- Runtime loading of `SYSTEM.md`, `STUDENT_STATE.md`, `LESSON_TEMPLATE.md`, `QUALITY_CHECKLIST.md`, and project bootstrap instructions.
- Explicit persisted lesson phase state so the tutor resumes instead of restarting or asking what comes next.
- Stored topic, practical situation, target chunks, story text, understood/active chunks, recurring errors, pronunciation issues, and next priorities.
- Firestore-backed state with safe in-memory fallback.
- Hidden model control markers for lesson phase and learner-progress updates.
- `/lesson-state` inspection endpoint.
- Phase-aware TTS pacing: very slow, very slow, medium, then clear natural speed.
- Unit tests in Cloud Build before deployment.
- Current learner progress from the account-lockout/password-reset practice.

Changed:
- Removed the conflicting older runtime coaching assumptions (including premature production pressure and the older level estimate) from `coach_prompt.py`.
- Runtime now treats the written framework as authoritative.
- Reset now also clears lesson state.

## 0.1 — 2026-09-03

Initial methodology consolidated from the learning-design discussion.

Added:
- English-only lesson rule.
- Input-before-output principle.
- Chunk-first vocabulary policy.
- Multi-angle English-only vocabulary explanation.
- Four-speed vocabulary repetition.
- Automatic four-round story listening sequence.
- Two very slow story rounds with long sentence pauses.
- Medium and natural-speed story rounds.
- No interruptions during four story rounds.
- Story expansion before learner testing.
- Paraphrases, contrasts, negatives and teacher-answered questions.
- Alternate viewpoint.
- Gradual question difficulty.
- Short English correction cues.
- Pronunciation repair ladder.
- Anti-idle-pause rule.
- Written source-of-truth design so the system does not rely on tutor memory.
