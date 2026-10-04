"""Discover all executable Python tooling, excluding tests and archived evidence."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def production_files(root=ROOT):
    paths = list((root / "scripts").rglob("*.py"))
    paths += [
        p for p in (root / ".github").rglob("*.py") if not p.name.startswith("test_")
    ]
    files = sorted(p.relative_to(root).as_posix() for p in paths)
    if not files:
        raise ValueError("Empty production source scope")
    return files
