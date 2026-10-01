# SDK and CLI quality evidence

The SDK and CLI now have proposed independent quality jobs alongside their
Python 3.11/3.12/3.13 unit matrices and documentation-link checks. Both use
immutable Actions and a complete version/hash-locked Python tool/build graph.
The SDK has no runtime dependencies. The CLI keeps its existing exact
`entrotter-sdk==0.1.0` requirement, supplied only by building the pinned public
SDK source, without resolving a package from a registry.

## Checks and boundaries

Ruff checks lint and formatting. Normal mypy rules include unannotated function
bodies; this is not a claim that arbitrary JSON is fully statically typed. The
SDK ships `py.typed`, verified in its actual wheel. The CLI has a minimal typing
stub for its optional engine import; the stub is not shipped as an engine and
cannot replace actual CLI→SDK→engine execution tests.

Bandit scans all production Python files under `src/` and `scripts/`, using every
default rule with `--ignore-nosec`. There are no finding/rule suppressions. Any
finding fails. A second check requires nonempty, complete file coverage without
skipped checks. Policy failure tests use explicitly labeled scanner fixtures.
Actual full scans currently report zero findings across SDK four/CLI five files.
This is evidence of the scanner result, not proof of security.

Each job audits the same 42 locked tool/build packages with strict collection,
required hashes and no ignored advisories. There were no reported known Python
vulnerabilities. The local unpublished SDK is source-checked separately; it is
not claimed to have a registry advisory identity. CLI dependency verification
checks the exact source revision, package name/version, empty runtime/optional
graph and covered build dependencies. New/unpinned/unaudited requirements fail.
Native binaries, the interpreter and OS are outside this package audit.

## Behavior and packaging

A correctly hashed report with an array/object `mode` previously raised a raw
TypeError in the SDK. The retained regression fails before the patch. Explicit
mode validation now raises ClientError, and a CLI test verifies the user receives
a normal error without a traceback. Source formatting and CLI result-variable
separation preserve existing output and wire behavior. SDK 18 and CLI 13 tests
pass; these overlap prior suite counts and are not added to a workspace total.

Fresh environments install only locally built wheels with `--no-index --no-deps`.
Isolated Python imports prove the installed packages are used. SDK metadata has
an MIT license and no runtime requirement; its marker and Python files match
source. CLI metadata retains the exact SDK requirement. With no engine Python
package installed, doctor, verify and inspect accept the byte-identical public
synthetic report. No packages are published.

The updated SDK also accepts all 16 existing archived-state/agent reports checked
in this slice, preserving their complete content hashes. This is parser/hash
compatibility evidence, not another archived-state or model execution.

The separate actual CLI→SDK→API check executes the fixture and real native Anvil
cases, compares full saved/exported/SDK reports, tests full-store 507 behavior,
checks 16 consecutive overload 503s without retry/work/output replacement, and
verifies recovery. Its dependency pins move to the new SDK/CLI commits while the
frozen benchmark checkouts and original integration job pins stay unchanged.

Reproduction commands live in each repository's README. Exact commands, source
pins, before/after failures, complete scan/advisory artifacts, package checks and
CI run IDs are recorded in [the evidence summary](../evidence/sdk-cli-quality/summary.json)
and its adjacent files. These PRs require independent review and merge. Other
repository quality work, complete default resource bounds, native/OS audits,
accessibility, videos and genuine target-user validation remain open.
