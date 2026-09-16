import os
from pathlib import Path

REQUIRED_FILES = (
    "PROJECT_INSTRUCTIONS.md",
    "SYSTEM.md",
    "STUDENT_STATE.md",
    "LESSON_TEMPLATE.md",
    "QUALITY_CHECKLIST.md",
)


def _candidate_dirs() -> list[Path]:
    candidates: list[Path] = []
    env_dir = os.environ.get("EFFORTLESS_FRAMEWORK_DIR")
    if env_dir:
        candidates.append(Path(env_dir))

    here = Path(__file__).resolve().parent
    candidates.extend(
        [
            here / "framework",  # Cloud Run image path copied by Dockerfile
            here.parent / "docs" / "effortless-framework",  # repo-root execution
            here.parent.parent / "docs" / "effortless-framework",  # app/ execution variants
        ]
    )
    return candidates


def find_framework_dir() -> Path:
    for directory in _candidate_dirs():
        if directory.is_dir() and all((directory / name).is_file() for name in REQUIRED_FILES):
            return directory
    searched = ", ".join(str(p) for p in _candidate_dirs())
    raise FileNotFoundError(f"Effortless framework files not found. Searched: {searched}")


def load_framework_files() -> dict[str, str]:
    directory = find_framework_dir()
    return {
        name: (directory / name).read_text(encoding="utf-8")
        for name in REQUIRED_FILES
    }


def build_framework_prompt() -> str:
    files = load_framework_files()
    sections = [
        "EFFORTLESS ENGLISH FRAMEWORK — AUTHORITATIVE PROJECT FILES",
        "The following files are the source of truth. If older runtime instructions conflict with them, these files win.",
    ]
    for name in REQUIRED_FILES:
        sections.append(f"\n===== {name} =====\n{files[name]}")
    return "\n".join(sections)
