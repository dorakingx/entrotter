# Retained failed checks

The first Ruff scan reported 54 lint findings. Initial staged type scans exposed
pipe/selector, collection and variable-inference diagnostics; logs preserve their
actual source locations at each stage. Corrected collection annotations and
explicit pipe/source guards leave only the three reviewed diagnostics in the
unchanged frozen Codex adapter. Those remain visible, not suppressed.

`optimized-wheel-before.log` is a real `python -O` regression with a mismatched
local wheel. A test interception prevents any attempted installation/execution;
the old verifier reaches that interception instead of rejecting the wheel. The
fixed checker rejects before a subprocess is attempted. This is labelled fault
injection, not a real malicious package installation.

The initial full Bandit scan retained 150 findings, including 83 uses of assert.
The new explicit guards remove those optimize-away conditions; four new quality
helpers introduce additional reviewed subprocess findings. The final complete
report has 75 findings, with no rule/severity/nosec suppression.

`incomplete-tool-lock.log` records a hash-required installation rejecting the
first regenerated lock, which omitted pip-tools' unsafe-by-default pip/setuptools
entries. Regeneration with explicit `--allow-unsafe --generate-hashes` includes
all declared pins. Hash requirements were not relaxed; the final fresh venv
installation and 50-package audit pass.

Text logs normalize the local workspace prefix and strip trailing whitespace.
Historical evidence and the pinned model-provider source were not rewritten.

The first integration workflow at fac0e42 was rejected before running (GitHub
run 35473462414). `workflow-yaml-before.log` reproduces the YAML parser error:
the inline `--only-binary=:all:` argument ended with a colon followed by a space.
A block command fixes it. The quality job now parses every workflow/action YAML
file; GitHub remains responsible for workflow-context/schema validation.

Integration run 35473624321 rejected an incomplete Python 3.12 schema lock:
`referencing` conditionally requires `typing-extensions` below Python 3.13.
The lock compiled on 3.13 omitted it. Both its version and hashes are now
explicit in the contract lock and remain covered by the 50-package quality
audit. The hash-required installation was not relaxed.
