# Native Anvil provenance and Cargo advisory coverage

[Tracking issue](https://github.com/entrotter/entrotter/issues/28).
[Engine implementation](https://github.com/entrotter/engine/pull/19).
The existing image audit covers detected OS/interpreter packages but does not
identify Anvil's native dependency inventory. Foundry v1.8.3 publishes a signed
SLSA build provenance statement and an archive-bound SPDX attestation. The new
separate gate verifies both before scanning their declared Cargo dependencies.

## What is verified

- Checksum-pinned Cosign verifies the exact release workflow identity, GitHub OIDC
  issuer, source commit `cae51ad458f6abb64852b7709eb784352429825d`, predicate type
  and archive digest. The signed provenance must include the builder's extracted
  Anvil binary digest as well as the expected archive subject and source pin.
- The release SPDX file is checksum-pinned and must equal the complete signed
  predicate. It contains 1,298 package entries. Its 1,126 Cargo package URLs,
  names and versions must match the scanner's complete inventory exactly,
  including duplicate counts. Missing/replaced/version-changed entries fail.
- Checksum-pinned Trivy scans all detected advisory severities, including unfixed,
  low and unknown. No suppression or VEX input is accepted. A fresh, unexpired
  database is required, and any finding fails. Raw signed claims, scan output,
  database metadata and all relevant hashes remain available on failure.
- Both Linux arm64 and amd64 release inventories pass the actual local scan
  without reported findings. Their signed binary hashes match prior real worker
  build manifests. An intentional real verification using the wrong expected
  source commit fails. Seven policy-fixture tests are separate from these actual
  cryptographic and advisory checks; the full native/unit suite has 149 tests.

The checked Anvil binary hashes are:

| Release | SHA-256 |
| --- | --- |
| Linux arm64 | `61ae6eeff626ffe4c265f3119ac4f534991ac8637008e76fd25d7284a685186f` |
| Linux amd64 | `674a06c97a01350cd00241762bbfb01ebcafce9b6e8cbd6c8758ecea6ef4b968` |

The existing [worker-image evidence](WORKER_IMAGE_AUDIT.md) supplies actual
container builds and platform-specific image IDs. Native auditing consumes the
builder's manifest; the separate image gate verifies its source/image binding.
The runtime package source and Dockerfile are unchanged in this slice, so no new
historical/model outcome or runtime behavior is claimed.

## Reproduce and inspect

From the pinned engine checkout, after building a worker manifest:

```bash
PYTHONPATH=src python3 scripts/check_native_security.py --manifest worker-image.json --output .quality/native-security
```

The public upstream API may rate-limit anonymous requests. An optional `GH_TOKEN`
authenticates only that API; the CI uses its read-only repository token. It is
not forwarded to Cosign/Trivy or included in evidence. The actual-worker CI runs
both image and native gates and uploads all generated files even on failure.

Evidence is in `evidence/native-release-audit/`. Large raw JSON files are stored
as deterministic gzip to keep the repository manageable. `compressed-inputs.json`
records their uncompressed SHA-256 and byte length; the summary records compressed
file hashes. Use `gzip -dc PATH.json.gz` to inspect the original JSON. Compression
does not strip findings, packages, signatures or certificates.

## Boundaries that remain

The pinned upstream [release workflow](https://github.com/foundry-rs/foundry/blob/cae51ad458f6abb64852b7709eb784352429825d/.github/workflows/release.yml)
uses Syft to scan the whole checkout. This is an overinclusive source inventory,
not an exact record of libraries linked into the Anvil binary for a given target
and feature set. It cannot establish that no linked dependency was missed by the
upstream generator. The 172 entries without Cargo package URLs, including local
workspace source and Actions, are explicitly retained outside this advisory scan.

The compiler, native C libraries, missing dependencies, host kernel/VM/daemon and
upstream build-system compromise still need separate treatment. A valid signature
proves the claimed origin, not independent source review or bit-for-bit
reproducible compilation. No absence-of-vulnerabilities or public multi-tenant
safety claim follows from this scan. Native/image quotas and remaining human
review, deployment, user-validation and submission gates stay open.


## Linux verification checkpoint

Engine `6410c37663d37685a30effccd87844e1740b8637` passes all five workflows.
Run 35470277261 executes 16 actual Docker checks and both package gates. Its
1,126 Cargo packages and 26 OS packages have no reported findings. Downloaded
source/auditor, archive/binary, signed SBOM and raw report hashes are verified;
policy evaluation over the downloaded inventory also passes. The full 24-finding
Bandit scan agrees with local results, all 42 Python dependencies have no reported
advisories, and the MIT wheel's 14 Python files match source.

[Coordination PR #29](https://github.com/entrotter/entrotter/pull/29), proof commit
`573b6c3a67773dbaeafaaedb413c638e5a44fcb5`, passes all three integration jobs
(35470453881) and links (35470453897). Pinned dependencies, checker and complete
fixture/EVM result IDs match the prior runtime verification. Public-source clone,
fresh venv, image build and fixture execution take 5.928 seconds on Linux with
Docker already running and warm caches; installation/VM startup are excluded.

Both PRs remain unmerged pending independent approval. Frozen benchmark inputs
remain clean and both local VM profiles remain stopped. This checkpoint adds
provenance/inventory coverage and does not change runtime or close the limits
listed above.
