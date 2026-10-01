# Fresh public checkout and cross-repository bounded agent integration

The bounded integration job now uses engine
`abb4662ce960e08b2aa3a2c8a1c10719339edccc` ([engine PR #21](https://github.com/entrotter/engine/pull/21)),
SDK `b0c2ba3bba411e548af44101ae06e879bd7b5dc0`, and CLI
`a63a39000e03d151e80b5a9c47dd4df449281b93`. The clean-checkout manifest also
selects the quality-checked scenario and viewer branches, at
`3a78ecca24334ae87119a5a0b64c84ba6dd71de1` and
`61740312f281f7e911e0eb6e9482a3c372cb1fae` respectively. These are proposed source
pins pending independent approval, not new merged releases or registry packages.
[Issue #38](https://github.com/entrotter/entrotter/issues/38) tracks the integration.

Previously, the multi-repository bounded CI still selected the pre-agent engine.
The new check connects the integrated risk/replay engine with the existing default
CLI/SDK/API and shared-export checks. The original native benchmark dependency
manifest, code, prompts, reports and earlier native CI remain frozen separately.
No model is generated and no evaluated holdout is reused for policy tuning.

## Reproduce from public source

From this coordination repository, with a running local Linux cgroup-v2 Docker
daemon and its Unix socket configured, run:

```bash
export ENTROTTER_DOCKER_SOCKET=/var/run/docker.sock
python3 scripts/reproduce_clean.py --bounded-agent --output evidence/my-bounded-agent.json
python3 scripts/reproduce_clean.py --bounded --output evidence/my-bounded-fixture.json
```

On macOS, use the actual owned Docker VM's Unix socket. A host Foundry installation
is not required for these bounded commands; the worker builder fetches and checks
the pinned Linux archive. `--foundry-archive` optionally accepts a predownloaded
archive and still verifies its checksum. No image or package is published.

Each command fetches five immutable public dependency revisions into a new temporary
checkout and creates a stdlib-only venv without pip or system site packages. It
builds the worker from that source, executes the experiment, exports the result,
and runs the separately fetched CLI `verify` and `inspect` commands through the
SDK. Complete report equality is required, including all agent exchanges and
metadata. The agent path derives decision steps and the initial requested-gas
budget from the public recording's request limits. It cannot select a Python
provider or silently fall back to native execution.

The timing includes public fetch, venv creation, worker-image build, execution,
CLI verification/inspection and temporary-checkout cleanup. It excludes this
coordination checkout, Docker installation and VM startup. Image/base/build caches
can be warm; it is not a measurement of onboarding on a cold computer. A run that
takes five minutes or longer exits unsuccessfully and records its elapsed time.
The generated report is temporary; the evidence output retains its exact artifact
ID, dependency/image/source pins and outcome. Use `--output` to avoid replacing
an earlier recorded measurement. No archive RPC, model credential or wallet key
is required for the artificial local case.

`--agent`, `--historical` and the original offline mode deliberately continue using
`dependency-pins.json` and the original experimental native API. They are not
claims of bounded execution. The five mode flags are mutually exclusive.

## Verification boundaries

The fresh replay complements the [19-report compatibility evidence](BOUNDED_AGENT_REPLAY.md).
It checks contributor execution using public sources and the actual worker; it
is not a new evaluation of model quality. The model's measured lack of advantage
and historical assumptions remain unchanged. Worker quotas do not cap host caller
processes or image/VM storage, and native custom callbacks are still unsandboxed.

Local and Linux results, failed-before command support, complete quality reports,
source fingerprints and artifact identity comparisons are retained in
`evidence/bounded-agent-integration/`. Security findings remain visible and
source-bound; independent review is required. No main merge, Pages deployment,
package publication, outreach or competition submission is part of this change.

At proof commit `5dba8e401956e2a71d3260f0d7cd2aaa16186a00`, all three
[integration jobs](https://github.com/entrotter/entrotter/actions/runs/35479672160),
[quality](https://github.com/entrotter/entrotter/actions/runs/35479672206), and
[links](https://github.com/entrotter/entrotter/actions/runs/35479672162) pass.
The fresh Linux replay takes 6.673 seconds and fixture 6.962 seconds; local macOS
measurements are 20.403 and 18.588 seconds respectively. Each uses a running Docker
daemon and may reuse image caches. Downloaded reports agree on complete artifact
IDs and image source contents across ARM64/AMD64. Full type/source, security
finding and dependency identities match the local checks. These results remain
pending independent review in [PR #41](https://github.com/entrotter/entrotter/pull/41).
