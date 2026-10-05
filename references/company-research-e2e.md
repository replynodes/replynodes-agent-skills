# Company research E2E reference

The keyless runner is
`tests/run-company-research-keyless-e2e.py --output PATH`. It provides a
reproducible contract and quality check over a fixed 20-company benchmark
(Stripe, Figma, Loom, Microsoft, Notion, Slack, Shopify, HubSpot, GitHub,
Linear, Canva, Atlassian, Zoom, Dropbox, OpenAI, Salesforce, Airtable, Intercom,
Twilio, Vercel). The benchmark spans SaaS, developer infrastructure, fintech,
commerce, platforms, enterprise software, and smaller/noisier sites.

The runner uses free Markdown, one bounded direct public homepage request for
HTML link discovery, and Brand HTTP surfaces. It canonicalizes and deduplicates
discovered candidates by host (dropping `www.` and a trailing dot), path, locale
prefix, query string, and logical category, and it probes at most one bounded
canonical first-party pricing path (`/pricing`) when the homepage does not link
one. It makes one no-retry request per selected page/endpoint, with at most one
bounded direct-pricing fallback after a Markdown 429, and keeps no raw response
bodies. Requests are paced against the free-surface rate window so the live
benchmark exercises the real extraction path instead of idling on HTTP 429s;
persistent 429s are still recorded as partial failures. Recorded metadata keeps
sanitized status, `Content-Type`, exact source and endpoint URLs, surface, and
per-company `page_read_count`. It also makes one keyless `tools/list` request to
`https://mcp.replynodes.com/mcp` and asserts that every tool named in the skill
is present in the live response.

The runner performs deterministic, bounded extraction from the consumed
first-party Markdown/HTML bodies: it derives the summary, products, features,
target market, pricing model/plans, integrations, customers, and current
signals from real body text, and links every populated claim to a bounded
excerpt taken from the body. Fields with no reliable evidence stay empty and are
listed as explicit `unknowns`. Filler/placeholder text is rejected. Every
selected successful page records its claim contribution in
`meta.page_contribution`; a page from a supported category must contribute at
least one claim.

For the Company Research-owned Markdown, Brand, and workflow MCP calls, the
runner explicitly hands off exactly one `X-ReplyNodes-Skill: company-research`
request header; arbitrary homepage discovery and direct-pricing fallback
requests remain untagged. It never reads or supplies `REPLYNODES_API_KEY`.

The emitted briefs are validated before report success with the same
deterministic schema, claim/evidence, extraction-quality, and pricing contract
validator used by the repository schema gate. Every material claim is linked to
evidence whose excerpt is relevant to the claim text. Pricing is
machine-checkable: `unknown: true` requires `model.value: null` and `plans: []`;
`unknown: false` requires a non-null observed model and at least one observed
plan. The runner enforces deterministic candidate ranking, canonical
duplicate/noise reduction, normal/sparse/partial-failure/goal-aware contract
fixtures, and the V2 budget of 8 successful pages by default / 12 hard cap. A
failed or unavailable fetch is recorded as a coverage limit, never as invented
evidence. The emitted JSON is a contract/E2E report for this runner, not
telemetry or PostHog evidence; it preserves the output contract and privacy
statement and does not claim host lifecycle analytics.

`docs/company-research-keyless-e2e.json` is the sanitized committed report, and
`docs/company-research-before-after.json` records qualitative before/after
evidence for representative companies (including Stripe) between the placeholder
baseline and the extraction-aware contract.
