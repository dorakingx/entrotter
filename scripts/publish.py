#!/usr/bin/env python3
"""Reviewed, opt-in GitHub bootstrap. Dry-run by default; never changes DNS or pays for hosting."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent


def command(args: list[str], *, cwd: Path | None = None, check: bool = True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(
            f"Command failed: {args[0]} {args[1]}\n{p.stderr.strip()[:1200]}"
        )
    return p


def gh_json(
    path: str, *, method: str = "GET", fields: dict | None = None, missing_ok=False
):
    cmd = ["gh", "api", path, "--method", method]
    for key, value in (fields or {}).items():
        cmd += [
            "-F" if isinstance(value, bool) else "-f",
            f"{key}={str(value).lower() if isinstance(value, bool) else value}",
        ]
    p = command(cmd, check=False)
    if p.returncode:
        if missing_ok and ("HTTP 404" in p.stderr or "HTTP 409" in p.stderr):
            return None
        raise RuntimeError(
            "GitHub API operation failed. Check organization/repository/Pages permissions. "
            + p.stderr.strip()[:600]
        )
    return json.loads(p.stdout) if p.stdout.strip() else {}


def preflight_local(manifest):
    for spec in manifest["repositories"]:
        path = WORKSPACE / spec["name"]
        for required in [
            "README.md",
            "LICENSE",
            "AGENTS.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
        ]:
            if not (path / required).is_file():
                raise RuntimeError(f"Missing {spec['name']}/{required}")
        if (path / "CNAME").exists():
            raise RuntimeError("Custom domain configuration is not authorized")
        for f in path.rglob("*"):
            if not f.is_file() or ".git" in f.parts or "__pycache__" in f.parts:
                continue
            if f.name.startswith(".env") and f.name != ".env.example":
                raise RuntimeError(f"Remove local env file before publishing: {f.name}")
            if f.suffix in {".png", ".webp", ".jpg", ".jpeg", ".zip", ".pyc"}:
                continue
            text = f.read_text(errors="ignore")
            if re.search(
                r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text
            ) or re.search(r"(?:ghp_|sk-proj-)[A-Za-z0-9_-]{24,}", text):
                raise RuntimeError(
                    f"Potential secret detected in {f.relative_to(path)}"
                )


def publish(args):
    manifest = json.loads((ROOT / "repositories.json").read_text())
    org = manifest["organization"]
    if org != "entrotter" or manifest["visibility"] != "public":
        raise RuntimeError("Unexpected publication target")
    preflight_local(manifest)
    for spec in manifest["repositories"]:
        print(f"PLAN public {org}/{spec['name']} <- {WORKSPACE / spec['name']}")
    print("PLAN GitHub Pages via Actions; NO custom domain; NO paid infrastructure.")
    if not args.apply:
        print(
            "Dry run only. Nothing was created, pushed or deployed. Review this script before --apply."
        )
        return
    if not shutil.which("gh") or not shutil.which("git"):
        raise RuntimeError(
            "Install GitHub CLI (gh) and git, then authenticate with gh auth login."
        )
    command(["gh", "auth", "status"])
    owner = gh_json(f"orgs/{org}")
    if owner.get("type") != "Organization":
        raise RuntimeError("Target is not an existing organization")
    membership = gh_json(f"user/memberships/orgs/{org}")
    if membership.get("state") != "active":
        raise RuntimeError("Authenticated user must be an active organization member")
    user = gh_json("user")
    published = []
    for spec in sorted(
        manifest["repositories"], key=lambda s: s["name"] == "entrotter"
    ):
        name = spec["name"]
        full = f"{org}/{name}"
        local = WORKSPACE / name
        remote = gh_json(f"repos/{full}", missing_ok=True)
        if remote:
            if remote.get("private"):
                raise RuntimeError(
                    f"{full} already exists privately; refusing to disclose it"
                )
            perms = remote.get("permissions", {})
            if not (perms.get("push") or perms.get("admin")):
                raise RuntimeError(f"No write permission for {full}")
            head = gh_json(f"repos/{full}/commits?per_page=1", missing_ok=True)
            if head and not (local / ".git").is_dir():
                raise RuntimeError(
                    f"{full} is not empty. Clone it and use reviewed PRs; never overwrite it with this archive."
                )
        else:
            remote = gh_json(
                f"orgs/{org}/repos",
                method="POST",
                fields={
                    "name": name,
                    "description": spec["description"],
                    "private": False,
                    "auto_init": False,
                    "has_issues": True,
                },
            )
        if not (local / ".git").is_dir():
            command(["git", "init", "-b", "main"], cwd=local)
        branches = command(
            ["git", "branch", "--show-current"], cwd=local
        ).stdout.strip()
        if branches != "main":
            raise RuntimeError(f"{name}: expected main; do not rewrite another branch")
        current = command(
            ["git", "remote", "get-url", "origin"], cwd=local, check=False
        )
        expected = {
            f"https://github.com/{full}.git",
            f"https://github.com/{full}",
            f"git@github.com:{full}.git",
        }
        if current.returncode:
            command(
                ["git", "remote", "add", "origin", f"https://github.com/{full}.git"],
                cwd=local,
            )
        elif current.stdout.strip() not in expected:
            raise RuntimeError(f"{name}: existing origin points elsewhere")
        for key, value in [
            ("user.name", user["login"]),
            ("user.email", f"{user['id']}+{user['login']}@users.noreply.github.com"),
        ]:
            if command(
                ["git", "config", "--get", key], cwd=local, check=False
            ).returncode:
                command(["git", "config", key, value], cwd=local)
        command(["git", "add", "--all"], cwd=local)
        changes = command(
            ["git", "diff", "--cached", "--quiet"], cwd=local, check=False
        )
        if changes.returncode == 1:
            command(
                [
                    "git",
                    "commit",
                    "-m",
                    "feat: bootstrap open-source Entrotter component",
                ],
                cwd=local,
            )
        # Use the authenticated CLI credential helper without writing a token to disk or URLs.
        command(
            [
                "git",
                "-c",
                "credential.helper=!gh auth git-credential",
                "push",
                "-u",
                "origin",
                "main",
            ],
            cwd=local,
        )
        sha = command(["git", "rev-parse", "HEAD"], cwd=local).stdout.strip()
        published.append(
            {"repository": full, "url": f"https://github.com/{full}", "commit": sha}
        )
        print(f"PUSHED {full} {sha}")
    pages_repo = f"{org}/entrotter.github.io"
    page = gh_json(f"repos/{pages_repo}/pages", missing_ok=True)
    if page and page.get("cname"):
        raise RuntimeError("Existing Pages custom domain found. Refusing to change it.")
    if page is None:
        gh_json(
            f"repos/{pages_repo}/pages",
            method="POST",
            fields={"build_type": "workflow"},
        )
    elif page.get("build_type") != "workflow":
        gh_json(
            f"repos/{pages_repo}/pages", method="PUT", fields={"build_type": "workflow"}
        )
    # Code was pushed before Pages activation; explicitly dispatch once after enabling it.
    command(
        ["gh", "workflow", "run", "pages.yml", "--repo", pages_repo, "--ref", "main"]
    )
    print(
        "PAGES WORKFLOW DISPATCHED. This is not yet a confirmed successful deployment."
    )
    if not args.skip_issues:
        for spec in json.loads((ROOT / "backlog/issues.json").read_text()):
            full = f"{org}/{spec['repository']}"
            existing = gh_json(f"repos/{full}/issues?state=all&per_page=100")
            if any(issue.get("title") == spec["title"] for issue in existing):
                continue
            label = spec["label"]
            command(
                [
                    "gh",
                    "label",
                    "create",
                    label,
                    "--repo",
                    full,
                    "--color",
                    "9C7AE5",
                    "--force",
                ]
            )
            command(
                [
                    "gh",
                    "issue",
                    "create",
                    "--repo",
                    full,
                    "--title",
                    spec["title"],
                    "--body-file",
                    str(ROOT / spec["file"]),
                    "--label",
                    label,
                ]
            )
    # Query exact status instead of announcing publication immediately.
    time.sleep(5)
    runs = gh_json(
        f"repos/{pages_repo}/actions/workflows/pages.yml/runs?event=workflow_dispatch&per_page=1"
    )
    run = (runs.get("workflow_runs") or [None])[0]
    status = {
        "repositories": published,
        "pages_status": "dispatched_not_yet_verified",
        "pages_run_url": run.get("html_url") if run else None,
    }
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence/publication.json").write_text(json.dumps(status, indent=2) + "\n")
    if run:
        print("Waiting for Pages workflow:", run["html_url"])
        command(
            [
                "gh",
                "run",
                "watch",
                str(run["id"]),
                "--repo",
                pages_repo,
                "--exit-status",
            ]
        )
        status["pages_workflow"] = "success"
        from urllib.request import urlopen

        with urlopen("https://entrotter.github.io/", timeout=30) as response:
            html = response.read(2 * 1024 * 1024).decode("utf-8")
            if response.status != 200 or "Send your agents" not in html:
                raise RuntimeError("Deployed content check failed")
        status["pages_status"] = "live_http_200_verified"
        print("VERIFIED LIVE: https://entrotter.github.io/")
        (ROOT / "evidence/publication.json").write_text(
            json.dumps(status, indent=2) + "\n"
        )
    else:
        raise RuntimeError(
            "No dispatched workflow found yet. Check GitHub Actions; do not call the site live."
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    p.add_argument("--skip-issues", action="store_true")
    try:
        publish(p.parse_args())
    except (RuntimeError, OSError, ValueError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        sys.exit(1)
