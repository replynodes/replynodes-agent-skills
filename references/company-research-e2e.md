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
is present in the live response. For the Company Research-owned Markdown,
Brand, and workflow MCP calls, the runner explicitly hands off exactly one
`X-ReplyNodes-Skill: company-research` request header; arbitrary homepage
discovery and direct-pricing fallback requests remain untagged. It never reads
or supplies `REPLYNODES_API_KEY`.

The emitted briefs are validated before report success with the same
deterministic schema, claim/evidence, and pricing contract validator used by
the repository schema gate. Every material claim is linked to evidence.
Pricing is machine-checkable: `unknown: true` requires `model.value: null` and
`plans: []`; `unknown: false` requires a non-null observed model and at least
one observed plan. The runner covers 20 public companies, with Stripe as the primary before/after
case, and enforces deterministic candidate ranking, duplicate/noise reduction,
normal/sparse/partial-failure/goal-aware contract fixtures, and the V2 budget
of 8 successful pages by default / 12 hard cap. A failed or unavailable fetch is
recorded as a coverage limit, never as invented evidence. The emitted JSON is a
contract/E2E report for this runner, not telemetry or PostHog evidence; it
preserves the output contract and privacy statement and does not claim host
lifecycle analytics.
