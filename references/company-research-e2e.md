# Company research E2E reference

The existing keyless runner is
`tests/run-company-research-keyless-e2e.py --output PATH`. It provides a
reproducible three-case check:

- `figma.com` (pricing may be unknown when its pricing link is outside the
  bounded selection)
- `loom.com` (public pricing)
- `microsoft.com` (larger multi-product with pricing unknown)

The runner uses free Markdown, one bounded direct public homepage request for
HTML link discovery, and Brand HTTP surfaces. It makes one no-retry request per
selected page/endpoint, with at most one bounded direct-pricing fallback after a
Markdown 429, keeps no raw response bodies, and records sanitized status,
`Content-Type`, exact source and endpoint URLs, surface, and per-company
`page_read_count`. It also makes one keyless `tools/list` request to
`https://mcp.replynodes.com/mcp` and asserts that every tool named in the skill
is present in the live response. It never reads or supplies
`REPLYNODES_API_KEY`.

The emitted briefs are validated before report success with the same
deterministic schema, claim/evidence, and pricing contract validator used by
the repository schema gate. Every material claim is linked to evidence.
Pricing is machine-checkable: `unknown: true` requires `model.value: null` and
`plans: []`; `unknown: false` requires a non-null observed model and at least
one observed plan. The report includes coverage limits, each company's
observed candidate sequence, and a trace-derived budget proof for the default
cap of 12, hard cap of 20, and rejection of candidate 21 without retry or
fallback. A failed or unavailable fetch is recorded as a coverage limit, never
as invented evidence.
