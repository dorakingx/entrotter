# Reproduce CLI quality with the declared SDK

The older CLI quality recipe checked out SDKeb992 while the current manifest
requires SDKba4. Its strict dependency-source check rejected the documented
revision. The corrected recipe reads `sdk_commit` directly from the same
quality-inputs.json used by CI, quotes the checkout variable, and preserves
separate frozen agent/price SDK inputs. Source guards were not weakened.

The exact documented quality recipe was executed once in a fresh private copied
checkout/venv with fail-fast Bash. It cloned the public SDK, checked out ba4,
installed hash-locked tool wheels, built/installed only the local SDK wheel,
passed pip check, Ruff lint/format, all9-source mypy and unsuppressed Bandit,
verified declared dependency coverage, audited42 locked identities with0
reported advisories, and built the CLI wheel. Host/caches were not controlled;
this is a setup result, not a timing or speed claim.

A second fresh environment installed only those CLI/SDK wheels without registry
access or an Engine. All7CLI/5SDK source and installed modules exactly match
original1ce CI wheels; only CLI METADATA/RECORD changed with the README. Full
README metadata and every RECORD hash/size match sources. Doctor and both
complete-verification commands pass with the original whole JSON goldens.
Runtime/scripts, SDK/workflow/locks/schemas and frozen samples are unchanged.
The prior92-test results are reused historical evidence; current mandatoryCI
is a separate publication requirement, not inferred from this documentation edit.

[Source/package/setup manifest](local-verification.json) binds the exact recipe
and raw log hashes. An initial wrong-cwd launch was interrupted130 before type
and security checks; that partial log remains private and proves no success.
The correct fresh-cwd execution is distinct and successful. No new EVM/model,
browser/media/user, main/Pages or submission execution is claimed. Independent
human protected-main approval and the continuing improvement goal remain separate.
