---
name: changelog
description: Add CHANGELOG.md entries and commit messages for the ansible-eda-demos repo, which maintains two changelogs (top-level dated log and the zjleblanc.eda collection's semver log). Use when the user asks for a changelog entry, release note, or commit message, or to document pending changes before committing.
---

# ansible-eda-demos Changelog

This repo has **two changelogs** with different conventions. Follow the base workflow in the personal `changelog` skill (gather diff, draft entry, write commit message) and apply the repo-specific routing and formats below.

## Which changelog(s) to update

| Changed paths | Update |
|---|---|
| Anything under `collections/zjleblanc/eda/` | **Both** [`collections/zjleblanc/eda/CHANGELOG.md`](../../../collections/zjleblanc/eda/CHANGELOG.md) and [`CHANGELOG.md`](../../../CHANGELOG.md) |
| Everything else (`rulebooks/`, `playbooks/`, `docs/`, `legacy/`, `integrations/`, `.github/`, root `README.md`, etc.) | **Only** the top-level [`CHANGELOG.md`](../../../CHANGELOG.md) |

If a diff touches both the collection and other repo areas, draft one entry for each file — do not force unrelated collection and non-collection work into a single entry.

## Top-level `CHANGELOG.md` format

Dated Keep a Changelog style. Match existing entries exactly:

```markdown
## YYYY-MM-DD — Brief summary

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

- Header: `## YYYY-MM-DD — Brief summary` (em dash, outcome-focused headline, not a file list).
- Only include the `### Added` / `### Changed` / `### Fixed` subsections that apply; omit empty ones.
- Insert the new entry immediately after the `# Changelog` title line (newest first).
- Same-day unrelated work gets its own `##` section with a different summary — never merged into an existing same-day section.

## Collection `CHANGELOG.md` format

`collections/zjleblanc/eda/CHANGELOG.md` uses **semver headers**, not dates:

```markdown
## X.Y.Z

- ...
- ...
```

- Header is the collection version, e.g. `## 1.1.0` — a flat bullet list below it, no `### Added`/`### Changed` subsections.
- Read [`collections/zjleblanc/eda/galaxy.yml`](../../../collections/zjleblanc/eda/galaxy.yml) for the current `version:`.
- The version number itself is bumped automatically by `.github/workflows/collection-release.yml` via `.github/scripts/bump_collection_version.py` based on the commit message prefix (`major:`/`minor:`/`patch:`, or `feat:`/`fix:` aliases) when merged to `main` — this skill does not bump `galaxy.yml`.
- Since the entry is drafted before that CI bump runs, add the new bullets under a `## Unreleased` header at the top if the next version is not yet known, or ask the user which bump type (major/minor/patch) they intend so the header can anticipate the resulting version. Default to asking rather than guessing.
- Keep bullets terse — this file historically lists feature-level bullets only (see the `1.0.0` entry), not categorized subsections.

## Commit message

Follow the personal `changelog` skill's rules: plain text, one line, imperative, outcome-focused, matching `git log` tone. If the change touches `collections/zjleblanc/eda/`, prefix the message with the semver bump keyword this repo's release pipeline expects (`major:`, `minor:`, `patch:`, or `feat:`/`fix:` aliases) so the CI version bump fires correctly — ask the user which bump type if it isn't obvious from the change.

## Checklist

- [ ] Determined whether the diff touches `collections/zjleblanc/eda/` and routed to the correct changelog(s)
- [ ] Top-level entry (if any) uses `## YYYY-MM-DD — Summary` with `### Added`/`### Changed`/`### Fixed`
- [ ] Collection entry (if any) uses a semver/`Unreleased` header with a flat bullet list, not dated categories
- [ ] Confirmed bump type (major/minor/patch) with the user when drafting a collection entry or commit prefix
- [ ] Commit message is plain text and, for collection changes, carries the correct bump-type prefix
- [ ] Did not run `git commit` unless explicitly requested
