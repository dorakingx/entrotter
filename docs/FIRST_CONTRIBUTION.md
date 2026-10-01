# Find a first contribution

Choose one small task below. Each issue identifies its scope, starting files and
acceptance checks. All six were open and labelled `good first issue` when checked
on September 20, 2026; availability can change. This is a contribution directory,
not a claim that the tasks have been completed or that contributors have joined.

| Repository | Task | Starting scope |
| --- | --- | --- |
| entrotter | [Add a safe, reproducible bug-report walkthrough](https://github.com/entrotter/entrotter/issues/44) | New documentation task |
| engine | [Explain success, reverted, rejected and noop EVM outcomes](https://github.com/entrotter/engine/issues/23) | New documentation task |
| sdk-python | [Add a small end-to-end SDK example](https://github.com/entrotter/sdk-python/issues/1) | Existing example/diagnostic task |
| cli | [Improve CLI errors and command examples](https://github.com/entrotter/cli/issues/1) | Existing example/diagnostic task |
| scenarios | [Add a field-by-field walkthrough of the recovery-trap fixture](https://github.com/entrotter/scenarios/issues/9) | New documentation task |
| entrotter.github.io | [Add a manual accessibility review checklist for the report viewer](https://github.com/entrotter/entrotter.github.io/issues/12) | New documentation task |

## Before changing files

Read the selected repository's CONTRIBUTING.md, SECURITY.md and the issue. Check
existing comments and open PRs for overlapping work. Start from the repository's
current main branch unless the issue explicitly identifies a dependency; record
the source revision you actually use. Never assume that a proposed worker, schema
or accessibility change is already merged or deployed.

Most of the new tasks are documentation exercises using existing public fixtures.
The SDK/CLI tasks can include executable examples or diagnostic tests. State the
Python, Foundry and Docker prerequisites of any command you run. Do not install
unpublished package names from a registry or obtain paid API keys just to begin.

Make one focused PR, link the issue, attach the relevant check results and explain
anything not run. Preserve synthetic/historical labels and never add guessed
measurements, user feedback, credentials or private reports. Human screen-reader
observations must come from an actual review; writing a checklist is preparation.

Main branches require independent approval and configured CI. Some older partial
PRs predate the full workflow set; see [required checks](REQUIRED_CHECKS.md) for the
integration procedure. Current main branches still await integration of the newer
workflows and product changes. A small PR based on main can therefore show missing
required checks until that integration is reviewed and merged. Check the linked
issue and dependency PRs before investing in setup; this directory does not claim
that all six current main branches are ready to merge a new contribution today.
Contributors should not weaken requirements to make an older branch mergeable.

The [checkpoint](../evidence/first-contribution-paths.json) records issue URLs,
labels, open states and body hashes from GitHub. It establishes that there is a
scoped contribution opportunity in each repository, not product acceptance or
genuine target-user evaluation.
