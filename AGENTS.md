# AGENTS.md

## Purpose
`py-stewart-filmscreen` is the Stewart Filmscreen protocol library used by the Home Assistant integration.

## Workflow
- Use `uv` for local commands.
- Run repo-local lint and tests before pushing.
- Keep protocol parsing and transport behavior deterministic and typed.

## Design Expectations
- Preserve stable identifiers and predictable command semantics.
- Keep startup, reconnect, and shutdown behavior boring and testable.

## Commits
- Use conventional commits for releasable changes: `fix: ...` or `feat: ...`.

## Releases
1. Merge normal conventional commits to `master`.
2. Let `release-please` open or update the release PR.
3. Do not manually edit version files or changelogs outside the Release Please PR.
4. Do not manually create tags or GitHub releases.
5. Merge the Release Please PR to publish.
