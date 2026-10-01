#!/usr/bin/env python3
"""Regenerate the public synthetic examples from source, not handwritten numbers."""

import json
from pathlib import Path
import sys


def main():
    workspace = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(workspace / "engine/src"))
    from entrotter_engine.runner import run
    from entrotter_engine.artifact import write_report

    for fixture in sorted((workspace / "scenarios/fixtures").glob("*.json")):
        result = run(json.loads(fixture.read_text()))
        write_report(result, workspace / "entrotter.github.io/reports" / fixture.name)
        print(fixture.name, result["artifact_id"])


if __name__ == "__main__":
    main()
