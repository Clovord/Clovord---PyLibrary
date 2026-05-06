from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from pathlib import Path

HEADER = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on Keep a Changelog, and this project follows Semantic Versioning.\n\n"

SECTIONS = {
    "Added": ("feat",),
    "Fixed": ("fix",),
    "Changed": ("refactor", "perf", "chore"),
    "Docs": ("docs",),
    "Tests": ("test",),
}

CONVENTIONAL_RE = re.compile(r"^(?P<type>[a-z]+)(\([^)]+\))?(!)?:\s*(?P<desc>.+)$", re.IGNORECASE)

README_MARKER_START = "<!-- latest-release-notes:start -->"
README_MARKER_END = "<!-- latest-release-notes:end -->"


def escape_markdown_text(text: str) -> str:
    escaped = text.replace("\\", "\\\\")
    for char in ("`", "*", "_", "[", "]", "(", ")", "<", ">"):
        escaped = escaped.replace(char, f"\\{char}")
    return escaped


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=True, text=True, capture_output=True)
    return result.stdout.strip()


def latest_tag() -> str | None:
    try:
        tags = run_git(["tag", "--sort=-v:refname"]).splitlines()
    except subprocess.CalledProcessError:
        return None
    return tags[0] if tags else None


def default_since_tag() -> str | None:
    """
    Pick a sensible baseline tag for changelog generation.

    If HEAD is already tagged (e.g. release tag was created before running
    this workflow), using the latest tag would produce an empty range.
    In that case, use the newest tag that is not pointing at HEAD.
    """
    try:
        tags = run_git(["tag", "--sort=-v:refname"]).splitlines()
    except subprocess.CalledProcessError:
        return None
    if not tags:
        return None

    try:
        head_tags = set(run_git(["tag", "--points-at", "HEAD"]).splitlines())
    except subprocess.CalledProcessError:
        head_tags = set()

    for tag in tags:
        if tag and tag not in head_tags:
            return tag

    return tags[0]


def commits_since(tag: str | None) -> list[str]:
    revision_range = "HEAD" if not tag else f"{tag}..HEAD"
    try:
        output = run_git(["log", revision_range, "--pretty=%s"])
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def latest_commit_subject() -> str | None:
    try:
        output = run_git(["log", "-1", "--pretty=%s", "HEAD"])
    except subprocess.CalledProcessError:
        return None
    subject = output.strip()
    return subject if subject else None


def categorize(commits: list[str]) -> dict[str, list[str]]:
    categorized: dict[str, list[str]] = {section: [] for section in SECTIONS}
    categorized["Other"] = []

    for subject in commits:
        m = CONVENTIONAL_RE.match(subject)
        if not m:
            categorized["Other"].append(subject)
            continue

        ctype = m.group("type").lower()
        desc = m.group("desc").strip()

        placed = False
        for section, prefixes in SECTIONS.items():
            if ctype in prefixes:
                categorized[section].append(desc)
                placed = True
                break

        if not placed:
            categorized["Other"].append(desc)

    return {k: v for k, v in categorized.items() if v}


def build_entry(version: str, categorized: dict[str, list[str]]) -> str:
    date_str = dt.date.today().isoformat()
    lines = [f"## [{version}] - {date_str}"]

    for section in ("Added", "Fixed", "Changed", "Docs", "Tests", "Other"):
        items = categorized.get(section)
        if not items:
            continue
        lines.append(f"### {section}")
        for item in items:
            lines.append(f"- {escape_markdown_text(item)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n\n"


def build_readme_release_notes(version: str, commits: list[str], categorized: dict[str, list[str]]) -> str:
    latest_commit = commits[0] if commits else "n/a"
    safe_latest_commit = escape_markdown_text(latest_commit)
    lines = [
        "## Latest Release Notes",
        f"Version: `{version}`",
        f"Last commit: {safe_latest_commit}",
        "",
    ]

    for section in ("Added", "Fixed", "Changed", "Docs", "Tests", "Other"):
        items = categorized.get(section)
        if not items:
            continue
        lines.append(f"### {section}")
        for item in items[:5]:
            lines.append(f"- {escape_markdown_text(item)}")
        lines.append("")

    lines.append("See full history in CHANGELOG.md.")

    body = "\n".join(lines).rstrip()
    return f"{README_MARKER_START}\n{body}\n{README_MARKER_END}\n"


def update_readme(version: str, commits: list[str], categorized: dict[str, list[str]]) -> None:
    readme = Path("README.md")
    if readme.exists():
        existing = readme.read_text(encoding="utf-8")
    else:
        existing = "# clovord\n\n"

    release_block = build_readme_release_notes(version, commits, categorized)
    pattern = re.compile(
        rf"{re.escape(README_MARKER_START)}.*?{re.escape(README_MARKER_END)}\n?",
        flags=re.DOTALL,
    )

    # Remove all old blocks first, then inject exactly one current block.
    cleaned = pattern.sub("", existing).rstrip()
    if cleaned:
        new_content = cleaned + "\n\n" + release_block
    else:
        new_content = release_block

    readme.write_text(new_content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update CHANGELOG.md from conventional commit messages.")
    parser.add_argument("--version", required=True, help="Release version, e.g. 0.1.5")
    parser.add_argument("--since-tag", default=None, help="Optional starting tag, e.g. v0.1.4")
    args = parser.parse_args()

    changelog = Path("CHANGELOG.md")
    existing = changelog.read_text(encoding="utf-8") if changelog.exists() else HEADER

    tag = args.since_tag if args.since_tag is not None else default_since_tag()
    commits = commits_since(tag)
    if not commits:
        fallback = latest_commit_subject()
        if fallback:
            commits = [fallback]
            print("No commits found in selected range, using latest HEAD commit as fallback.")
        else:
            print("No commits found to add to changelog.")
            return 0

    categorized = categorize(commits)
    entry = build_entry(args.version, categorized)

    update_readme(args.version, commits, categorized)

    version_header = f"## [{args.version}]"
    if version_header in existing:
        print(f"Version {args.version} already exists in CHANGELOG.md")
        return 0

    if existing.startswith("# Changelog"):
        first_section = existing.find("## [")
        if first_section == -1:
            new_content = HEADER + entry
        else:
            new_content = existing[:first_section] + entry + existing[first_section:]
    else:
        new_content = HEADER + entry + existing

    changelog.write_text(new_content, encoding="utf-8")
    print(f"Updated CHANGELOG.md and README.md for version {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
