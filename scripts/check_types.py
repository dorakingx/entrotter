#!/usr/bin/env python3
"""Check every production script against its actual pinned dependency variant.

The three existing optional-pipe/selector diagnostics in the byte-frozen model
adapter remain visible, source-bound and narrowly reviewed; no ignores or stubs.
"""

import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from quality_scope import ROOT, production_files

AGENT_FILES = [
    "benchmark_agent",
    "benchmark_direct",
    "check_agent",
    "check_historical",
    "codex_policy",
    "direct_anvil_case",
    "export_reports",
]
WORKER_FILES = ["check_host_limits", "check_export_budget"]


def evaluate(output, returncode, expected):
    errors = [line for line in output.splitlines() if ": error: " in line]
    allowed = [finding["diagnostic"] for finding in expected]
    if any(len(finding.get("reason", "")) < 40 for finding in expected):
        raise ValueError("Each existing type diagnostic needs a concrete rationale")
    if returncode != (1 if errors else 0) or sorted(errors) != sorted(allowed):
        raise ValueError("Type diagnostics changed or mypy failed; inspect full output")
    if (
        not re.search(r"(?:checked|checking) \d+ source files?", output)
        and "Success: no issues found in" not in output
    ):
        raise ValueError("Missing type-check coverage result")
    return len(errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["agent-engine", "worker-engine", "sdk", "cli"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    policy = json.loads((ROOT / "quality-inputs.json").read_text())
    if version("mypy") != policy["mypy_version"]:
        raise ValueError("Mypy version differs from reviewed policy")
    sources = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in production_files()
    }
    for name, digest in policy["frozen_sources"].items():
        if sources.get(name) != digest:
            raise ValueError("Frozen provider source changed")
    dependencies = {}
    paths = {}
    for name, pin in policy["dependency_commits"].items():
        path = getattr(args, name.replace("-", "_")).resolve()
        commit = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(path), "status", "--porcelain"], text=True, timeout=10
        ).strip()
        if commit != pin or dirty:
            raise ValueError(
                "Type dependency must be clean at the declared immutable pin: " + name
            )
        paths[name] = path / "src"
        dependencies[name] = commit
    agents = ["scripts/" + name + ".py" for name in AGENT_FILES]
    workers = ["scripts/" + name + ".py" for name in WORKER_FILES]
    general = sorted(set(sources) - set(agents) - set(workers))
    groups = {
        "agent": (agents, [paths["agent-engine"]]),
        "worker": (workers, [paths["worker-engine"], paths["sdk"], paths["cli"]]),
        "general": (general, []),
    }
    output = ROOT / ".quality/types"
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for name, (files, imports) in groups.items():
        environment = {
            k: v
            for k, v in os.environ.items()
            if k not in {"MYPYPATH", "PYTHONPATH", "PYTHONOPTIMIZE"}
        }
        environment["MYPYPATH"] = os.pathsep.join(map(str, imports))
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--config-file",
                str(ROOT / "pyproject.toml"),
                "--no-pretty",
                "--no-color-output",
                *files,
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )
        full = process.stdout + process.stderr
        (output / (name + ".log")).write_text(full)
        expected = policy["frozen_type_findings"] if name == "agent" else []
        count = evaluate(full, process.returncode, expected)
        results.append(
            {
                "group": name,
                "files": files,
                "exit_code": process.returncode,
                "reviewed_diagnostics": count,
            }
        )
    result = {
        "status": "passed_with_explicit_frozen_diagnostics",
        "mypy_version": version("mypy"),
        "sources_sha256": sources,
        "dependency_commits": dependencies,
        "groups": results,
        "limitations": [
            "Normal mypy with unannotated bodies, not strict typing or runtime JSON validation",
            "Imported external packages provide types; their implementation is checked in owning repositories",
            "Three frozen-provider pipe/selector diagnostics are retained; independent review required",
        ],
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
