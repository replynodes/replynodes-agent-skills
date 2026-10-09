# Proposal: Make ReplyNodes skills discoverable and safely acquirable

## Why now

The canonical repository contains useful read-only public-data skills, but the live acquisition funnel is fragmented:

- GitHub source has 23 `SKILL.md` files while the current Skills.sh page exposes 17 indexed entries.
- Skills.sh still renders legacy aliases and an old `replynodes/agent-skills` page.
- A 30-query live baseline found no ReplyNodes result for natural task-language queries; direct `replynodes` search does find the package.
- ClawHub has owner-scoped packages and aggregate counters, but aliases, source provenance, and attribution are not equivalent to GitHub source state.
- Focused CLI installation needs a clean-environment proof; the current host is at 99% disk usage and an install probe failed with `ENOSPC`.

This change makes the source repository's public contract explicit, improves truthful task-language metadata, provides safe examples, and records external registry limitations without creating artificial installs or duplicate listings.

## Goals

1. Establish one canonical umbrella install and supported focused install form for priority skills.
2. Make README, root `SKILL.md`, taxonomy, and priority skill metadata task-oriented, bounded, read-only, and keyless-first only where verified.
3. Provide five copyable GitHub Actions examples that use harmless public reads and never expose credentials or create install loops.
4. Preserve a reproducible 30-query discovery baseline and daily measurement contract that separates registry counters from product attribution and retention.
5. Document Skills.sh and ClawHub as separate external artifacts and record owner actions required for index/provenance correction.

## In scope

- `README.md`, root `SKILL.md`, `skills.sh.json`, and priority skill first-screen metadata/CTAs.
- `docs/distribution-growth-plan.md`.
- Five files under `examples/github-actions/`.
- Baseline templates under `references/`.
- OpenSpec artifacts and deterministic distribution tests.

## Out of scope

- Registry publication, deletion, rename, hide/unhide, or duplicate listing creation.
- Synthetic installs, repeated CI installs, leaderboard manipulation, or new telemetry sinks.
- Credentials, cookies, private data, write-capable provider behavior, or changes to runtime APIs.
- Claiming a clean install or live registry refresh without readback evidence.

## Capabilities

- `install-discovery`
- `workflow-examples`
- `distribution-measurement`

## Success criteria

- Strict OpenSpec validation passes.
- Repository tests and `git diff --check` pass at the exact PR head.
- Public docs point to canonical source and focused pages, with legacy/index drift explicitly labeled.
- Baseline contains exactly 30 bounded query rows and preserves `not observable` when rank is unavailable.
- Clean focused and umbrella installation evidence is either captured or marked blocked with the actual host error; no partial install is reported as success.
- PR is opened against the repository default branch and the exact head SHA is reported.
