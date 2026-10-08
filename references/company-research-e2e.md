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
signals from real body text, and links every populated claim to a bounded,
normalized excerpt taken from the body. Extraction is conservative and fails
closed to an explicit `unknown` rather than emitting a mis-typed claim: customers
require explicit customer/case-study context, integrations require explicit
connector/ecosystem evidence, pricing plans require a recognized plan name paired
with an observed amount and are deduplicated, positioning rejects CTA/signup
copy, and error/not-found bodies never yield claims, signals, or pricing. Fields
with no reliable evidence stay empty and are listed as explicit `unknowns`.
Filler/placeholder text is rejected. Every selected successful page records its
claim contribution in `meta.page_contribution`; a page from a supported category
must contribute at least one claim, or is recorded honestly with a support note
when no claim survives the type checks.

The validator applies independent, field-aware content checks in addition to
excerpt/claim token relevance, so a benchmark cannot go green on a wrong-type
claim whose excerpt merely repeats it. Regression fixtures for each review
finding live in `tests/test-company-research-v2-quality-fixtures.py` (benchmark
false-green, customer context, integration evidence, pricing coherence, error
pages, positioning CTA rejection, excerpt normalization) and run in the package
test.

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

## Live re-verification (2026-10-08)

Re-executed 2026-10-08 with `tests/run-company-research-keyless-e2e.py` under a
clean `HOME` and `DISABLE_TELEMETRY=1`: a bounded live keyless run over the first
three benchmark companies (Stripe, Figma, Loom) emitted briefs that pass the
runner's schema/contract/quality validator, and all 20 briefs in
`docs/company-research-keyless-e2e.json` re-validate against the same
`company_brief_validator` from the source head
`4aa42f65980056d3464f596d0fd749c3be17eca7`. The default 20-company live run is
data-dependent: it is accepted only when at least one company grounds public
pricing, and a changed or noisy live page can trip an extraction-quality
assertion (observed 2026-10-08 as a linked-evidence excerpt check).

Focused-install reference limitation: `npx skills add
https://github.com/replynodes/replynodes-agent-skills/tree/main/skills/company-research`
installs only `skills/company-research/SKILL.md`. The repository-root
`references/` files that the skill names (`company-brief.schema.json`,
`company-brief-contract.md`, `company-research-e2e.md`,
`company-research-distribution.md`) are not bundled with the focused skill; they
resolve only in the full repository (umbrella install). The inline contract in
`SKILL.md` is self-contained for host use.
