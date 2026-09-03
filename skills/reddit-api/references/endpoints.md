# Endpoint reference

Base URL: `https://api.replynodes.com/v1/reddit`

All five routes below are the complete public surface. Nothing else is
documented or supported; do not invent additional routes or parameters.

## `GET /capabilities`

Free, no authentication required.

```bash
curl "https://api.replynodes.com/v1/reddit/capabilities"
```

Returns the provider status and the live route/price catalog:

```json
{
  "data": {
    "provider": { "name": "reddit", "status": "available" },
    "routes": [
      "GET /v1/reddit/capabilities (free)",
      "GET /v1/reddit/subreddits/{name}/posts price_micros=3000",
      "GET /v1/reddit/posts/{post_id} price_micros=3000",
      "GET /v1/reddit/posts/{post_id}/comments price_micros=3000",
      "GET /v1/reddit/search price_micros=3000"
    ],
    "service": "reddit-gateway",
    "version": "dev"
  },
  "meta": { "request_id": "<opaque id>" }
}
```

Use this first to confirm the gateway is reachable and pricing has not
changed, at no cost.

## `GET /subreddits/{name}/posts`

$0.003 (3000 USDC micros). Requires `Authorization: Bearer <workspace API key>`.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `name` | path | yes | Subreddit name, no `r/` prefix |
| `sort` | query | no | `new` is confirmed working; other values are not verified against this gateway |
| `limit` | query | no | Positive integer page size; no published maximum — request conservative sizes |

```bash
curl -H "Authorization: Bearer $REDDIT_API_KEY" \
  "https://api.replynodes.com/v1/reddit/subreddits/programming/posts?sort=new&limit=10"
```

Returns `data` as an array of post objects (`id`, `title`, `permalink`,
`url`, `score`, `author`, `subreddit`, `created_at`, `source`).

## `GET /posts/{post_id}`

$0.003. Requires `Authorization: Bearer <workspace API key>`.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `post_id` | path | yes | Reddit's base-36 post id, e.g. the `1w65ged` in `/r/x/comments/1w65ged/...` |

```bash
curl -H "Authorization: Bearer $REDDIT_API_KEY" \
  "https://api.replynodes.com/v1/reddit/posts/EXAMPLE_POST_ID"
```

Returns `data` as a single post object (same fields as the list route above).

## `GET /posts/{post_id}/comments`

$0.003. Requires `Authorization: Bearer <workspace API key>`.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `post_id` | path | yes | Same post id format as above |
| `subreddit` | query | yes | The post's subreddit name; the gateway needs it to resolve the comment thread |
| `limit` | query | no | Positive integer page size; no published maximum |

```bash
curl -H "Authorization: Bearer $REDDIT_API_KEY" \
  "https://api.replynodes.com/v1/reddit/posts/EXAMPLE_POST_ID/comments?subreddit=programming&limit=20"
```

Returns `data` as an array of comment objects (`id`, `body`, `author`,
`permalink`, `created_at`, `source`). `source` may be `arctic-shift` or
`reddit-rss` depending on which upstream served the read.

## `GET /search`

$0.003. Requires `Authorization: Bearer <workspace API key>`.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `q` | query | yes | Search text |
| `subreddit` | query | no | Scopes the search to one subreddit |
| `limit` | query | no | Positive integer page size; no published maximum |

```bash
curl -H "Authorization: Bearer $REDDIT_API_KEY" \
  --data-urlencode "q=rust async" -G \
  --data-urlencode "subreddit=programming" \
  --data-urlencode "limit=10" \
  "https://api.replynodes.com/v1/reddit/search"
```

Returns `data` as an array of post objects (same fields as the list route).

## Errors

See the [Errors table in `SKILL.md`](../SKILL.md#errors) for the full
`code` → HTTP status → meaning mapping, and the retry policy for transient
`422`/`429`/`502`/`503`/`504` upstream failures.
