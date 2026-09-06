---
name: appstore-data-api
title: App Store Public Reads
description: Read-only, normalized public-data reads of App Store applications through the ReplyNodes App Store public-read service: app lookup, developer catalog lookup, storefront chart listings, privacy label lookup, ratings summaries, paged reviews, bounded term search, related-app listings, and type-ahead suggestions — nine capabilities via one HTTPS gateway. Two authentication paths are supported — a Bearer workspace key for prepaid/team usage and an x402 v2 pay-per-call flow in USDC on Base for anonymous single-call usage. Normalized JSON, transparent bounded pages, and the documented routes match the live gateway surface. Public reads only: no purchase, review-submission, account, or other mutation exists, and no platform login material is involved.
version: 1.1.6
contract_version: v1
mode: readonly
auth: Bearer workspace key OR x402 v2 pay-per-call in USDC on Base at the gateway; the read layer itself carries no credential material
license: Apache-2.0
keywords: [app store, appstore-data-api, ios, read-only, public data, app metadata, fetcher, x402, pay-per-call, usdc, base, wallet]
search_terms: [app store, appstore, ios, app lookup, app search, related apps, app metadata, public app data, developer, list, privacy, ratings, reviews, search, similar, suggest, x402, pay-per-call, usdc, base, wallet]
entrypoint: SKILL.md
install_guide: INSTALL.md
source: published from the public sanitized provenance repository; review changes in git
---

# App Store Public Reads

Read-only, normalized public-data reads of App Store applications through the ReplyNodes App Store public-read service: app lookup, developer catalog lookup, storefront chart listings, privacy label lookup, ratings summaries, paged reviews, bounded term search, related-app listings, and type-ahead suggestions — nine capabilities via one HTTPS gateway. Two authentication paths hit the same routes — a Bearer workspace key for prepaid/team usage and an x402 v2 pay-per-call flow in USDC on Base for anonymous single-call usage. Normalized JSON, transparent bounded pages, and normalized errors. Public reads only: no purchase, review-submission, account, or other mutation exists, and no platform login material is involved.

This directory is the public `appstore-data-api` agent skill package. This public package documents the nine supported GET capabilities and their normalized v1 contract.
The supported public gateway base URL is https://api.replynodes.com. Use this deployment base unless your workspace is explicitly issued another HTTPS gateway URL; never use localhost:18789.

## Quick reference

| | |
| --- | --- |
| Base URL | `https://api.replynodes.com` |
| Auth | `Authorization: Bearer <workspace API key>` OR x402 v2 pay-per-call in USDC on Base |
| Price | `/v1/appstore/capabilities` is free; every other route is `amount_micros=3000` ($0.003 / call) |
| Endpoints | 9 priced `GET` routes, plus the free `/capabilities` route |
| Read-only | Yes — no purchase, review-submission, account, or other mutation |

## Surface status

- The nine documented read operations have stable public contracts with bounded requests and normalized v1 responses.
- Route paths in this catalog are stable capability identifiers used for agent tool bindings; public gateway exposure for this platform is issued to your workspace at onboarding and must not be assumed reachable anywhere else.
- No availability, uptime, latency, or success-rate figure is claimed anywhere in this package; example payloads are illustrative fixtures, not captured responses.

## Package contents

| File | Purpose |
| --- | --- |
| `LICENSE` | Apache-2.0 license copied from the repository root. |
| `SKILL.md` | This handbook (package entrypoint). |
| `INSTALL.md` | Step-by-step installation for every supported agent family. |
| `PUBLICATION.md` | ClawHub publication status, moderation evidence, and claim boundaries. |
| `manifest.json` | Machine-readable inventory: per-file sizes and SHA-256 digests plus the exact capability-to-operation map. |
| `CHECKSUMS.txt` | `sha256sum`-format checksums for every packaged handbook/reference file. |
| `llms.txt` | Single-file orientation for LLM agents (byte-copy of the canonical artifact). |
| `references/appstore-public-v1.openapi.json` | OpenAPI 3.1 spec of the supported read capabilities (byte-copy). |
| `references/appstore-mcp.schema.json` | Read-only MCP-style tool manifest (byte-copy). |
| `references/endpoints.md` | Worked HTTP examples and per-agent integration snippets (byte-copy). |
| `evidence/publication-evidence.json` | Machine-readable local verification facts and prohibited-claims policy. |
| `skill-card.md` | ClawHub verification card metadata. |

