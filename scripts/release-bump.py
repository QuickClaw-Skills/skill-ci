#!/usr/bin/env python3
"""Bump a QuickClaw skill version and optionally publish a GitHub release.

Default mode is safe/local: update skill.json and release notes only.
Use --commit, --tag, --push and --github-release explicitly for write actions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise SystemExit(
            f"command failed: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout[-4000:]}\n"
            f"stderr:\n{proc.stderr[-4000:]}"
        )
    return proc


def parse_version(version: str) -> tuple[int, int, int]:
    match = SEMVER_RE.match(version)
    if not match:
        raise SystemExit(f"Unsupported skill.json.version: {version!r}; expected X.Y.Z")
    return tuple(int(x) for x in match.groups())  # type: ignore[return-value]


def bump_version(version: str, bump: str) -> str:
    major, minor, patch = parse_version(version)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise SystemExit(f"invalid bump type: {bump}")


def github_token() -> str | None:
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "GITHUB_SKILLS"):
        value = os.environ.get(name)
        if value:
            return value
    return None


def github_api(method: str, url: str, payload: dict | None = None, allow_404: bool = False) -> dict | None:
    token = github_token()
    if not token:
        raise SystemExit("GitHub release requested but GH_TOKEN/GITHUB_TOKEN/GITHUB_SKILLS is not set")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "quickclaw-skill-ci-release-bump",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")[:2000]
        if allow_404 and exc.code == 404:
            return None
        raise SystemExit(f"GitHub API failed {method} {url}: {exc.code}\n{body}") from exc


def repo_slug(root: Path) -> str:
    remote = run(["git", "remote", "get-url", "origin"], cwd=root, check=False)
    url = remote.stdout.strip()
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", url)
    if not match:
        raise SystemExit("Could not infer GitHub repo from origin remote; use --repo owner/name")
    return f"{match.group('owner')}/{match.group('repo')}"


def update_release_notes(root: Path, version: str, note: str) -> None:
    today = dt.date.today().isoformat()
    block = f"## v{version} - {today}\n\n{note.strip()}\n\n"
    for filename in ("RELEASE_NOTES.md", "CHANGELOG.md"):
        path = root / filename
        if path.exists():
            path.write_text(block + path.read_text(encoding="utf-8"), encoding="utf-8")
            return
    (root / "RELEASE_NOTES.md").write_text(block, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump and release a QuickClaw skill")
    parser.add_argument("--root", default=".", help="Skill repository root")
    parser.add_argument("--bump", choices=["patch", "minor", "major"], default="patch")
    parser.add_argument("--version", help="Explicit target version instead of bumping")
    parser.add_argument("--note", default="Automated QuickClaw Skills release.")
    parser.add_argument("--repo", help="GitHub repo owner/name; inferred from origin when omitted")
    parser.add_argument("--commit", action="store_true", help="Commit version/release note changes")
    parser.add_argument("--tag", action="store_true", help="Create annotated vX.Y.Z tag")
    parser.add_argument("--push", action="store_true", help="Push current branch and tag")
    parser.add_argument("--github-release", action="store_true", help="Create idempotent GitHub Release")
    parser.add_argument("--dry-run", action="store_true", help="Print intended actions without writing files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skill_json = root / "skill.json"
    if not skill_json.exists():
        raise SystemExit(f"skill.json not found: {skill_json}")

    data = json.loads(skill_json.read_text(encoding="utf-8"))
    old_version = str(data.get("version", ""))
    new_version = args.version or bump_version(old_version, args.bump)
    parse_version(new_version)
    tag = f"v{new_version}"

    print(json.dumps({"root": str(root), "old": old_version, "new": new_version, "tag": tag}, ensure_ascii=False))
    if args.dry_run:
        return

    data["version"] = new_version
    skill_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_release_notes(root, new_version, args.note)

    run(["python3", "-m", "json.tool", "skill.json"], cwd=root)

    if args.commit:
        paths = ["skill.json"]
        for candidate in ("RELEASE_NOTES.md", "CHANGELOG.md"):
            if (root / candidate).exists():
                paths.append(candidate)
        run(["git", "add", *paths], cwd=root)
        run(["git", "commit", "-m", f"chore: release {tag}"], cwd=root)

    if args.tag:
        existing = run(["git", "tag", "--list", tag], cwd=root)
        if existing.stdout.strip():
            raise SystemExit(f"tag already exists locally: {tag}")
        run(["git", "tag", "-a", tag, "-m", tag], cwd=root)

    if args.push:
        run(["git", "push", "origin", "HEAD"], cwd=root)
        if args.tag:
            run(["git", "push", "origin", tag], cwd=root)

    if args.github_release:
        slug = args.repo or repo_slug(root)
        existing = github_api("GET", f"https://api.github.com/repos/{slug}/releases/tags/{tag}", allow_404=True)
        if existing:
            print(f"GitHub Release {tag} already exists; skip")
        else:
            release = github_api(
                "POST",
                f"https://api.github.com/repos/{slug}/releases",
                {
                    "tag_name": tag,
                    "target_commitish": tag,
                    "name": tag,
                    "body": args.note,
                    "draft": False,
                    "prerelease": False,
                    "generate_release_notes": False,
                },
            )
            assert release is not None
            print(f"GitHub Release created: {release.get('html_url')}")


if __name__ == "__main__":
    main()
