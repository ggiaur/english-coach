# Effortless-style English Tutor Framework

This folder is the working specification for a consistent English-learning system.

## Goal

Build **usable spoken English** for:
- everyday situations,
- helping foreign visitors,
- travel and real-life conversation,
- IT work, support, meetings and professional communication.

The system is **input-first**, **English-only during lessons**, **chunk-based**, and inspired by the core principles of Effortless English without copying proprietary lesson material.

## Source of truth

`SYSTEM.md` is the pedagogical source of truth.

For ChatGPT Projects or any environment with persistent project instructions, copy the content of `PROJECT_INSTRUCTIONS.md` into the project instructions. Its main job is to force the tutor to read and follow `SYSTEM.md` rather than relying on memory.

## Files

- `PROJECT_INSTRUCTIONS.md` — short bootstrap instructions for every session.
- `SYSTEM.md` — complete teaching protocol.
- `LESSON_TEMPLATE.md` — required structure for every lesson.
- `LESSON_001_IT_HELPDESK.md` — first worked example.
- `STUDENT_STATE.md` — current level estimate, known issues and progress.
- `QUALITY_CHECKLIST.md` — pre-flight and live lesson checks.
- `CHANGELOG.md` — methodology changes.

## Core rule

**Do not test production before the input has been sufficiently established.**

The tutor must first make the language familiar and understandable through repeated, slow, varied English input. Only then may the learner be asked to produce it.
