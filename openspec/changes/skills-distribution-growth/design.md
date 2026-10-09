# Design: Canonical source with separately verified registries

## Architecture and boundaries

The GitHub repository is the canonical source artifact. Skills.sh is an external index of GitHub content; a HTTP 200 or rendered page does not prove fresh indexing, correct slug mapping, installability, or source identity. ClawHub is a separate publisher artifact owned by `replynodes-ai`; its downloads, rolling install counters, versions, scanner state, and provenance must be read independently.

No code path is added between these systems. This change is documentation, metadata, examples, evidence templates, and deterministic validation only.

## Install funnel

- Umbrella CTA: `npx --yes skills add replynodes/replynodes-agent-skills`.
- Focused CTA: direct GitHub skill directory URL, for example:
  `npx --yes skills add https://github.com/replynodes/replynodes-agent-skills/tree/main/skills/company-research`.
- Focused repository-plus-`--skill` forms remain compatibility probes, not the primary CTA, because a repository with a root `SKILL.md` can stop discovery before nested skills.
- `--full-depth` is a diagnostic/workaround flag, not evidence that a user-friendly install funnel is fixed.

The clean-install matrix records command, CLI version, HOME/workdir isolation, source SHA, installed path, content hash, and exact failure. It uses `DISABLE_TELEMETRY=1` for internal probes only; user-facing commands never include that variable.

## Metadata and taxonomy

Priority descriptions use task language (`company research`, `URL to Markdown`, `App Store research`, `public web research`) with bounded truthful keywords. They preserve read-only and keyless-first limits already supported by live production evidence. Legacy slugs are documented as discrepancies and never reintroduced as public taxonomy entries.

## Workflow examples

Five GitHub Actions files cover company research, URL-to-Markdown, App Store research, umbrella routing, and a scheduled public-research workflow. Each example:

- is manually dispatched or explicitly scheduled;
- uses `npx skills add` only as a documented comment/CTA, not on every push;
- performs bounded public reads only;
- uses placeholders or GitHub secret references without printing them;
- links to the canonical source and skill page;
- states that upstream/rate-limit failure must be surfaced, not retried indefinitely.

## Measurement

`references/discovery-query-baseline.csv` stores exactly 30 task-language queries, target slugs, UTC observation fields, method, visibility, observable rank, competitors, and evidence URL. `references/distribution-daily-baseline.csv` separates:

- external signals: Skills.sh installs, ClawHub downloads/installs/stars, GitHub stars and traffic;
- product signals: downstream callers, requests, key creation after attributed use, sibling adoption, and two-UTC-day retention;
- attribution: only existing bounded IDs/UTM/run headers where available.

External counters are never labeled genuine users, conversions, or retained callers. The observation window starts only after post-merge public readback and remains `PENDING` until two eligible UTC calendar days exist.

## Verification and rollback

Required gates are strict OpenSpec validation, distribution tests, `git diff --check`, exact-head changed-file review, public URL/status readback, and safe keyless smoke evidence for documented routes. A clean-install failure is recorded as a blocker with its actual error. All implementation changes are additive/documentation-focused and revertible without runtime migration.

External correction requests to Skills.sh or ClawHub are owner/operator actions after this PR; this repository change must not pretend those actions happened.
