"""Run a real link scan against the caller's tracked documents; stdlib only."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def scan(binary, root, files, allow_test_loopback=False):
    """The loopback exception is used only by local HTTP regression tests."""
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GITHUB_TOKEN", "GH_TOKEN"} and not key.startswith("LYCHEE_")
    }
    with tempfile.TemporaryDirectory(prefix="entrotter-links-") as directory:
        output = Path(directory) / "report.json"
        command = [
            str(binary),
            "--config",
            os.devnull,
            "--no-progress",
            "--hidden",
            "--cache=false",
            "--insecure=false",
            "--include-fragments=full",
            "--max-concurrency",
            "4",
            "--host-concurrency",
            "2",
            "--host-request-interval",
            "300ms",
            "--max-retries",
            "1",
            "--timeout",
            "15",
            "--root-dir",
            str(root),
            "--format",
            "json",
            "--verbose",
            "--output",
            str(output),
        ]
        if not allow_test_loopback:
            command.append("--exclude-all-private")
        result = subprocess.run(
            [*command, "--", *files],
            cwd=root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300,
        )
        if not output.is_file():
            raise RuntimeError(f"Lychee produced no report (exit {result.returncode})")
        return result.returncode, json.loads(output.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.repo.resolve()
    binary = args.binary.resolve()
    version = subprocess.check_output([str(binary), "--version"], text=True).strip()
    if version != "lychee 0.24.2":
        raise SystemExit(f"Unreviewed checker version: {version}")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
    files = sorted(
        name
        for name in tracked.decode().split("\0")
        if Path(name).suffix.lower() in {".md", ".html", ".css"}
    )
    if not files:
        raise SystemExit("No tracked documents: refusing an empty green scan")
    code, report = scan(binary, root, files)
    failed = code != 0 or report["successful"] == 0
    evidence = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "worktree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=root)
        ),
        "checker": version,
        "checker_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "files": {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in files
        },
        "lychee_exit_code": code,
        "passed": not failed,
        "path_redaction": "Local checkout prefix replaced with /workspace/repository",
        "report": report,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(evidence, indent=2).replace(
        str(root), "/workspace/repository"
    )
    args.output.write_text(serialized + "\n")
    print(
        json.dumps(
            {
                "files": len(files),
                "passed": not failed,
                **{
                    key: report[key]
                    for key in (
                        "total",
                        "unique",
                        "successful",
                        "errors",
                        "timeouts",
                        "excludes",
                    )
                },
            }
        )
    )
    if failed:
        print(
            json.dumps(report["error_map"], indent=2).replace(
                str(root), "/workspace/repository"
            )
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
