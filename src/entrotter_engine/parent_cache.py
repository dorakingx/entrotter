"""Internal trace-only bounded archive bridge. It owns one fixed child per experiment."""

from __future__ import annotations
import json
import math
import os
from pathlib import Path
import secrets
import selectors
import signal
import subprocess
import sys
import time
from .evm import ExecutionError
from .rpc import RPC

MAX_CONFIG = 16384
MAX_OUTPUT = 4096


class ParentCache:
    def __init__(self, url: str, parent: dict, deadline: float):
        RPC(
            url
        )  # Preserve the ordinary URL policy; never print or select a URL from a plan.
        self.url, self.parent, self.deadline = url, parent, deadline
        self.process: subprocess.Popen[bytes] | None = None
        self.stats: dict[str, int] | None = None
        self.token = secrets.token_hex(16)
        self.output = bytearray()

    def __enter__(self):
        if (
            os.name != "posix"
            or not math.isfinite(self.deadline)
            or not 0 < self.deadline - time.monotonic() <= 150
        ):
            raise ExecutionError("Owned parent cache requires a finite POSIX deadline")
        config = json.dumps(
            {
                "url": self.url,
                "parent": self.parent,
                "deadline": self.deadline,
                "token": self.token,
            }
        )
        if len(config.encode()) > MAX_CONFIG:
            raise ExecutionError("Parent cache configuration exceeds its bound")
        try:
            end = min(self.deadline, time.monotonic() + 5)
            self.process = subprocess.Popen(
                [sys.executable, str(Path(__file__).with_name("_parent_cache.py"))],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            if self.process.stdout is None or self.process.stdin is None:
                raise ExecutionError("Owned parent cache startup pipe is unavailable")
            # Private fixed configuration travels over the ownership pipe, never
            # argv or an added environment variable. Keep this pipe open afterward.
            os.set_blocking(self.process.stdin.fileno(), False)
            pending = memoryview(config.encode() + b"\n")
            with selectors.DefaultSelector() as writer:
                writer.register(self.process.stdin, selectors.EVENT_WRITE)
                while pending:
                    if time.monotonic() >= end:
                        raise ExecutionError(
                            "Owned parent cache startup exceeded its budget"
                        )
                    if writer.select(max(0, min(0.1, end - time.monotonic()))):
                        try:
                            count = os.write(
                                self.process.stdin.fileno(), pending[:4096]
                            )
                        except BlockingIOError:
                            continue
                        pending = pending[count:]
            os.set_blocking(self.process.stdout.fileno(), False)
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdout, selectors.EVENT_READ)
                while b"\n" not in self.output:
                    if time.monotonic() >= end:
                        raise ExecutionError(
                            "Owned parent cache startup exceeded its budget"
                        )
                    for key, _ in selector.select(
                        max(0, min(0.1, end - time.monotonic()))
                    ):
                        raw = os.read(key.fd, 512)
                        if not raw:
                            raise ExecutionError(
                                "Owned parent cache exited before startup"
                            )
                        self.output.extend(raw)
                        if len(self.output) > MAX_OUTPUT:
                            raise ExecutionError(
                                "Owned parent cache output exceeded its bound"
                            )
            line, rest = self.output.split(b"\n", 1)
            ready = json.loads(line)
            if (
                not isinstance(ready, dict)
                or set(ready) != {"version", "port", "token"}
                or ready["version"] != 1
                or ready["token"] != self.token
                or type(ready["port"]) is not int
                or not 1 <= ready["port"] <= 65535
            ):
                raise ExecutionError("Owned parent cache startup binding differs")
            self.output = bytearray(rest)
            self.url = f"http://127.0.0.1:{ready['port']}/{self.token}"
            return self
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise

    def __exit__(self, *exc):
        failed = False
        if self.process is None:
            return
        try:
            try:
                if self.process.stdin is not None:
                    self.process.stdin.close()
                self.process.wait(timeout=2)
            except BaseException:
                failed = True
            finally:
                if self.process.poll() is None:
                    try:
                        os.killpg(self.process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    except BaseException:
                        failed = True
                    try:
                        self.process.wait(timeout=2)
                    except BaseException:
                        failed = True
            try:
                if self.process.stdout is not None:
                    while True:
                        raw = os.read(self.process.stdout.fileno(), 512)
                        if not raw:
                            break
                        self.output.extend(raw)
                        if len(self.output) > MAX_OUTPUT:
                            raise ValueError()
                if self.output:
                    stats = json.loads(self.output)
                    keys = {
                        "requests",
                        "upstream",
                        "hits",
                        "entries",
                        "bytes",
                        "uncached",
                        "errors",
                        "refused_handlers",
                    }
                    if (
                        not isinstance(stats, dict)
                        or set(stats) != keys
                        or any(
                            type(v) is not int or not 0 <= v <= 8 * 1024 * 1024
                            for v in stats.values()
                        )
                        or stats["entries"] > 1024
                        or stats["bytes"] > 8 * 1024 * 1024
                        or stats["requests"] > 4096
                        or stats["upstream"] + stats["hits"] > stats["requests"]
                    ):
                        raise ValueError()
                    self.stats = stats
            except (ValueError, OSError):
                self.stats = None
                failed = True
            if self.process.returncode != 0 or self.stats is None:
                failed = True
        finally:
            for stream in (self.process.stdin, self.process.stdout):
                if stream is not None:
                    try:
                        stream.close()
                    except BaseException:
                        failed = True
        if failed and (not exc or exc[0] is None):
            raise ExecutionError("Owned parent cache cleanup failed") from None
