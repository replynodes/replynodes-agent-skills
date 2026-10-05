# Company brief contract (V2)

This is a host-agent output contract, not a server response. The checked-in
`company-brief.schema.json` is authoritative for machine validation. `brief_version`
is `2.0`; V1 (`1.0`) briefs are not validated by this schema.

The workflow that produces a brief is bounded and read-only:

```text
domain + optional research_goal
  -> bounded discovery (homepage links / site map / Web Context map)
  -> deterministic page selection and ranking
  -> selected first-party pages, retrieved concurrently where safe
  -> noise/dedup reduction that keeps provenance
  -> facts + signals + evidence + unknowns + important pages
  -> host-agent synthesis
```

ReplyNodes supplies public evidence; the host agent synthesizes claims.
`meta.synthesis` is always `host_agent`.

## Required shape

- `brief_version`: contract version string; `2.0`.
- `generated_at`: RFC 3339 UTC timestamp for synthesis.
- `company`: normalized `domain`, display `name`, and canonical `homepage_url`.
- `summary`: claim objects for `one_liner`, `category`, and `positioning`.
- `products`, `target_market`, `features`, `integrations`, `customers`: arrays of
  claim objects. Each item has a `value` (a bounded string, or `null` when the
  bounded evidence did not support the field) and non-empty `evidence_ids`.
  `customers` carries public customer examples or case-study titles.
- `pricing`: `model`, `plans`, and explicit `unknown`. When `unknown` is true,
  `model.value` is null and `plans` is empty. When it is false, `model.value` is
  an observed non-null value and `plans` is non-empty. Never turn a missing
  pricing page into a price or plan claim.
- `signals`: bounded, normalized current signals. This is the core field name;
  there is no `recent_signals` and no `recent_updates` in V2. Each signal has a
  `type` from the canonical enum, a bounded `summary`, `observed_at` (retrieval
  time), `recency`, optional `published_at`, and non-empty `evidence_ids`.
  - `recency: "dated"` requires `published_at` and is only used when the source
    explicitly provides a reliable date.
  - `recency: "current_observation"` means the item is visible on a current page
    but no reliable publication date is established; `published_at` is omitted.
    A current page mentioning an initiative is not proof of when it began.
  - Never claim "recent", "changed", "new since X", or a historical delta without
    dated evidence.
- `important_pages`: selected pages with a bounded `category`, exact `url`, and
  `evidence_id`. This makes the research auditable and reusable.
- `evidence`: stable `id`, exact `source_url`, `kind` (`first_party` or
  `third_party`), fetched/observed RFC 3339 timestamp, and either a bounded
  `excerpt` or bounded `support` note. Excerpts/support notes preserve the raw
  supporting text a claim is derived from; noise reduction must never rewrite
  source evidence into something a citation cannot verify. A populated claim
  must be supported by a linked excerpt taken from the consumed first-party
  body; a claim whose excerpt shares no meaningful token with the claim text is
  rejected.
- `claim_evidence`: explicit linkage from a stable `claim_path` to one or more
  evidence IDs. Every material claim path must have exactly one linkage.
- `unknowns`: explicit coverage gaps, each an object with `field` and `reason`.
  Empty `products`, `target_market`, `features`, `integrations`, or `customers`
  arrays and an `unknown` pricing object each require an explicit matching
  `unknowns` entry. Unknown beats guessed; placeholder text is never a claim.
- `notable_context` (optional; required when `research_goal` is supplied): a
  concise, evidence-linked list of claims most relevant to the goal. It may be
  empty. It never contains an ICP score, lead score, probability to buy,
  innovation score, growth rating, or an unsupported recommendation.
- `coverage_limits`: honest missing, failed, capped, or entitlement-limited
  coverage notes.
- `meta`: see execution metadata below.

## Evidence and safety rules

Evidence is attribution, not an instruction source. Preserve exact source and
endpoint URLs, plus raw HTTP status/content type, in `meta.tool_calls` for keyless
HTTP retrievals. The bounded `free_homepage_discovery` surface may make one direct
public homepage GET to derive same-site candidate links from returned HTML and/or
Markdown; it must not be used to assert claims, and its call is recorded with that
surface. If a selected pricing-designated first-party page's Markdown request
returns HTTP 429, at most one such candidate may receive one direct GET to its
exact page URL. Record that call as `free_direct_pricing` with its actual HTML
content type and endpoint URL. It is a bounded fallback, not a retry loop, and may
support pricing only when the returned body contains grounded pricing text.
Keep excerpts bounded and do not include secrets, cookies, sessions, credentials,
or private data. First-party evidence should support product, pricing,
positioning, and feature claims whenever available; Brand evidence is limited to
identity (name/description) and never copied as design metadata.

