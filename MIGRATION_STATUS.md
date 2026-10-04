# Migration status — October 4, 2026

The accepted active goal migrates Entrotter to the single public MIT repository
`dorakingx/entrotter`. The owner's later direct request replaces the proposed
Pages hosting with the new Vercel project https://entrotter.vercel.app/.
Migration, passing CI and submission are checkpoints; improvement continues
through the verified official deadline.

## Completed preparation

- Authenticated owner and old Org admin verified. Inventory found seven public
  repositories and zero private repositories. The extra `tokyo2026` project
  remains separate while awaiting the owner's disposition.
- A permanent owner-controlled backup outside the old Org preserves 125,701
  regular files (12,424,955,111 logical bytes), symlinks, ignored/private work,
  all Git bundles/refs and uncommitted work. All seven repositories restored
  into a separate directory and passed Git integrity/object checks. The backup
  remains on the same physical Mac disk; it is not an off-device disaster copy.
- All four release attachments restored with exact API digests; restored MP4s
  are readable. The approved Aave review video retains its exact 11,002,134
  bytes and 138.48-second duration. Instruction archive hashes also match.
- Additional owner authentication made Packages, Projects, Org hooks and Actions
  metadata readable. No packages/projects/hooks/Org Actions secrets, variables
  or runners were listed. Org rulesets return an explicit Team-plan feature
  restriction, not an unexplained missing-resource result.
- Local unsquashed integration starts at coordinator bdb2059 and merges current
  Engine f53a66a / SDK ba4af51 / CLI169b759 / Scenarios8785bb0 / Viewer dacd134.
  Each initial component subtree exactly matches its source tree. Source commits
  remain ancestors; 423 source refs have namespaced archival mappings.
- The eight unfinished local-save files are preserved byte-for-byte on the
  separate `migration/local-cli-save` branch. They are pending review and are
  excluded from the already deployed viewer.
- New Vercel production deployment is READY. Public unauthenticated HTTPS,
  all 29 public-file bytes/MIME types, Aave display, sample switching and CLI
  recipes were checked. Automatic Git integration is pending migration.

## Still required

All659 CI archives from the initial authenticated inventory now have exact-byte
backup and independent reconstruction/CRC verification, including actual restored
copies of84 archives found in the workspace snapshot. All seven public wiki
routes redirect to the repository, corroborating authenticated missing wiki Git
refs; both Pages environment policies/names are exported. Final remote delta,
external app disposition and the complete backup/deletion audit remain pending.
The extra Tokyo project's disposition is pending. Do not delete the Org.

The local foundation adapts one-clone paths/bootstrap, active docs and instructions,
all component CI coverage, Docker prerequisites and fixed viewer CLI recipes.
The legacy Org/Pages publisher is retired; the replacement stages only29 declared
static files and rejects the retired --apply command. Scoped/full configured
checks passed: Engine390, SDK55, CLI107, scenarios23, root39, website Python12 and
Node138 (764 tests, no skips), lint/format/types and source-bound security gates.
All88 root and159 website findings remain visible with individual rationales;
the three original frozen-provider type diagnostics remain unchanged. Independent
history, foundation-source and policy reviews passed for their explicit scopes.
A fresh committed-clone/demo, current browser/audit results and remote mandatory
CI are still separate gates; local passing tests are not their substitutes.

Formal coordinator transfer has not occurred. Destination ownership, current
refs/issues/PR delta and collisions must be freshly verified before transfer.
Root and component main branches remain unmerged/protected. Component PR metadata
is not automatically transferred or approved by a history merge.

Next: retain a reviewed committed candidate and backup; independently audit the
final asset delta; run fresh one-clone demo/real Anvil/browser checks; create a reviewed migration PR;
verify formal transfer by repository ID; link the existing new Vercel project;
resolve old Org runtime/app dependencies and capture final deltas before the
separate deletion audit. Update the existing submission only within the official
portal and after all required facts/materials/quality gates are verified.

Private inventories, auth/session data, producer logs and owner contacts are
retained outside public Git. No credentials are exported or committed.
