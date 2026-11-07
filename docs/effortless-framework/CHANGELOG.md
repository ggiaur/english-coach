# CHANGELOG.md

## 0.5 — 2026-11-07 (később)

- `/learn` site: John 9 verses 1 to 5 (verbatim WEB), 8 scenes, 5 characters, 36 phrase cards, 39 textbook entries, 20 original pictures (none of Jesus), audio buttons with four speeds.
- Optional password (`APP_PASSWORD`), `/tts` proxy to a local Piper container, `docker-compose.yml`, `DOCKER.md`.
- `SYSTEM.md` section 29 (content rules), project rules in `CLAUDE.md` (no picture of Jesus, phrase cards allowed).
- Second 2026-11-07 session recorded (`PROGRESS_LOG.md`, `ITEM_TRACKER.md`, `STUDENT_STATE.md`).

## 0.4 — 2026-11-07

- `TASK_LANGUAGE.md` and `SYSTEM.md` section 28: 8 task words, one instruction and one question per turn, task rescue (proposal).
- `Say:` replaced by `Repeat:` in lesson and script files; L1 story shortened.
- John 9 voice session recorded (`PROGRESS_LOG.md`, `ITEM_TRACKER.md`, `STUDENT_STATE.md`).
- Progress web page at `/progress` (`app/static/progress/`), direct song links in `LISTENING_LINKS.md`, unit test for the page.

## 0.3 — 2026-11-06

Changes after the first Bible-track voice session and placement.

Added:
- `SYSTEM.md` sections 20 to 24: task clarity and turn design, voice mode, Bible track, listening lane (songs and audio), mastery-based progression.
- Portable tutor kit: `PORTABLE_TUTOR_PROMPT.md`, `SESSION_SCRIPTS.md`, `STATE_PROTOCOL.md`, `PROGRESS_LOG.md`, `ITEM_TRACKER.md`.
- Fully scripted week 1: `LESSONS_W01_IT.md`, `LESSONS_W01_BIBLE_AND_SONGS.md`, `LESSON_BIBLE_JOHN9_01.md`.
- Measurement: `ASSESSMENT_KIT.md`, `QUESTION_GYM.md`. Monthly plan: `MONTHLY_PLAN_M01.md`. Links: `LISTENING_LINKS.md`. How-to: `HASZNALAT.md`.
- Root `CLAUDE.md` with the owner's standing write authorization for this repository.
- `DAILY_SPEAKING.md`: daily 2 to 3 minutes of free speaking with end-of-session feedback, and the synonym and collocation phrase bank. `SYSTEM.md` sections 25 to 27 (daily speaking, load and timing review, portability).
- Song lane shortened to 10 minutes per weekday (2 phrases per song); weekly total about 6 hours.
- Load and timing review every two weeks (`ASSESSMENT_KIT.md` section 3); `SESSION RECORD` gains `time_of_day`, `freshness_1_5`, `minutes_actual`, `daily_speaking`.
- Decisions recorded: WEB is the repository Bible text; weekly free conversation stays (10 minutes) next to the daily practice.
- `PLACEMENT_BIBLE_001.md`: result record and a graded test bank (v2).
- `WEEKLY_PLAN_W01.md`: first weekly plan (draft, pending learner approval).
- Bible-track level and new preferences in `STUDENT_STATE.md`.

Fixed (system-level causes):
- Long listening blocks with no learner task.
- Answers given together with the question.
- Bible text simplified into a different wording.
- Placement test items not graded by difficulty.

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
