---
name: appstore-data-api
title: App Store Public Reads
description: Read-only, normalized public-data reads of App Store applications through the ReplyNodes App Store public-read service: app lookup by track id or bundle id, bounded term search, and related-app listings. Bearer workspace-key authentication or x402 v2 payment negotiation at the gateway, transparent bounded pages, normalized errors, and an explicit unsupported-capability matrix. Public reads only: no purchase, review, account, or other mutation exists, and no platform login material is involved.
version: 1.0.9
contract_version: v1
mode: readonly
auth: Bearer workspace key or x402 v2 negotiation at the gateway; the read layer itself carries no credential material
license: Apache-2.0
keywords: [app store, appstore-data-api, ios, read-only, public data, app metadata, fetcher]
search_terms: [app store, appstore, ios, app lookup, app search, related apps, app metadata, public app data]
entrypoint: SKILL.md
install_guide: INSTALL.md
source: published from the public sanitized provenance repository; review changes in git
---

# App Store Public Reads

Read-only, normalized public-data reads of App Store applications through the ReplyNodes App Store public-read service: app lookup by track id or bundle id, bounded term search, and related-app listings. Bearer workspace-key authentication or x402 v2 payment negotiation at the gateway, transparent bounded pages, normalized errors, and an explicit unsupported-capability matrix. Public reads only: no purchase, review, account, or other mutation exists, and no platform login material is involved.

This directory is the public `appstore-data-api` agent skill package. This public package documents the three supported GET capabilities and their normalized v1 contract.
The supported public gateway base URL is https://api.replynodes.com. Use this deployment base unless your workspace is explicitly issued another HTTPS gateway URL; never use localhost:18789.

## Surface status

- The three documented read operations have stable public contracts with bounded requests and normalized v1 responses.
- Route paths in this catalog are stable capability identifiers used for agent tool bindings; public gateway exposure for this platform is issued to your workspace at onboarding and must not be assumed reachable anywhere else.
- No availability, uptime, latency, or success-rate figure is claimed anywhere in this package; example payloads are illustrative fixtures, not captured responses.

## Package contents

| File | Purpose |
| --- | --- |
| `LICENSE` | Apache-2.0 license copied from the repository root. |
| `SKILL.md` | This handbook (package entrypoint). |
| `INSTALL.md` | Step-by-step installation for every supported agent family. |
| `PUBLICATION.md` | ClawHub publication status, moderation evidence, and claim boundaries. |
| `manifest.json` | Machine-readable inventory: per-file sizes and SHA-256 digests plus the exact capability-to-operation map and unsupported-capability matrix. |
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
- No request path carries or accepts credentials, keys, or login material of any kind; the read layer performs public reads server-side.
- Only public platform data is returned; counters, scores, and prices are null when the source omits them - zeros are never fabricated - and unknown upstream fields are dropped.

## Credential safety

- Authenticate at the gateway exclusively with your ReplyNodes workspace API key; keys are stored server-side only as SHA-256 hashes.
- Never embed the key in client-side code, repositories, logs, screenshots, or support tickets; send it per request in the Authorization header.
- Customer-managed platform credentials are not required, accepted, or stored: callers hold only their ReplyNodes API key while reads run server-side.
- The App Store read layer accepts no credential material on any path; requests carry position and selection data plus an opaque correlation id only.

## Capabilities - exact mapping to implemented read operations

Capabilities cover single-app lookup (by numeric track id or bundle id),
bounded term search, and related-app listings for public App Store data.

| Capability | MCP tool | Route | Matrix operation | Implemented in |
| --- | --- | --- | --- | --- |
| `get_app` | `appstore_get_app` | GET `/v1/appstore/app` | `app` | public read contract |
| `search_apps` | `appstore_search_apps` | GET `/v1/appstore/search` | `search` | public read contract |
| `get_similar_apps` | `appstore_get_similar_apps` | GET `/v1/appstore/similar` | `similar` | public read contract |

This public package is validated for route, schema, checksum, JSON, and credential-safety consistency before release.

