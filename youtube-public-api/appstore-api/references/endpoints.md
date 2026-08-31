# Endpoint examples - App Store Data API (v1)

All operations below are GET-only public reads. Replace `BASE_URL` with your
workspace gateway URL and `API_KEY` with your ReplyNodes fetcher API key.
Never commit real keys.

- The three supported read operations are implemented and behavior-tested today in services/appstore-fetcher (issue #15): capability gating before any egress, explicit egress allowlisting including redirects, bounded timeouts and response sizes, and strict normalization into the v1 contract.
- Route paths in this catalog are stable capability identifiers used for agent tool bindings; public gateway exposure for this platform is issued to your workspace at onboarding and must not be assumed reachable anywhere else.
- No availability, uptime, latency, or success-rate figure is claimed anywhere in this package; example payloads are illustrative fixtures, not captured responses.

## Generic HTTP (curl)

### GET /v1/appstore/app - lookup by track id

```sh
curl -sS \
  -H 'Authorization: Bearer API_KEY' \
  "BASE_URL/v1/appstore/app?id=1234567890"
```

### GET /v1/appstore/app - lookup by bundle id

```sh
curl -sS \
  -H 'Authorization: Bearer API_KEY' \
  "BASE_URL/v1/appstore/app?appId=com.example.app"
```

### GET /v1/appstore/search

```sh
curl -sS \
  -H 'Authorization: Bearer API_KEY' \
  "BASE_URL/v1/appstore/search?term=example&limit=5&country=us&language=en-us"
```

`limit` defaults to 20 and is clamped client-side to at most 50.

### GET /v1/appstore/similar

```sh
curl -sS \
  -H 'Authorization: Bearer API_KEY' \
  "BASE_URL/v1/appstore/similar?id=1234567890&country=us"
```

### Sample success payload (normalized v1 shape; illustrative fixture,
### not a captured response)

```json
{
  "data": [
    {
      "id": "ios:app:1234567890",
      "platform": "ios",
      "bundle_id": "com.example.app",
      "title": "Example App",
      "url": "https://apps.example.com/example-app",
      "icon_url": null,
      "description": "An illustrative application used by documentation fixtures.",
      "release_notes": "Documentation fixture release notes.",
      "developer": {
        "name": "Example Developer",
        "id": "ios:developer:987654321"
      },
      "primary_genre": "Productivity",
      "genres": ["Productivity"],
      "content_rating": "4+",
      "languages": ["EN"],
      "version": "1.0.0",
      "size_bytes": null,
      "min_os_version": "15.0",
      "released_at": "2025-03-01T00:00:00Z",
      "updated_at": "2026-07-15T00:00:00Z",
      "rating": { "score": 4.2, "ratings_count": 128, "reviews_count": null },
      "pricing": { "price": null, "currency": null, "free": true },
      "screenshot_urls": []
    }
  ],
  "meta": {
    "request_id": "req-8f14e45fce",
    "contract_version": "v1",
    "generated_at": "2026-08-23T00:00:00Z",
    "availability": "partial",
    "missing_fields": ["*.icon_url", "*.pricing.price", "*.pricing.currency", "*.rating.reviews_count", "*.size_bytes"],
    "detail": "Some fields were omitted by the upstream source."
  }
}
```

`null` means the public source omitted the value; zeros are never fabricated.
`meta.missing_fields` uses dotted `*.paths` that apply to every element of
`data`, reported in a fixed deterministic order.

### Handling errors and quotas

```sh
# 429 example - honor Retry-After before retrying
curl -sS -i \
  -H 'Authorization: Bearer API_KEY' \
  "BASE_URL/v1/appstore/app?id=1234567890"
# HTTP/1.1 429 Too Many Requests
# Retry-After: 30
# ...
{"error":{"code":"rate_limited","message":"The upstream quota is exhausted; retry later.","request_id":"req-0f341b6a2c"}}
```

Retry guidance: retry idempotent reads on 502/503 with backoff; treat
400/404 as terminal for the request.

## OpenClaw agents

Install this skill directory into the agent's skills folder so `SKILL.md` and
`llms.txt` are discoverable, then instruct it naturally:

```text
Use the ReplyNodes App Store skill to look up com.example.app, then find
related apps and summarize ratings. Surface meta.availability and null
counters honestly, and respect any 429 Retry-After you receive.
```

The agent resolves BASE_URL/API_KEY from its environment configuration; the
skill text never contains either.

## Hermes-style function calling

Register the three tools; execute by issuing the mapped HTTPS GET:

```json
[
  {
    "name": "appstore_get_app",
    "description": "Look up one public App Store application. GET /v1/appstore/app returns exactly one normalized public application record for the numeric track id or bundle id supplied via the id or appId query parameter, per contract v1 (developer, rating, pricing, genres, languages, version, release data). Callers authenticate with a ReplyNodes Bearer workspace key or settle 0.001 USDC per call via x402 v2 pay-per-request payment (HTTP 402) - no account or API key is required on the x402 path. An unknown or non-public id yields not_found.",
    "parameters": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string",
          "description": "Numeric track id (up to 19 digits) or reverse-DNS-style bundle id; provide id or appId.",
          "pattern": "^([0-9]{1,19}|[A-Za-z0-9][A-Za-z0-9-]*(?:\\.[A-Za-z0-9-]+)+)$",
          "minLength": 3,
          "maxLength": 200
        },
        "appId": {
          "type": "string",
          "description": "Alias for id; provide appId or id.",
          "pattern": "^([0-9]{1,19}|[A-Za-z0-9][A-Za-z0-9-]*(?:\\.[A-Za-z0-9-]+)+)$",
          "minLength": 3,
          "maxLength": 200
        },
        "country": {
          "type": "string",
          "description": "Optional storefront hint, ISO 3166-1 alpha-2 lowercase (e.g. us).",
          "pattern": "^[a-z]{2}$"
        },
        "language": {
          "type": "string",
          "description": "Optional language hint, ISO 639-1 lowercase optionally followed by -<region> (e.g. en or en-us).",
          "pattern": "^[a-z]{2}(-[a-z]{2})?$"
        }
      },
      "required": [],
      "additionalProperties": false
    }
  },
  {
    "name": "appstore_search_apps",
    "description": "Search public App Store applications by term. GET /v1/appstore/search returns zero or more normalized public application records matching the free-text term query parameter, as one bounded page (default 20 results, clamped to at most 50; no continuation tokens exist on this surface). Callers authenticate with a ReplyNodes Bearer workspace key or settle 0.002 USDC per call via x402 v2 pay-per-request payment (HTTP 402) - no account or API key is required on the x402 path.",
    "parameters": {
      "type": "object",
      "properties": {
        "term": {
          "type": "string",
          "description": "Free-text search query; required and never empty after trimming.",
          "pattern": "^\\S(.*)?$"
        },
        "limit": {
          "type": "integer",
          "description": "Page size bound; defaults to 20 and is clamped to at most 50 client-side.",
          "minimum": 1,
          "maximum": 50,
          "default": 20
        },
        "country": {
          "type": "string",
          "description": "Optional storefront hint, ISO 3166-1 alpha-2 lowercase (e.g. us).",
          "pattern": "^[a-z]{2}$"
        },
        "language": {
          "type": "string",
          "description": "Optional language hint, ISO 639-1 lowercase optionally followed by -<region> (e.g. en or en-us).",
          "pattern": "^[a-z]{2}(-[a-z]{2})?$"
        }
      },
      "required": [
        "term"
      ],
      "additionalProperties": false
    }
  },
  {
    "name": "appstore_get_similar_apps",
    "description": "List public apps related to one App Store application. GET /v1/appstore/similar returns zero or more normalized public application records related to the app referenced by the id or appId query parameter; no continuation tokens exist on this surface. Callers authenticate with a ReplyNodes Bearer workspace key or settle 0.0015 USDC per call via x402 v2 pay-per-request payment (HTTP 402) - no account or API key is required on the x402 path.",
    "parameters": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string",
          "description": "Numeric track id (up to 19 digits) or reverse-DNS-style bundle id; provide id or appId.",
          "pattern": "^([0-9]{1,19}|[A-Za-z0-9][A-Za-z0-9-]*(?:\\.[A-Za-z0-9-]+)+)$",
          "minLength": 3,
          "maxLength": 200
        },
        "appId": {
          "type": "string",
          "description": "Alias for id; provide appId or id.",
          "pattern": "^([0-9]{1,19}|[A-Za-z0-9][A-Za-z0-9-]*(?:\\.[A-Za-z0-9-]+)+)$",
          "minLength": 3,
          "maxLength": 200
        },
        "country": {
          "type": "string",
          "description": "Optional storefront hint, ISO 3166-1 alpha-2 lowercase (e.g. us).",
          "pattern": "^[a-z]{2}$"
        },
        "language": {
          "type": "string",
          "description": "Optional language hint, ISO 639-1 lowercase optionally followed by -<region> (e.g. en or en-us).",
          "pattern": "^[a-z]{2}(-[a-z]{2})?$"
        }
      },
      "required": [],
      "additionalProperties": false
    }
  }
]
```

## ChatGPT actions (OpenAPI import)

1. Import `openapi/appstore-public-v1.openapi.json` as an action schema.
2. Choose *API key* auth with the *Bearer* scheme and supply the workspace key
   as a saved credential (never paste it into conversations).
3. The three operations appear under their operationIds `get_app`,
   `search_apps`, and `get_similar_apps`, limited to GET requests.

## Claude tool use

Declare the same three tools via native tool-use definitions or point an MCP
client at `mcp/appstore-mcp.schema.json`. Tool results are the raw JSON
responses shown above - surface `meta.availability` and null counters honestly
to the user instead of inventing values.

## MCP agents

Manifest: `mcp/appstore-mcp.schema.json`. It declares transport (HTTP with
bearer authentication), server `instructions`, and three read-only tools
(`appstore_get_app`, `appstore_search_apps`, `appstore_get_similar_apps`)
whose input schemas mirror the capability parameters exactly. Distribution
note inside the manifest marks it as a local artifact; registry publication
is out of scope.

## Error reference

| HTTP | Code | Meaning |
| --- | --- | --- |
| 400 | `invalid_request` | Malformed input such as a bad id, empty term, or out-of-range limit. |
| 404 | `not_found` | Resource does not exist or is not public. |
| 429 | `rate_limited` | Quota exhausted; honor Retry-After before retrying. |
| 502 | `upstream_unavailable` | The public read could not be completed at this time; retry later. |
| 503 | `degraded` | Operation not enabled (dormant or killed) or fail-closed state. |

## Unsupported capabilities (do not improvise)

| Capability | Reason | Notes |
| --- | --- | --- |
| `list` | deferred scope | Storefront ranking crawls; high volume, deferred beyond #15. |
| `developer` | deferred scope | Developer catalog enumeration; deferred beyond #15. |
| `reviews` | deferred scope | Paged user reviews; pagination contract deferred beyond #15. |
| `ratings` | deferred scope | Standalone ratings fetch; already embedded in app records. |
| `suggest` | deferred scope | Type-ahead suggestions; deferred beyond #15. |
| `*write_or_authenticated` | read only policy | No purchase, review submission, account, login, or authenticated capability exists on this boundary, now or later. |

Regenerate this file with `bash ../catalog/generate_appstore.sh` after editing
catalog_appstore.json.
