# CLAUDE.md — ggiaur/english-coach

## Repository write authorization (owner's statement)

BJ (repository owner) stated on 2026-11-06 that Claude may write to this repository
(edit files, commit, push branches, open pull requests) **without asking again each time**,
and that this should be treated as a permanent authorization for **this repository only**.

This note records the owner's consent. It does not change the tool or connection permissions,
which are set in the Claude connection settings. It does not apply to other repositories.

## Working convention (Claude's proposal, not the owner's words)

- `main` is auto-deployed to Cloud Run through Cloud Build. Work on a branch and open a pull request.
  Merge when the owner has accepted the change.
- `docs/effortless-framework/SYSTEM.md` and `STUDENT_STATE.md` are loaded into the tutor prompt at runtime.
  Check their wording before merging.

## Project rules to follow

- Source of truth for teaching: `docs/effortless-framework/SYSTEM.md`.
- Lessons run in English only. Planning and evaluation with the owner may be in Hungarian.
- Never store song lyrics or other copyrighted text in the repository. Links and titles only.
- Bible text must be a real translation, word for word. The repository default is the World English Bible
  (public domain). Verify the wording against a source before writing it into a file.
- Progress is mastery-based (see `SYSTEM.md` section 24): move on when an item is secure, two full retries
  at most, then mark it pending and bring it back 3 to 7 days later in a different context.
- No vocabulary notebooks or word lists. Phrases in context, plus a short weekly written task.
  Phrase cards (phrase + one full sentence + a short grammar note) are allowed, and the owner may keep his own
  handwritten phrase notes in the same form (owner's statement, voice, 2026-11-07).
- No picture of Jesus anywhere (owner's statement, voice, 2026-11-07). Use a light symbol or text. Pictures of other
  people, qualities and scenes are allowed if they are original drawings or clearly free to use, with the source noted.
- Every new word is explained in English like a native dictionary and teacher: simple sentences, example, contrast,
  one question. No Hungarian translation inside the lesson. Each Bible-chapter person gets at least 5 simple sentences,
  traits, phrase cards and a picture (not for Jesus). Teacher's words are always marked apart from Bible text.