## Response envelope

Success: `{ "data": [ <app records> ], "meta": { "request_id": "req-...", "contract_version": "v1", "generated_at": "2026-08-23T00:00:00Z", "availability": "complete" } }`.
Single lookups carry exactly one element in `data`; searches and related
listings carry zero or more; `data` is always present even when empty.
Failure: `{ "error": { "code": "...", "message": "...", "request_id": "req-..." } }`.
`meta.request_id` echoes your opaque correlation id; always quote it in
support requests. Normalized payloads follow contract `v1`: identifiers
are platform-prefixed URNs (`ios:app:<id>`), timestamps are RFC3339 UTC, and
counters, scores, and prices are explicit `null` when the public source omits
them - zeros are never fabricated. Unknown upstream fields are dropped.

## Page bounds

- Search returns one bounded page: limit defaults to 20 when omitted and is clamped client-side to at most 50 regardless of what a caller requests. There are no continuation tokens on this surface.

## Normalized errors

Every non-2xx response uses the envelope above with one of: `400 invalid_request`, `404 not_found`, `429 rate_limited`, `502 upstream_unavailable`, `503 degraded`.
The full meaning table lives in [references/endpoints.md](references/endpoints.md);
retry only idempotent reads on 502/503 with backoff, treat 400/404 as terminal
for the attempt, and honor `Retry-After` on 429.

## Unsupported capabilities

| Capability | Reason | Notes |
| --- | --- | --- |
| `list` | deferred scope | Storefront ranking crawls; high volume, deferred beyond #15. |
| `developer` | deferred scope | Developer catalog enumeration; deferred beyond #15. |
| `reviews` | deferred scope | Paged user reviews; pagination contract deferred beyond #15. |
| `ratings` | deferred scope | Standalone ratings fetch; already embedded in app records. |
| `suggest` | deferred scope | Type-ahead suggestions; deferred beyond #15. |
| `*write_or_authenticated` | read only policy | No purchase, review submission, account, login, or authenticated capability exists on this boundary, now or later. |

Anything not listed under Capabilities is out of scope. Do not improvise
around this matrix; requests for these capabilities are refused rather than
approximated.

## Install

Worked steps per agent family (OpenClaw, Hermes, ChatGPT, Claude, generic
HTTP, MCP agents) are in [INSTALL.md](INSTALL.md). Quick reference:

- OpenClaw: Install the skill files (SKILL.md plus llms.txt) into the agent's skill directory; default BASE_URL is https://api.replynodes.com and a workspace key is optional when using x402 v2 negotiation.
- Hermes: Register each tool below as a function/tool definition; execute HTTPS GET requests with a Bearer key or follow x402 v2 payment requirements returned as HTTP 402.
- ChatGPT: Import references/appstore-public-v1.openapi.json as an action schema; configure bearer authentication with the workspace key.
- Claude: Declare the tools via the Model Context Protocol manifest or native tool-use JSON shown in the examples.
- generic HTTP: Any HTTP client works: GET the URL with Authorization: Bearer <key>; parse the JSON response.
- MCP agents: Consume references/appstore-mcp.schema.json: three read-only tools with JSON-Schema inputs mirroring the capability parameters.

## Honest scope

- Public reads only: no purchase, review submission, account, login, or any other write or authenticated capability exists in this domain, now or later.
- Capabilities beyond the supported matrix (rankings, developer catalogs, reviews, standalone ratings, suggestions) are explicitly unsupported - see the matrix in this handbook; do not improvise around it.
- This package is prepared for ClawHub as @replynodes-ai/appstore-api; publication and moderation are not claimed without registry inspect evidence.
- No live availability figures, uptime numbers, latency, or success-rate claims appear anywhere in this package; example payloads in the references are illustrative fixtures, not captured responses.
- No official platform partnership, endorsement, license grant, or data-sharing arrangement is claimed or implied.
- The supported default base URL is https://api.replynodes.com; never use localhost:18789. A workspace may be issued another HTTPS gateway URL explicitly.
