# Verification failures retained

`wrong-source-commit.log` is an intentional negative real Cosign check: the correct signed SBOM was verified with an all-zero expected source commit. Cosign rejected the certificate identity. No cryptographic check was disabled.

`wrong-predicate-type.log` is an initial investigative invocation using `https://spdx.dev/Document`. The upstream published predicate is `https://spdx.dev/Document/v2.3`; the command failed closed. The implemented checker requires and verifies that exact published type.

The first type-check run also required explicit Counter key annotations; the corrected 19-file check passes. Policy fixture tests are distinct from the actual upstream signature and advisory scans.
