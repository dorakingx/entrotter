# Static hosting on Vercel

The owner selected the new project **entrotter** on Vercel's existing Doraking
Hobby account. Its public URL is https://entrotter.vercel.app/. The initial
reviewed deployment uses viewer dacd134; monorepo Git integration is pending.
Other projects, domains and billing are unchanged. The backend stays local.

`vercel.json` at repository root builds only the static website. From one clone:

```bash
python3 scripts/publish.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory website/_site
```

Choose a new empty output directory for another staging run with `--output`.
The public-file manifest explicitly lists viewer assets, modules, example
reports, schemas and MIT license. No repo-root files, private logs, local env
files, Node tools or backend sources are staged. Symlinks and path traversal
are rejected. The old publisher's `--apply` / `--skip-issues` options fail closed;
they cannot create Organizations/repos, change protection or deploy Pages.

The existing Vercel project must be linked to the transferred repository after
review, with the repo root as build root and `website/_site` as output. Required
GitHub checks and independent main approval remain mandatory. Project creation,
branch pushes and config files alone are not evidence of a live deployment.
Verify READY, the actual production alias, public HTTPS, source byte hashes,
MIME types and actual browser behavior after an authorized deployment.
