# Documentation link checks

Every repository's proposed `Documentation links` workflow scans that PR checkout,
using the shared composite action in this coordination repository. Consumers pin
the action to an immutable commit; changes require a reviewed pin update in each
consumer. This is a CI-only dependency, not a runtime package dependency.

The action downloads [Lychee 0.24.2](https://github.com/lycheeverse/lychee/releases/tag/lychee-v0.24.2)
over verified HTTPS and verifies the Linux x86_64 GNU release archive's SHA-256:
`1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`.
The installer supports the `ubuntu-latest` x86_64 job. The Python scanner can also
run locally with the matching Lychee release for the operator's platform.

From any repository checkout, with the coordination repository cloned nearby:

```bash
python3 /path/to/entrotter/.github/actions/docs-links/test_check.py /path/to/lychee
python3 /path/to/entrotter/.github/actions/docs-links/check.py \
  --binary /path/to/lychee --repo . --output /tmp/docs-links.json
```

The real checker regression suite creates missing Markdown targets and headings,
a hidden PR template, HTML fragments and root-relative assets, CSS resources,
and a loopback HTTP server serving actual 200 and 404 responses. Network access
to loopback is enabled only inside that test. These are controlled checker tests,
not evidence that public endpoints were available.

The production scan uses `git ls-files` to select all tracked Markdown, HTML and
CSS, including hidden directories. Newly added files must be staged before a
local scan. It checks file existence, Markdown/HTML anchor and text fragments,
and public HTTP(S) destinations. Absolute local web paths resolve against the
checkout root. It uses no persisted response cache, ignores repository Lychee
configuration, removes inherited Lychee overrides/GitHub tokens, checks TLS,
and limits requests to four globally and two per host. Timeouts, 403s, 404s,
429s and other failures are not converted to success. Diagnose network/rate
failures and rerun; never claim they prove a broken or valid target by themselves.

`docs-links` artifacts contain the complete detailed checker report, every input
file hash, source SHA, worktree cleanliness, checker version/binary hash and time.
Local checkout prefixes are replaced with `/workspace/repository` to avoid
publishing personal paths. A scan with no documents or no successful links fails.
Lychee's `cached` counter can include duplicate destinations reused within a run;
disk cache is disabled. Redirects are retained in the report.

Private and loopback HTTP endpoints are excluded and listed, because examples of
the local API are not public websites. Code/preformatted examples are outside
link extraction: an RPC endpoint used with POST is not validated by HTTP GET.
Directory links prove existence, not the correctness of every file inside them.
This is not JavaScript execution, dynamic report-fetch validation, a browser
rendering/accessibility audit, or a guarantee of future third-party availability.
The existing browser and artifact tests cover separate behavior. Main remains
protected; these proposed checks and documentation still need independent review.
