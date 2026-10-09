# Design

## Source and index boundaries

GitHub source metadata is canonical. Skills.sh indexes GitHub and may expose soft-200 pages, stale descriptions, and legacy slugs; it has no self-serve authenticated write path in the observed public contract. ClawHub is a separate publisher artifact with owner-scoped readback and possible slug/version reservations. Source changes never imply external index refresh or ClawHub provenance.

## Install funnel

Keep the root `replynodes` umbrella and nested `skills/<slug>/SKILL.md` layout. Use `--full-depth` in public focused commands because the current CLI requires it for this layout. Internal discovery installs set `DISABLE_TELEMETRY=1`. A clean install matrix records the source SHA and installed content hash; it does not generate repeated CI installs.

## Measurement

Use a checked-in baseline template and daily snapshots from public registry pages, GitHub traffic, and existing downstream product telemetry. Registry counters are external signals. Real-user/conversion reporting uses existing bounded product attribution and two-day retention; no new sink is introduced.

## Distribution surfaces

Improve the README and focused skill first screens. Add five workflow examples under `examples/github-actions/`. Link ClawHub pages as non-canonical acquisition surfaces and explicitly flag slug/provenance drift. For external corrections, open upstream PR/issues with exact URLs and source SHA; do not create duplicates.

## Risks and rollback

The main risk is index caching or stale external ownership state. All changes are documentation/examples and can be reverted without runtime impact. Do not rename public slugs in this change. Registry owner actions remain separate blockers.
