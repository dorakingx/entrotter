#!/usr/bin/env python3
"""Stage explicitly declared static files; no GitHub/Org/service mutations."""

import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "website"
PUBLIC_ROOT_FILES = {
    "index.html",
    "404.html",
    "style.css",
    "app.js",
    "comparison.mjs",
    "report-validation.mjs",
    "trace-report.mjs",
    "trace-comparison.mjs",
    "trace-viewer.mjs",
    "observed-trace.mjs",
    "position-report.mjs",
    ".nojekyll",
    "LICENSE",
}


def stage(output: Path) -> list[str]:
    files = json.loads((SITE / "public-files.json").read_text())
    if not isinstance(files, list) or len(files) != len(set(files)):
        raise ValueError("Public-file manifest must be a unique list")
    if not PUBLIC_ROOT_FILES.issubset(files):
        raise ValueError("Public-file manifest omits a required viewer file")
    sources = []
    for name in files:
        if not isinstance(name, str):
            raise ValueError("Public-file names must be strings")
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or str(path) != name:
            raise ValueError("Public-file names must be canonical relative paths")
        if name not in PUBLIC_ROOT_FILES and (
            path.parts[0] not in {"assets", "reports", "schemas"}
            or any(part.startswith(".") for part in path.parts)
        ):
            raise ValueError("File is outside the declared static publication scope")
        source = SITE / path
        if not source.is_file() or any(
            (SITE.joinpath(*path.parts[:i])).is_symlink()
            for i in range(1, len(path.parts) + 1)
        ):
            raise ValueError(
                "Public files must be regular files without symlink parents"
            )
        sources.append((name, source))
    output = output.resolve()
    if SITE.is_relative_to(output):
        raise ValueError("Output cannot replace the website or its parent")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Choose a new or empty output directory")
    output.mkdir(parents=True, exist_ok=True)
    for name, source in sources:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("website/_site"))
    parser.add_argument("--apply", action="store_true", help="retired legacy option")
    parser.add_argument(
        "--skip-issues", action="store_true", help="retired legacy option"
    )
    args = parser.parse_args()
    if args.apply or args.skip_issues:
        parser.error(
            "Legacy Org/repository/Pages bootstrap is retired; see docs/HOSTING.md"
        )
    output = args.output if args.output.is_absolute() else ROOT / args.output
    print(f"Staged {len(stage(output))} static files in {output}")


if __name__ == "__main__":
    main()
