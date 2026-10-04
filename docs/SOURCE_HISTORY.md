# Source issues, pull requests and unfinished work

[source-history.json](source-history.json) records all **130 original source
items:29 issues and101 pull requests** across the six project repositories.
The extra Tokyo repository is excluded. The records bind repository IDs,
item IDs, numbers, titles, captured states, original source URLs and exact
preserved PR-head refs to the current component folders. The
[migration manifest](../migration-manifest.json) links this archive to the
existing source/ref/path mappings.

The coordinator's original Issue/PR identities survive the formal Transfer to
dorakingx/entrotter. Component Issue/PR records are source provenance, not newly
created GitHub issues, merged PRs or approvals. Original discussion and review
exports are retained in the owner-controlled private backup outside the old
Org. An actual separate restore verified all536 captured inventory files
(34,439,078 bytes), including the source discussion records. Raw API exports,
contacts, app settings and unrelated assets are not published with this map.

## Inspect an original PR from one clone

A normal full clone fetches the published archival branches. For example:

```bash
git show origin/archive/engine/pull/35/head:README.md
git log origin/archive/cli/pull/10/head --oneline -5
```

At an archival commit, files retain the original repository's root layout;
the `engine/` or `cli/` prefix belongs to the integrated monorepo. Do not apply
an original root-layout patch blindly to the monorepo. The map records whether
each head is an ancestor of the selected source commit. That relationship proves
history inclusion; it does not prove every historical behavior remains current.
Unselected proposals remain preserved on their exact original PR-head refs.
Historical review states never approve a new monorepo PR.

The eight unfinished viewer-save files are retained separately on
`migration/local-cli-save` at79340eae730d4bbdca1bd88597ffda1362953c8a.
They are pending review and excluded from the current production viewer.
Use [contribution guidance](../CONTRIBUTING.md) to propose a focused change against
the current component folder and link its original source item.

## Continue an unfinished issue

Look up the source repository and number in the JSON map before creating work.
An existing coordinator item already has its native URL; reuse it. A component
item has its preserved source identity and component path. Reuse an existing
monorepo tracking issue when it covers the same work. If a new issue is needed,
label the description "Migration re-registration", cite the original repository,
number and ID, and preserve original authorship as attribution rather than
pretending the historical issue or approvals were transferred.

Original source URLs are provenance identifiers and may become unavailable
after the old Org is deleted. Development and tests use the single monorepo
and local preserved Git history, with no source-URL execution dependency.
Main integration, independent approval, external app continuity, Tokyo disposition,
final asset deltas and Org deletion remain separate gates.
