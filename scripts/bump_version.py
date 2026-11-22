#!/usr/bin/env python3
"""Automated semantic version bumping and changelog generation.

Inspects conventional commits since the latest git tag, determines the semantic
version bump (major, minor, or patch), updates all manifest files, and updates CHANGELOG.md.

Usage:
  python scripts/bump_version.py [--bump patch|minor|major|auto] [--dry-run]
                                 [--out-version] [--notes-file FILE]
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

MANIFEST_FILES = [
    "package.json",
    "plugin.json",
    "gemini-extension.json",
    ".claude-plugin/plugin.json",
]


def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def get_latest_tag():
    code, out, _ = run_cmd(["git", "describe", "--tags", "--abbrev=0"])
    if code == 0 and out:
        return out
    return None


def get_current_version(repo_root):
    pkg_path = os.path.join(repo_root, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, "r", encoding="utf-8") as f:
            return json.load(f).get("version", "1.0.0")
    return "1.0.0"


def get_commits_since_tag(tag=None):
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--oneline", "--no-merges"]
    else:
        cmd = ["git", "log", "--oneline", "--no-merges"]
    code, out, _ = run_cmd(cmd)
    if code != 0 or not out:
        return []
    # Strip the commit hash
    commits = []
    for line in out.splitlines():
        parts = line.split(" ", 1)
        if len(parts) > 1:
            commits.append(parts[1].strip())
    return commits


def parse_semver(v_str):
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", v_str.strip())
    if not m:
        return 1, 0, 0
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def increment_semver(major, minor, patch, bump_type):
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def analyze_commits(commits):
    has_feat = False
    has_breaking = False

    categorized = {
        "Features": [],
        "Bug Fixes": [],
        "Performance": [],
        "Documentation": [],
        "Refactoring": [],
        "Tests": [],
        "Maintenance & CI": [],
        "Other Changes": [],
    }

    for subject in commits:
        if not subject:
            continue
        # Skip release commits
        if subject.startswith("chore(release):"):
            continue

        if "BREAKING CHANGE" in subject or re.search(r"^[a-z]+(\([^\)]+\))?!:", subject):
            has_breaking = True

        m = re.match(r"^([a-z]+)(?:\(([^\)]+)\))?!?:\s*(.+)$", subject, re.IGNORECASE)
        if m:
            prefix, scope, msg = m.group(1).lower(), m.group(2), m.group(3)
            formatted = f"- **{scope}:** {msg}" if scope else f"- {msg}"
            if prefix in ("feat", "feature"):
                categorized["Features"].append(formatted)
                has_feat = True
            elif prefix in ("fix", "patch"):
                categorized["Bug Fixes"].append(formatted)
            elif prefix in ("perf", "performance"):
                categorized["Performance"].append(formatted)
            elif prefix in ("docs", "doc"):
                categorized["Documentation"].append(formatted)
            elif prefix in ("refactor", "style"):
                categorized["Refactoring"].append(formatted)
            elif prefix in ("test", "tests"):
                categorized["Tests"].append(formatted)
            elif prefix in ("chore", "ci", "build"):
                categorized["Maintenance & CI"].append(formatted)
            else:
                categorized["Other Changes"].append(formatted)
        else:
            categorized["Other Changes"].append(f"- {subject}")

    if has_breaking:
        bump = "major"
    elif has_feat:
        bump = "minor"
    else:
        bump = "patch"

    return bump, categorized


def format_release_notes(version, date_str, categorized):
    lines = [f"## [{version}] - {date_str}\n"]
    has_items = False
    for category, items in categorized.items():
        if items:
            has_items = True
            lines.append(f"### {category}\n")
            for item in items:
                lines.append(f"{item}")
            lines.append("")
    if not has_items:
        lines.append("- Maintenance and documentation updates.\n")
    return "\n".join(lines).strip()


def update_manifest_file(filepath, new_version):
    if not os.path.exists(filepath):
        return False
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = new_version
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return True


def update_changelog(changelog_path, new_entry):
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"

    marker = "All notable changes to this project will be documented in this file.\n\n"
    if marker in content:
        parts = content.split(marker, 1)
        updated = parts[0] + marker + new_entry + "\n\n" + parts[1]
    else:
        updated = content + "\n\n" + new_entry + "\n"

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(updated.strip() + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bump", choices=["auto", "patch", "minor", "major"], default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out-version", action="store_true")
    parser.add_argument("--notes-file", default=None)
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    latest_tag = get_latest_tag()
    current_version = get_current_version(repo_root)
    commits = get_commits_since_tag(latest_tag)

    if not commits and args.bump == "auto":
        print(f"No new commits since tag {latest_tag}. Working tree is up to date.")
        if args.out_version:
            print(f"v{current_version}")
        sys.exit(0)

    detected_bump, categorized = analyze_commits(commits)
    bump_type = args.bump if args.bump != "auto" else detected_bump

    maj, minr, pat = parse_semver(current_version)
    new_version = increment_semver(maj, minr, pat, bump_type)
    new_tag = f"v{new_version}"
    today = datetime.date.today().isoformat()

    release_notes = format_release_notes(new_version, today, categorized)

    print(f"Current version: {current_version} (tag: {latest_tag or 'none'})")
    print(f"Bump type:       {bump_type}")
    print(f"New version:     {new_version} ({new_tag})")
    print("\nRelease notes preview:")
    print("-" * 40)
    print(release_notes)
    print("-" * 40)

    if args.dry-run if hasattr(args, "dry-run") else args.dry_run:
        print("\nDry run mode enabled. No files modified.")
        if args.out_version:
            print(new_tag)
        return

    # Update manifest files
    for rel_path in MANIFEST_FILES:
        full_path = os.path.join(repo_root, rel_path)
        if update_manifest_file(full_path, new_version):
            print(f"Updated {rel_path} -> {new_version}")

    # Update CHANGELOG.md
    changelog_path = os.path.join(repo_root, "CHANGELOG.md")
    update_changelog(changelog_path, release_notes)
    print(f"Updated {changelog_path}")

    # Write notes file if requested
    if args.notes_file:
        notes_full_path = os.path.abspath(args.notes_file)
        with open(notes_full_path, "w", encoding="utf-8") as f:
            f.write(release_notes + "\n")
        print(f"Wrote release notes to {notes_full_path}")

    # Set GitHub Actions output if running in workflow
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"version={new_version}\n")
            f.write(f"tag={new_tag}\n")
            f.write(f"bump_type={bump_type}\n")

    if args.out_version:
        print(new_tag)


if __name__ == "__main__":
    main()
