#!/usr/bin/env python3
"""Verify actual CLI -> SDK -> bounded local API behavior, including real Anvil.

No archive endpoint, wallet, model call or external service is used. Quota-error
checks deliberately lower the saved-file count to two; engine unit tests also
exercise the production 128-file and 128-MiB defaults.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time

import entrotter_cli.main as cli_module
import entrotter_engine.api as api_module
import entrotter_sdk.client as sdk_module
from entrotter_engine.api import EngineServer
from entrotter_engine.store import ArtifactStore
from entrotter_sdk import Client, ClientError, RunResult


class ObservedServer(EngineServer):
    def __init__(self, *args, **kwargs):
        self.activity = threading.Condition()
        self.active = 0
        super().__init__(*args, **kwargs)

    def process_request_thread(self, request, address):
        with self.activity:
            self.active += 1
            self.activity.notify_all()
        try:
            super().process_request_thread(request, address)
        finally:
            with self.activity:
                self.active -= 1
                self.activity.notify_all()

    def wait_active(self, count):
        with self.activity:
            if not self.activity.wait_for(lambda: self.active == count, timeout=3):
                raise RuntimeError("Expected handler count was not observed")


def revision(module):
    root = Path(module.__file__).resolve().parents[2]
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain"], text=True
    ).strip()
    if dirty:
        raise RuntimeError(f"Tested dependency {root.name} must be clean")
    return commit


def check_default_worker(engine, inputs, root, manifest_path):
    """Real public entrypoints, source-bound image, and unavailable-daemon rejection."""
    manifest = json.loads(manifest_path.read_text())
    if not os.environ.get("ENTROTTER_WORKER_IMAGE") == manifest["image_id"]:
        raise AssertionError()
    sources = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (engine / "src/entrotter_engine").glob("*.py")
    }
    sources["Dockerfile"] = hashlib.sha256(
        (engine / "container/Dockerfile").read_bytes()
    ).hexdigest()
    if not sources == manifest["source_files"]:
        raise AssertionError()
    if (
        not hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
        == manifest["source_digest"]
    ):
        raise AssertionError()
    from entrotter_engine.isolated import client, verify_daemon

    with client() as prefix:
        info = verify_daemon(prefix)
        label = subprocess.check_output(
            [
                *prefix,
                "image",
                "inspect",
                "--format",
                '{{index .Config.Labels "org.entrotter.source"}}',
                manifest["image_id"],
            ],
            text=True,
            timeout=10,
        ).strip()
    if not label == manifest["source_digest"]:
        raise AssertionError()
    target = root / "local-default.json"
    ids = {}
    for name, source in inputs.items():
        base = [
            sys.executable,
            "-m",
            "entrotter_cli",
            "run",
            str(source),
            "--local",
            "-o",
            str(target),
        ]
        completed = subprocess.run(base, capture_output=True, text=True, timeout=45)
        if not completed.returncode == 0:
            raise AssertionError("Default local CLI execution failed")
        report = RunResult.parse(json.loads(target.read_bytes())).report
        ids[name] = report["artifact_id"]
        previous = target.read_bytes()
        missing = {
            **os.environ,
            "ENTROTTER_DOCKER_SOCKET": str(root / "missing.sock"),
            "ENTROTTER_WORKER_IMAGE": "",
        }
        rejected = subprocess.run(
            base, env=missing, capture_output=True, text=True, timeout=10
        )
        if not (rejected.returncode == 1 and "Traceback" not in rejected.stderr):
            raise AssertionError()
        if not target.read_bytes() == previous:
            raise AssertionError()
        if name == "fixture":
            native = subprocess.run(
                [*base, "--native"],
                env=missing,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if not native.returncode == 0:
                raise AssertionError("Explicit trusted native control failed")
            if not json.loads(target.read_bytes()) == report:
                raise AssertionError()
    return {
        "image_id": manifest["image_id"],
        "image_source_digest": manifest["source_digest"],
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "actual_source_matches_image_manifest_and_label": True,
        "cgroup_version": info["CgroupVersion"],
        "artifact_ids": ids,
        "local_cli_without_mode_opt_in": True,
        "missing_worker_fails_without_export_replacement": True,
        "explicit_native_fixture_matches": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--worker-manifest",
        type=Path,
        help="Verify the bounded default with this built image manifest",
    )
    args = parser.parse_args()
    pins = {
        "engine": revision(api_module),
        "sdk-python": revision(sdk_module),
        "cli": revision(cli_module),
    }
    engine = Path(api_module.__file__).resolve().parents[2]
    inputs = {name: engine / f"tests/data/{name}.json" for name in ["fixture", "local"]}
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="entrotter-host-check-") as directory:
        root = Path(directory)
        worker = (
            check_default_worker(engine, inputs, root, args.worker_manifest)
            if args.worker_manifest
            else None
        )
        server = ObservedServer(0, output=root / "saved")
        server.store = ArtifactStore(root / "saved", max_files=2)
        calls = []
        actual_runner = server.runner

        def counted_run(scenario):
            calls.append(scenario["mode"])
            return actual_runner(scenario)

        server.runner = counted_run
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        client = Client(url, timeout=5)
        output = root / "export.json"

        def cli_run(path):
            return subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "entrotter_cli",
                    "run",
                    str(path),
                    "--api",
                    url,
                    "-o",
                    str(output),
                ],
                capture_output=True,
                text=True,
                timeout=45,
            )

        reports = {}
        sockets = []
        try:
            for name, path in inputs.items():
                process = cli_run(path)
                if process.returncode != 0:
                    raise RuntimeError("CLI/API integration run failed")
                report = RunResult.parse(json.loads(output.read_bytes())).report
                if not client.get(report["artifact_id"]).report == report:
                    raise AssertionError()
                if (
                    not json.loads(
                        (
                            root / "saved" / (report["artifact_id"] + ".json")
                        ).read_bytes()
                    )
                    == report
                ):
                    raise AssertionError()
                reports[name] = report
            if worker:
                # Independent standalone CLI and API process paths must share the
                # same daemon slot. This is a real idle bounded Docker worker.
                from entrotter_engine.isolated import (
                    client as docker_client,
                    worker_args,
                    WORKER_NAME,
                )

                previous = output.read_bytes()
                before = len(calls)
                with docker_client() as prefix:
                    command = worker_args(prefix, worker["image_id"], WORKER_NAME)
                    command.insert(-1, "--detach")
                    incumbent = subprocess.check_output(
                        command, stdin=subprocess.DEVNULL, text=True, timeout=10
                    ).strip()
                    try:
                        local_busy = subprocess.run(
                            [
                                sys.executable,
                                "-m",
                                "entrotter_cli",
                                "run",
                                str(inputs["fixture"]),
                                "--local",
                                "-o",
                                str(output),
                            ],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        if not (
                            local_busy.returncode == 1
                            and "busy" in local_busy.stderr.lower()
                        ):
                            raise AssertionError()
                        api_busy = cli_run(inputs["fixture"])
                        if not (
                            api_busy.returncode == 1 and "HTTP 429" in api_busy.stderr
                        ):
                            raise AssertionError()
                        # SDK intentionally omits server error bodies; the engine
                        # real-HTTP suite checks the exact worker_busy code.
                        if "not automatically retried" not in api_busy.stderr:
                            raise AssertionError()
                        if not "Traceback" not in local_busy.stderr + api_busy.stderr:
                            raise AssertionError()
                        if not output.read_bytes() == previous:
                            raise AssertionError()
                        if not len(calls) == before + 1:
                            raise AssertionError()  # One POST, no automatic retry.
                        if not len(list((root / "saved").glob("*.json"))) == 2:
                            raise AssertionError()
                        state = subprocess.check_output(
                            [
                                *prefix,
                                "inspect",
                                "--format",
                                "{{.Id}} {{.State.Running}}",
                                WORKER_NAME,
                            ],
                            text=True,
                            timeout=10,
                        ).strip()
                        if not state == incumbent + " true":
                            raise AssertionError(
                                "Rejected caller removed incumbent worker"
                            )
                    finally:
                        subprocess.run(
                            [*prefix, "rm", "--force", incumbent],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=10,
                        )
                if not cli_run(inputs["fixture"]).returncode == 0:
                    raise AssertionError()
                worker["daemon_shared_admission"] = {
                    "standalone_local_cli_rejected": True,
                    "cli_sdk_api_429": True,
                    "api_posts": len(calls) - before - 1,
                    "existing_export_and_incumbent_preserved": True,
                    "successful_run_after_release": True,
                    "scope": "one container worker per configured daemon; no native/host-process/storage bound",
                }
            if not reports["fixture"]["mode"] == "fixture":
                raise AssertionError()
            if not reports["local"]["mode"] == "evm-local":
                raise AssertionError()
            if not [
                step["status"] for step in reports["local"]["candidate"]["trace"]
            ] == ["success", "reverted"]:
                raise AssertionError()
            if not all(
                (step["receipt"] for step in reports["local"]["candidate"]["trace"])
            ):
                raise AssertionError()
            if not cli_run(inputs["fixture"]).returncode == 0:
                raise AssertionError()  # Idempotent at capacity.
            previous = output.read_bytes()
            changed = json.loads(inputs["fixture"].read_text())
            changed["title"] = "Distinct synthetic quota probe"
            probe = root / "quota-probe.json"
            probe.write_text(json.dumps(changed))
            before = len(calls)
            rejected = cli_run(probe)
            if not (rejected.returncode == 1 and "HTTP 507" in rejected.stderr):
                raise AssertionError()
            if not "Traceback" not in rejected.stderr:
                raise AssertionError()
            if not len(calls) - before == 1:
                raise AssertionError()  # No automatic POST retries.
            if not output.read_bytes() == previous:
                raise AssertionError()
            if not len(list((root / "saved").glob("*.json"))) == 2:
                raise AssertionError()
            if (
                not client.get(reports["local"]["artifact_id"]).report
                == reports["local"]
            ):
                raise AssertionError()
            # Wait for preceding completed requests to release their slots, then
            # fill them with real idle TCP connections before probing through SDK.
            server.wait_active(0)
            for _ in range(8):
                sockets.append(
                    socket.create_connection(
                        ("127.0.0.1", server.server_port), timeout=3
                    )
                )
            server.wait_active(8)
            try:
                client.health()
            except ClientError as error:
                if "HTTP 503" not in str(error):
                    raise AssertionError()
            else:
                raise RuntimeError("Connection bound did not reject SDK request")
            before = len(calls)
            for _ in range(16):
                busy = cli_run(inputs["fixture"])
                if not (busy.returncode == 1 and "HTTP 503" in busy.stderr):
                    raise AssertionError(
                        f"Busy CLI response: exit={busy.returncode}, stderr={busy.stderr!r}"
                    )
            if not len(calls) == before:
                raise AssertionError()
            if not output.read_bytes() == previous:
                raise AssertionError()
            for connection in sockets:
                connection.close()
            sockets.clear()
            server.wait_active(0)
            if not client.health()["status"] == "ok":
                raise AssertionError()
        finally:
            for connection in sockets:
                connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        if not not thread.is_alive():
            raise AssertionError()
        if worker:
            if not worker["artifact_ids"] == {
                name: report["artifact_id"] for name, report in reports.items()
            }:
                raise AssertionError()
    result = {
        "status": "passed",
        "kind": "integration verification, not a performance benchmark",
        "tested_commits": pins,
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "default_worker": worker,
        "wall_seconds": time.monotonic() - started,
        "artifact_ids": {
            name: report["artifact_id"] for name, report in reports.items()
        },
        "verified": [
            "actual CLI/SDK/API fixture and Anvil runs",
            "SDK get and saved-file full equality",
            "real EVM success and revert receipts",
            "full-store idempotent repeat",
            "CLI reports 507 without retrying POST or replacing export",
            "eight idle sockets cause SDK/CLI 503 without executing work",
            "health recovers after idle sockets close",
        ],
        "fault_parameters": {
            "store_file_limit": 2,
            "connection_limit": 8,
            "busy_cli_attempts": 16,
        },
        "archive_or_model_calls": False,
        "limitations": [
            "Lowered file-count quota for integration; production thresholds tested separately",
            "Uses the tested API constructor default; worker manifest enables additional default-path proof. Kernel enforcement is a separate CI job",
            "Shared export retention is verified separately by check_export_budget.py on compatible revisions; host processes, explicit native execution and image/VM storage remain operator-controlled",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
