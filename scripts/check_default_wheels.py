import argparse
import email
import json
import hashlib
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Verify downloaded CI wheels against source and exercise the installed bounded default"
)
for name in ["engine", "sdk", "cli"]:
    parser.add_argument("--" + name + "-source", type=Path, required=True)
    parser.add_argument("--" + name + "-wheel", type=Path, required=True)
parser.add_argument("--reference", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
items = [
    (
        name,
        "entrotter_" + name,
        getattr(args, name + "_source").resolve(),
        getattr(args, name + "_wheel").resolve(),
    )
    for name in ["engine", "sdk", "cli"]
]
records = {}
for name, package, source, wheel in items:
    with zipfile.ZipFile(wheel) as archive:
        expected = {
            str(p.relative_to(source / "src")): p.read_bytes()
            for p in (source / "src" / package).glob("*.py")
        }
        actual = {
            p: archive.read(p)
            for p in archive.namelist()
            if p.startswith(package + "/") and p.endswith(".py")
        }
        if not actual == expected:
            raise AssertionError()
        metadata = email.message_from_bytes(
            archive.read(
                next(x for x in archive.namelist() if x.endswith(".dist-info/METADATA"))
            )
        )
        if not metadata["License-Expression"] == "MIT":
            raise AssertionError()
        requires = metadata.get_all("Requires-Dist", [])
        if not requires == (["entrotter-sdk==0.1.0"] if name == "cli" else []):
            raise AssertionError()
        records[name] = {
            "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "python_files_match_source": len(actual),
            "license": "MIT",
            "requires_dist": requires,
        }
with tempfile.TemporaryDirectory(prefix="entrotter-default-installed-") as directory:
    root = Path(directory)
    venv = root / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True
    )
    python = str(venv / "bin/python")
    subprocess.run(
        [
            python,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            *[str(x[3]) for x in items],
        ],
        check=True,
        capture_output=True,
    )
    verify = """import json,sys
from pathlib import Path
import entrotter_engine,entrotter_sdk,entrotter_cli
if not all(Path(x.__file__).is_relative_to(sys.prefix) for x in [entrotter_engine,entrotter_sdk,entrotter_cli]):
    raise AssertionError("Installed package escaped the fresh venv")
"""
    subprocess.run(
        [python, "-I", "-c", verify], check=True, capture_output=True, cwd=root
    )
    output = root / "report.json"
    env = dict(os.environ)
    if not (env.get("ENTROTTER_WORKER_IMAGE") and env.get("ENTROTTER_DOCKER_SOCKET")):
        raise AssertionError()
    cmd = [
        python,
        "-I",
        "-m",
        "entrotter_cli",
        "run",
        str(items[0][2] / "tests/data/fixture.json"),
        "--local",
        "-o",
        str(output),
    ]
    subprocess.run(cmd, env=env, cwd=root, check=True, capture_output=True, timeout=30)
    report = json.loads(output.read_bytes())
    if not report == json.loads(args.reference.read_bytes()):
        raise AssertionError()
    previous = output.read_bytes()
    env["ENTROTTER_DOCKER_SOCKET"] = str(root / "missing.sock")
    failed_run = subprocess.run(cmd, env=env, cwd=root, capture_output=True, timeout=10)
    if not (failed_run.returncode == 1 and output.read_bytes() == previous):
        raise AssertionError()
result = {
    "status": "passed",
    "wheels": records,
    "fresh_venv": True,
    "registry_access": False,
    "installation": "--no-index --no-deps; execution uses Python -I and confirms module paths inside venv",
    "default_local_cli_artifact_id": report["artifact_id"],
    "full_public_report_equality": True,
    "missing_worker_preserves_existing_export": True,
    "check_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
