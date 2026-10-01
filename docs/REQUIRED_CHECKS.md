# Required CI checks

The six `main` branches now require 32 checks, increased from 13 on September 20,
2026. The change closes a delivery gap: recent quality, security, Docker,
documentation and browser jobs ran successfully but were not required for merging.

The exact names, source commits and GitHub Actions application ID are recorded in
[required-checks.json](../required-checks.json). These commits are proposed branch
checkpoints with passing CI; they are not claimed to be independently approved or
merged. All requirements are bound to GitHub Actions app ID 15368.

| Repository | Before | Now | Required coverage |
| --- | ---: | ---: | --- |
| entrotter | 1 | 5 | integration, host-bounds, bounded-default, quality, docs-links |
| engine | 4 | 8 | Python 3.11–3.14, evm, isolated, quality, docs-links |
| sdk-python | 3 | 5 | Python 3.11–3.13, quality, docs-links |
| cli | 3 | 5 | Python 3.11–3.13, quality, docs-links |
| scenarios | 1 | 5 | validate, two pinned compatibility jobs, quality, docs-links |
| entrotter.github.io | 1 | 4 | check, accessibility, quality, docs-links |

## Evidence and retained protections

[Verification](../evidence/required-check-coverage/verification.json) records the
additions and invariants. Adjacent per-repository files contain the complete
`before` and `after` protection responses and the observed check runs with source
SHAs, application identities, conclusions and job URLs.

Only the required-status-checks endpoint was updated. Readback confirms no
existing requirement was removed, strict freshness remains enabled, one independent
approval is required, admins remain subject to protection, and every unrelated
protection field is unchanged. A subsequent live read matched all six saved
responses. Check lists are compared by context and application, not API ordering.
No main branch was pushed, merged or deployed by this settings change.

The website's `build` and `deploy` jobs intentionally run after merging to main;
they are skipped on pull requests and therefore are not pre-merge requirements.
Their eventual success and live-site verification remain separate release gates.

## Integrating existing pull requests

Older partial PRs may now show expected checks because their branches predate
the complete workflows. Bring the cumulative workflow changes into the reviewed
integration branch and require every configured job plus independent approval
before merging to main. Do not remove requirements or bypass protection to merge
an earlier slice. A stacked PR targeting another feature branch is not evidence
that main's merge gate has passed.

Scenario compatibility job names contain Python versions and exact engine pins.
When changing that matrix, first observe the replacement jobs passing, then
deliberately update the corresponding required names and this policy together.
The manifest is a recorded policy, not an automatic synchronization service.

This checkpoint proves settings and observed CI coverage. It does not establish
independent code review, completion of the security gate, deployment of the new
website, or competition readiness.