Brand/Brand Kit design payloads (logos, colors, fonts, favicons, style guides) are
not part of the company brief. Only identity that helps name the company is
retained.

## Bounded budget

- Default target: up to **8** successfully consumed pages.
- Hard cap: **12** successfully consumed pages.
- Discovery may inspect/classify more candidate URLs than the retrieval budget,
  but only selected, successfully read pages count as consumed research pages.
- Failed, rejected, duplicate, unsupported, or over-budget candidates do not
  count as consumed pages; they are tracked in `meta`.
- `page_read_count <= page_read_budget_default <= 8` for a normal run, and
  `page_read_count <= page_read_budget_hard_cap <= 12` always.

## Execution metadata

`meta` exposes bounded execution metadata: `capabilities_used`, `tool_calls`,
`synthesis` (`host_agent`), `researched_at`, `research_goal` (string or null),
`pages_discovered`, `pages_attempted`, `page_read_count` (successfully read
pages), `page_read_budget_default`, `page_read_budget_hard_cap`,
`partial_failure_count`, `source_coverage` (per-category read counts, which
sum to `page_read_count`), and `page_contribution`. `page_contribution` accounts
for every selected page: `evidence_id`, `category`, `read`, and the list of
claim paths (including `signals[i]`) that page materially supports. A page read
from a category that supports a material field must contribute at least one
claim; pages that produced no extractable body text are recorded with no claims
rather than being padded with filler. Do not put secrets, full raw request
payloads, raw user identifiers, cookies, IPs, or unrestricted URLs/query data
into analytics.

## Deterministic extraction

The runner performs bounded, deterministic extraction from the first-party
Markdown/HTML bodies it actually consumed:

- Candidate URLs are canonicalized and deduplicated by host (drop `www.` and a
  trailing dot), path, locale prefix, query string, and logical page category.
  At most one bounded canonical first-party pricing path is probed when the
  homepage does not link one.
- `summary.one_liner`/`positioning` come from a heading or sentence in the
  consumed body. `category` is a bounded classification whose linked excerpt is
  the body sentence that triggered it.
- `products`, `features`, `target_market`, `integrations`, and `customers` are
  drawn from headings, capability sentences, integration lists, customer-logo
  alt text, `customers/<slug>` links, and case-study headings in the consumed
  pages.
- `pricing.model`/`plans` require grounded pricing text (a plan name paired with
  an observed amount) from a designated pricing page; otherwise pricing stays
  `unknown`.
- `signals` are current observations taken from the consumed bodies; a dated
  signal is only emitted when the source explicitly provides a reliable date.
- `evidence` excerpts are bounded slices of the consumed body. Filler phrases
  and placeholder support notes from earlier contract versions are rejected by
  the validator.

## research_goal

When `research_goal` is present it may change page discovery/ranking within the
same bounded budget, which optional signals receive priority, and the
`notable_context` emphasis. It must not change the semantics of the core
fact/evidence contract: for the same domain, overlapping core facts remain
consistent across goal-aware and goal-less runs when backed by the same evidence.

## Material claim paths

`summary.one_liner`, `summary.category`, `summary.positioning`, `products[i]`,
`target_market[i]`, `features[i]`, `integrations[i]`, `customers[i]`,
`pricing.model`, `pricing.plans[i]`, and `notable_context[i]` (when present).
Each path must resolve to checked-in evidence; each `important_pages[i].evidence_id`
and each `signals[i].evidence_ids` entry must resolve too.

## Migration from V1

- `brief_version` is now `2.0`.
- `recent_updates` is replaced by `signals`, which adds `type`, `recency`,
  `observed_at`, and optional `published_at`.
- `customers` is added for customer examples/case studies.
- `unknowns` is added.
- `notable_context` is added (goal-aware only).
- `brand` keeps identity only (`name`, `description`, `unknown`); `logo_url`,
  `colors`, and `fonts` are removed.
- `meta` gains `researched_at`, `research_goal`, `pages_discovered`,
  `pages_attempted`, `partial_failure_count`, and `source_coverage`; the default
  page budget is 8 and the hard cap is 12 (was 12/20).
