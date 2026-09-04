# Hacker News Public Reads — Endpoints

This file is the canonical endpoint catalog for the `hackernews-data-api` skill.
Use it as the source for Hermes function declarations, Claude tool-use JSON, and ad-hoc curl examples.

Base URL: `https://api.replynodes.com` (do not use localhost; never print or commit a workspace key).

All routes return the normalized v1 envelope described in `SKILL.md`:

```json
{
  "data": <T | [T, ...]>,
  "meta": {
    "request_id": "<string>",
    "provider": "hackernews",
    "endpoint": "<canonical path>",
    "next_cursor": "<string | null>",
    "availability": "available | rate_limited | unavailable",
    "missing_fields": ["<field>", ...],
    "fetched_at": "<RFC3339 timestamp>"
  }
}
```

A failed request (any non-2xx except 402) is never charged; the prepaid credit debit only settles after the upstream read returns a 2xx, and x402 v2 settlement happens only on the same condition.

## Hermes function declarations

```json
[
  {
    "name": "hackernews_get_stories_top",
    "description": "List front-page Hacker News stories (bounded page).",
    "parameters": {
      "type": "object",
      "properties": {
        "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20, "description": "Page size bound; clamped at 50."},
        "page": {"type": "integer", "minimum": 1, "description": "1-indexed page number; mutually exclusive with cursor."},
        "cursor": {"type": "string", "description": "Opaque continuation token from a prior meta.next_cursor."}
      }
    }
  },
  {
    "name": "hackernews_get_stories_new",
    "description": "List newest Hacker News stories (bounded page).",
    "parameters": {"$ref": "#/definitions/pagination"}
  },
  {
    "name": "hackernews_get_stories_best",
    "description": "List best Hacker News stories (bounded page).",
    "parameters": {"$ref": "#/definitions/pagination"}
  },
  {
    "name": "hackernews_get_stories_ask",
    "description": "List Ask HN stories (bounded page).",
    "parameters": {"$ref": "#/definitions/pagination"}
  },
  {
    "name": "hackernews_get_stories_show",
    "description": "List Show HN stories (bounded page).",
    "parameters": {"$ref": "#/definitions/pagination"}
  },
  {
    "name": "hackernews_get_stories_job",
    "description": "List Hacker News jobs postings (bounded page).",
    "parameters": {"$ref": "#/definitions/pagination"}
  },
  {
    "name": "hackernews_get_item",
    "description": "Fetch one Hacker News item with bounded comment thread.",
    "parameters": {
      "type": "object",
      "required": ["id"],
      "properties": {
        "id": {"type": "integer", "description": "Numeric Hacker News item id."},
        "depth": {"type": "integer", "minimum": 0, "maximum": 8, "default": 3, "description": "Max comment depth to inline; deeper comments are dropped and reported in meta.missing_fields."}
      }
    }
  },
  {
    "name": "hackernews_get_user",
    "description": "Fetch one public Hacker News user profile.",
    "parameters": {
      "type": "object",
      "required": ["handle"],
      "properties": {
        "handle": {"type": "string", "description": "Hacker News username (case-sensitive)."}
      }
    }
  },
  {
    "name": "hackernews_search",
    "description": "Search Hacker News by free-text term with optional tag filters.",
    "parameters": {
      "type": "object",
      "required": ["q"],
      "properties": {
        "q": {"type": "string", "minLength": 1, "description": "Free-text search query; required and never empty after trimming."},
        "tags": {"type": "string", "description": "Comma-separated tag filters (story, comment, poll, show_hn, ask_hn, front_page)."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
        "page": {"type": "integer", "minimum": 1},
        "cursor": {"type": "string"}
      }
    }
  }
]
```

`pagination` definition (used by feed/search functions):

```json
{
  "pagination": {
    "type": "object",
    "properties": {
      "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
      "page": {"type": "integer", "minimum": 1},
      "cursor": {"type": "string"}
    }
  }
}
```

## curl examples (Bearer workspace key)

```sh
curl -sS https://api.replynodes.com/v1/hackernews/stories_top \
  -H "Authorization: Bearer ***"
```

```sh
curl -sS "https://api.replynodes.com/v1/hackernews/item/1?depth=3" \
  -H "Authorization: Bearer ***"
```

```sh
curl -sS "https://api.replynodes.com/v1/hackernews/user/pg" \
  -H "Authorization: Bearer ***"
```

```sh
curl -sS "https://api.replynodes.com/v1/hackernews/search?q=agi&tags=story,show_hn&limit=20" \
  -H "Authorization: Bearer ***"
```

## curl example (x402 v2 accountless)

```sh
# 1. Probe without auth to get 402 + payment-required header
curl -sSi https://api.replynodes.com/v1/hackernews/stories_top

# 2. Re-issue same call with X-PAYMENT carrying a signed x402 v2 payload
curl -sS https://api.replynodes.com/v1/hackernews/stories_top \
  -H "X-PAYMENT: <base64 x402 payload>"
```

The 402 body is the requirements advertisement, not settlement or successful paid access. Settlement happens only when the upstream read returns 2xx.

## What this catalog does not claim

- No claim that a 402 response is payment settlement or successful paid access.
- No claim of registry publication status; see `PUBLICATION.md` for that.
- No claim of upstream availability, uptime, latency, or success rate.
- No claim that any illustrative example reflects a captured live response.