#!/usr/bin/env python3
"""Determine the next semantic version for the zjleblanc.eda collection and
bump galaxy.yml in place.

The bump level is derived from the prefix of each commit subject line, for
every commit since the last `collection-v*` tag that touched the collection
path:

    major: ...            -> major bump
    minor: ...             -> minor bump
    feat: ...               -> minor bump (alias of minor:)
    patch: ...             -> patch bump
    fix: ...                -> patch bump (alias of patch:)
    (anything else)         -> patch bump (safe default)

When multiple qualifying commits are present, the highest bump level wins
(major > minor > patch).

Outputs (written to $GITHUB_OUTPUT, or printed if unset):
    new_version        - the computed next version (empty if no qualifying
                          commits were found, meaning no release should run)
    previous_version    - the version read from galaxy.yml before bumping
    bump_type           - "major", "minor", or "patch"
"""
import os
import re
import subprocess

COLLECTION_PATH = os.environ.get("COLLECTION_PATH", "collections/zjleblanc/eda")
GALAXY_YML = os.path.join(COLLECTION_PATH, "galaxy.yml")
TAG_PREFIX = "collection-v"

LEVELS = {"patch": 0, "minor": 1, "major": 2}

PREFIX_TO_LEVEL = {
    "major": "major",
    "minor": "minor",
    "feat": "minor",
    "patch": "patch",
    "fix": "patch",
}

PREFIX_RE = re.compile(r"^(major|minor|feat|patch|fix)(\(.+\))?!?:", re.IGNORECASE)


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def get_last_tag():
    try:
        return run(["git", "describe", "--tags", "--match", f"{TAG_PREFIX}*", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None


def get_commits_since(ref):
    rev_range = f"{ref}..HEAD" if ref else "HEAD"
    log = run(["git", "log", rev_range, "--pretty=format:%H%x01%s", "--", COLLECTION_PATH])
    commits = []
    if log:
        for line in log.split("\n"):
            sha, _, subject = line.partition("\x01")
            commits.append((sha, subject))
    return commits


def determine_bump(commits):
    bump = "patch"
    for _, subject in commits:
        match = PREFIX_RE.match(subject.strip())
        level = PREFIX_TO_LEVEL[match.group(1).lower()] if match else "patch"
        if LEVELS[level] > LEVELS[bump]:
            bump = level
    return bump


def read_version():
    with open(GALAXY_YML, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"^version:\s*(\S+)\s*$", content, re.MULTILINE)
    if not match:
        raise SystemExit(f"Could not find a 'version:' field in {GALAXY_YML}")
    return content, match.group(1)


def compute_next_version(version, level):
    major, minor, patch = (int(part) for part in version.split("."))
    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def write_version(content, old_version, new_version):
    new_content = re.sub(
        rf"^version:\s*{re.escape(old_version)}\s*$",
        f"version: {new_version}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    with open(GALAXY_YML, "w", encoding="utf-8") as f:
        f.write(new_content)


def write_output(name, value):
    output_file = os.environ.get("GITHUB_OUTPUT")
    line = f"{name}={value}\n"
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(line)
    else:
        print(line, end="")


def main():
    last_tag = get_last_tag()
    commits = get_commits_since(last_tag)

    print(f"Last release tag: {last_tag or '(none found)'}")
    print(f"Collection-scoped commits since last tag: {len(commits)}")
    for sha, subject in commits:
        print(f"  {sha[:7]} {subject}")

    if not commits:
        print("No collection-scoped commits found; skipping release.")
        write_output("new_version", "")
        write_output("previous_version", "")
        write_output("bump_type", "")
        return

    bump = determine_bump(commits)
    content, current_version = read_version()
    new_version = compute_next_version(current_version, bump)

    print(f"Bump type: {bump}")
    print(f"Version: {current_version} -> {new_version}")

    write_version(content, current_version, new_version)

    write_output("new_version", new_version)
    write_output("previous_version", current_version)
    write_output("bump_type", bump)


if __name__ == "__main__":
    main()
