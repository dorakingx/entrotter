"""Verify a bundled synthetic report or run one scenario against a local API."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

from entrotter_sdk import Client, RunResult


FIXTURE = Path(__file__).parent / "fixtures" / "synthetic-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", help="Optional local API origin, e.g. http://127.0.0.1:8787")
    parser.add_argument("--scenario", type=Path, help="Scenario JSON for the optional API run")
    args = parser.parse_args()

    if bool(args.api) != bool(args.scenario):
        parser.error("--api and --scenario must be provided together")

    if args.api:
        scenario = json.loads(args.scenario.read_text(encoding="utf-8"))
        result = Client(args.api, token=os.getenv("ENTROTTER_API_TOKEN")).run(scenario)
        report = result.report
    else:
        report = json.loads(FIXTURE.read_text(encoding="utf-8"))

    parsed = RunResult.parse(report)
    with tempfile.TemporaryDirectory(prefix="entrotter-sdk-example-") as temp_dir:
        output = Path(temp_dir) / "report.json"
        output.write_text(json.dumps(parsed.report, indent=2) + "\n", encoding="utf-8")
        round_tripped = RunResult.parse(json.loads(output.read_text(encoding="utf-8")))

    print(f"Verified {round_tripped.mode} artifact: {round_tripped.artifact_id}")
    print("Hash integrity passed; this does not establish model correctness or financial safety.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
