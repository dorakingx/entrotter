# Engine candidate status

## 2026-10-01 — Whole worker preparation deadline, PR #22

The current bounded archive candidate now prepares the image in an owned POSIX
session. An independent watchdog caps all preparation phases at 600 seconds and
kills that session on expiry or owner-lifetime pipe EOF, including owner SIGKILL.
The operator can choose a shorter timeout. The parent cleans staging and publishes
the manifest atomically after successful preparation. Runtime/worker source,
container configuration, archive hashes and report contracts are unchanged.

The blocked-download regression failed before the fix. Final local checks pass
204 engine tests, including 15 build tests exercising a real stalled HTTP body,
native blocking call, SIGTERM, owner SIGKILL, an ignoring descendant, timer/handler
restoration and manifest failure preservation. Use the pinned Foundry 1.8.3;
an initial run with the unrelated Homebrew 1.6.0 correctly rejected recorded
observations. Ruff, mypy and the full source-bound 24-finding Bandit policy pass.

An actual BuildKit RUN sleeping for 60 seconds was stopped in 10.013 seconds by
a 10-second budget. A guest /proc query found no remaining probe process. A
normal build produced the same immutable image and complete fixture artifact
e6a12db320dd37e8d37341fe202836d9442a7e428f89381223c9ab29faa479a6.
Evidence and the Docker probe source are in evidence/worker-build-deadline/.

Independent approval, protected integration and cross-repository pin promotion
remain pending. Owner SIGKILL can leave staging/config files; cache/image/VM
storage, arbitrary caller quotas and uninterruptible kernel faults are not bounded
by this change. No new model/archive replay, upstream transaction, image
publication or paid service was used. See the coordination repository for the
broader release gates; this does not establish full goal completion.