## Read-only guarantees

- Every cataloged operation is an HTTP GET capability over public application data only.
- No purchase, review-submission, account, login, or any other write or authenticated capability exists in this domain, now or later; it is excluded by policy rather than by configuration.
- Only the documented operations are supported by this public package.
- No request path carries or accepts platform login material of any kind; the read layer performs public reads server-side.
- Only public platform data is returned; counters, scores, and prices are null when the source omits them - zeros are never fabricated - and unknown upstream fields are dropped.

## Authentication

Two payment paths hit the same nine routes; the gateway picks the right one
from the headers you send. Neither path requires App Store or developer
account credentials.

**(a) Bearer workspace-key** — for prepaid/team usage where a workspace
already holds credits. Mint a key from the [ReplyNodes
console](https://app.replynodes.com/auth). Keys are stored server-side only
as SHA-256 hashes; never embed a key in client-side code, repositories, logs,
screenshots, or support tickets — send it per request in the Authorization
header.

```bash
export APPSTORE_API_KEY="<your workspace API key>"
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/app?id=553834731"
```

**(b) x402 v2 pay-per-call** — for anonymous single-call usage. The
gateway answers a priced request with HTTP `402` plus an x402 v2
challenge body (asset `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` USDC
on Base, network `eip155:8453`, amount `3000` base units = `$0.003` per
call). A wallet signs the challenge and retries with an `X-PAYMENT`
header; on settlement the gateway releases the same response a Bearer
caller would receive. To fund a wallet first, see the [ReplyNodes top-up
page](https://replynodes.com/topup?skill=appstore-api).

```bash
# 1. anonymous probe — gateway returns 402 + payment-required header
curl -i "https://api.replynodes.com/v1/appstore/search?term=test"
# HTTP/2 402
# payment-required: <base64 challenge>
# {"x402Version":2,"accepts":[{"scheme":"exact","network":"eip155:8453",...}],"extensions":{"topup":{"topup_url":"/v1/billing/topup/intents"}}}

# 2. sign challenge with a Base USDC wallet and retry
curl -i \
  -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/search?term=test"
# HTTP/2 200 + normalized App Store response (same body a Bearer caller sees)
```

`GET /v1/appstore/capabilities` needs no header and costs nothing — use it
to confirm the gateway is up and to see the live route/price/payment-modes
catalog (`payment_modes: ["prepaid_credit", "x402_per_call", "x402_topup"]`)
before spending on data calls.

An unauthenticated request to any priced route returns HTTP `402` with
the x402 challenge above (it does **not** return `401`). A Bearer key
that is missing, malformed, expired, or revoked returns HTTP `401` with
`code: invalid_or_expired_token`; the gateway does **not** fall back
to x402 for that request — auth errors fail closed, exactly as
documented in [Normalized errors](#normalized-errors).

If your integration already speaks x402 for other ReplyNodes gateways
(Reddit, Hacker News, FOMO data API), the same v2 challenge shape
applies here: asset `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`,
network `eip155:8453`, amount in micros.

Every response — success or error — carries an opaque `request_id` in
`meta` (or in `error`) for support correlation. Never print, log, or
ask a user to paste an API key into chat, and never log a signed
`X-PAYMENT` proof — it is single-use bearer material.

### Pricing

`GET /v1/appstore/capabilities` is free and requires no header. Every one
of the nine data routes below is priced at `amount_micros=3000` ($0.003
per call), whether paid via a Bearer workspace key drawing down prepaid
credit or via a signed x402 v2 `X-PAYMENT` proof in USDC on Base. No
settlement, credit, or balance change is claimed anywhere in this package
without a completed payment or a valid key — this handbook documents the
request/response contract only.

## Capabilities - exact mapping to implemented read operations

Capabilities cover single-app lookup, developer catalog lookup, storefront
chart listings, privacy label lookup, ratings summaries, paged reviews,
bounded term search, related-app listings, and type-ahead suggestions for
public App Store data. This table is the live `/v1/appstore/capabilities`
surface — nothing here is deferred.

| Capability | MCP tool | Route | Matrix operation | Implemented in |
| --- | --- | --- | --- | --- |
| `get_app` | `appstore_get_app` | GET `/v1/appstore/app` | `app` | public read contract |
| `get_developer` | `appstore_get_developer` | GET `/v1/appstore/developer` | `developer` | public read contract |
| `list_apps` | `appstore_list_apps` | GET `/v1/appstore/list` | `list` | public read contract |
| `get_privacy` | `appstore_get_privacy` | GET `/v1/appstore/privacy` | `privacy` | public read contract |
| `get_ratings` | `appstore_get_ratings` | GET `/v1/appstore/ratings` | `ratings` | public read contract |
| `get_reviews` | `appstore_get_reviews` | GET `/v1/appstore/reviews` | `reviews` | public read contract |
| `search_apps` | `appstore_search_apps` | GET `/v1/appstore/search` | `search` | public read contract |
| `get_similar_apps` | `appstore_get_similar_apps` | GET `/v1/appstore/similar` | `similar` | public read contract |
| `suggest_terms` | `appstore_suggest_terms` | GET `/v1/appstore/suggest` | `suggest` | public read contract |

This public package is validated for route, schema, checksum, JSON, and credential-safety consistency before release.

## Response envelope

Success: `{ "data": [ <app records> ], "meta": { "request_id": "req-...", "contract_version": "v1", "generated_at": "2026-08-23T00:00:00Z", "availability": "complete" } }`.
Single lookups (`app`, `developer`, `privacy`) carry exactly one element in
`data`; list-shaped operations (`list`, `ratings`, `reviews`, `search`,
`similar`, `suggest`) carry zero or more; `data` is always present even when
empty. Failure: `{ "error": { "code": "...", "message": "...", "request_id": "req-..." } }`.
`meta.request_id` echoes your opaque correlation id; always quote it in
support requests. Normalized payloads follow contract `v1`: identifiers
are platform-prefixed URNs (`ios:app:<id>`), timestamps are RFC3339 UTC, and
counters, scores, and prices are explicit `null` when the public source omits
them - zeros are never fabricated. Unknown upstream fields are dropped.

## Page bounds

- Search, list, reviews, similar, and suggest each return one bounded page: limit defaults to 20 when omitted and is clamped client-side to at most 50 regardless of what a caller requests. There are no continuation tokens on this surface.

## Scenarios

Each route below shows the Bearer path and the x402 anonymous-probe-then-retry
path; both hit the identical route and return the identical normalized body.

**Check the gateway is live and see current pricing (free, no key needed):**

```bash
curl "https://api.replynodes.com/v1/appstore/capabilities"
```

**App lookup by track id (Bearer):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/app?id=553834731"
```

**App lookup by track id (x402):**

```bash
curl -i "https://api.replynodes.com/v1/appstore/app?id=553834731"
# HTTP/2 402 — sign the payment-required challenge, then retry:
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/app?id=553834731"
```

**Related apps (Bearer / x402):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/similar?id=553834731"

curl -i "https://api.replynodes.com/v1/appstore/similar?id=553834731"
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/similar?id=553834731"
```

**Storefront chart listing (Bearer / x402):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/list?category=TOP_FREE&country=us"

curl -i "https://api.replynodes.com/v1/appstore/list?category=TOP_FREE&country=us"
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/list?category=TOP_FREE&country=us"
```

**Developer catalog lookup (Bearer / x402):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/developer?id=553834731"

curl -i "https://api.replynodes.com/v1/appstore/developer?id=553834731"
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/developer?id=553834731"
```

**Privacy label lookup (Bearer / x402):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/privacy?id=553834731"

curl -i "https://api.replynodes.com/v1/appstore/privacy?id=553834731"
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/privacy?id=553834731"
```

**Ratings summary (Bearer / x402):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/ratings?id=553834731"

curl -i "https://api.replynodes.com/v1/appstore/ratings?id=553834731"
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/ratings?id=553834731"
```

**Reviews, paged by country (Bearer / x402):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/reviews?id=553834731&country=us"

curl -i "https://api.replynodes.com/v1/appstore/reviews?id=553834731&country=us"
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/reviews?id=553834731&country=us"
```

**Bounded term search (Bearer / x402):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/search?term=test"

curl -i "https://api.replynodes.com/v1/appstore/search?term=test"
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/search?term=test"
```

**Type-ahead suggestions (Bearer / x402):**

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/appstore/suggest?term=tes&country=us"

curl -i "https://api.replynodes.com/v1/appstore/suggest?term=tes&country=us"
curl -i -H "X-PAYMENT: <base64 payment proof>" \
  "https://api.replynodes.com/v1/appstore/suggest?term=tes&country=us"
```

## Normalized errors

Every non-2xx response uses the envelope above with one of: `400 invalid_request`, `401 invalid_or_expired_token`, `404 not_found`, `429 rate_limited`, `502 upstream_unavailable`, `503 degraded`.
An unauthenticated request to a priced route returns `402` with an x402 v2
challenge, not `401` — `401` is reserved for a Bearer key that is present but
invalid, malformed, expired, or revoked, and the gateway does not fall back
to x402 in that case; it fails closed.
The full meaning table lives in [references/endpoints.md](references/endpoints.md);
retry only idempotent reads on 502/503 with backoff, treat 400/404 as terminal
for the attempt, and honor `Retry-After` on 429.

## Install

Worked steps per agent family (OpenClaw, Hermes, ChatGPT, Claude, generic
HTTP, MCP agents) are in [INSTALL.md](INSTALL.md). Quick reference:

- OpenClaw: Install the skill files (SKILL.md plus llms.txt) into the agent's skill directory; default BASE_URL is https://api.replynodes.com and a workspace key is optional when using x402 v2 negotiation.
- Hermes: Register each tool below as a function/tool definition; execute HTTPS GET requests with a Bearer key or follow x402 v2 payment requirements returned as HTTP 402.
- ChatGPT: Import references/appstore-public-v1.openapi.json as an action schema; configure bearer authentication with the workspace key.
- Claude: Declare the tools via the Model Context Protocol manifest or native tool-use JSON shown in the examples.
- generic HTTP: Any HTTP client works: GET the URL with Authorization: Bearer <key>, or follow the x402 v2 challenge; parse the JSON response.
- MCP agents: Consume references/appstore-mcp.schema.json for JSON-Schema inputs mirroring the capability parameters.

## Honest scope

- Public reads only: no purchase, review submission, account, login, or any other write or authenticated capability exists in this domain, now or later.
- The nine capabilities in this handbook are the live `/v1/appstore/capabilities` surface; anything not listed there is out of scope and requests for it are refused rather than approximated.
- This package is prepared for ClawHub as @replynodes-ai/appstore-api; publication and moderation are not claimed without registry inspect evidence.
- No live availability figures, uptime numbers, latency, or success-rate claims appear anywhere in this package; example payloads in the references are illustrative fixtures, not captured responses.
- No official platform partnership, endorsement, license grant, or data-sharing arrangement is claimed or implied.
- No settlement, auto-credit, instant balance, or wallet-connect UX is claimed anywhere in this package; x402 payment requires a caller-held wallet signing the challenge, and success is a completed request/response, not a balance claim.
- The supported default base URL is https://api.replynodes.com; never use localhost:18789. A workspace may be issued another HTTPS gateway URL explicitly.
