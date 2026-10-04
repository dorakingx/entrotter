#!/usr/bin/env python3
"""Require pinned tools, hashed official-index locks and exact installed versions."""

import hashlib
from importlib.metadata import version
import json
import re

from quality_scope import ROOT


def requirements(text):
    records = {}
    for block in re.split(r"\n(?=[A-Za-z0-9])", text):
        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not lines:
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)(?:\s*\\)?$", lines[0])
        if not match:
            raise ValueError("Every dependency must have a single exact version pin")
        name = re.sub(r"[-_.]+", "-", match[1]).lower()
        if name in records:
            raise ValueError("Duplicate dependency")
        records[name] = (match[2], lines[1:])
    return records


def evaluate(inputs, lock):
    # The pip install gate also independently enforces hash syntax for every
    # transitive distribution. No URLs, editable installs or extra indexes.
    for text in [inputs, lock]:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("--") and not stripped.startswith("--hash=sha256:"):
                if stripped != "--index-url https://pypi.org/simple":
                    raise ValueError("Only the official package index is permitted")
    clean = "\n".join(
        line for line in lock.splitlines() if not line.startswith("--index-url")
    )
    declared, locked = requirements(inputs), requirements(clean)
    if not locked or not declared:
        raise ValueError("Empty dependency scope")
    for name, (pin, _) in declared.items():
        if name not in locked or locked[name][0] != pin:
            raise ValueError("Declared dependency missing or changed in lock: " + name)
    for name, (_, hashes) in locked.items():
        if not hashes or any(
            not re.fullmatch(r"--hash=sha256:[0-9a-f]{64}(?:\s*\\)?", h) for h in hashes
        ):
            raise ValueError("Missing or invalid wheel hashes: " + name)
    return {name: pin for name, (pin, _) in locked.items()}


def main():
    inputs = ROOT / "requirements-quality.in"
    lock = ROOT / "requirements-quality.txt"
    locked = evaluate(inputs.read_text(), lock.read_text())
    contract_inputs = ROOT / "requirements-contracts.in"
    contract_lock = ROOT / "requirements-contracts.txt"
    contracts = evaluate(contract_inputs.read_text(), contract_lock.read_text())
    if any(locked.get(name) != pin for name, pin in contracts.items()):
        raise ValueError("Contract-test dependency is outside the audited tool lock")
    installed = {name: version(name) for name in locked}
    if installed != locked:
        raise ValueError("Installed dependency versions differ from the reviewed lock")
    result = {
        "status": "passed",
        "declared_tools": list(requirements(inputs.read_text())),
        "audited_locked_packages": len(locked),
        "installed_versions": installed,
        "requirements_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "contract_test_versions": contracts,
        "contract_lock_sha256": hashlib.sha256(contract_lock.read_bytes()).hexdigest(),
        "local_runtime": "Local engine/SDK/CLI source pins are checked separately; no registry fallback",
        "limitations": [
            "Python package advisory scope only; browser/Node/native/host binaries are separate gates"
        ],
    }
    output = ROOT / ".quality/dependency-scope.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
