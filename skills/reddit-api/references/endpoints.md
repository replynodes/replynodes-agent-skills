# Endpoint reference

Base URL: `https://api.replynodes.com/v1/reddit`

All seven routes below are the complete public surface. Nothing else is
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
      "GET /v1/reddit/subreddit_posts/{subreddit} price_micros=1000",
      "GET /v1/reddit/post_by_id/{id} price_micros=1000",
      "GET /v1/reddit/post_by_permalink price_micros=1000",
      "GET /v1/reddit/search_posts price_micros=1000",
      "GET /v1/reddit/user_posts/{username} price_micros=1000",
      "GET /v1/reddit/user_activity/{username} price_micros=1000"
    ],
    "service": "replynodes-fetcher",
    "version": "dev"
  },
  "meta": { "request_id": "<opaque id>" }
}
```

Use this first to confirm the gateway is reachable and pricing has not
changed, at no cost.

## `GET /v1/reddit/subreddit_posts/{subreddit}`

$0.001 (1000 USDC micros). Requires `Authorization: Bearer *** API key>` or x402 v2 payment.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `subreddit` | path | yes | Subreddit name, no `r/` prefix |
| `sort` | query | no | `new`/`hot`/`top` confirmed working |
| `limit` | query | no | Positive integer page size; no published maximum — request conservative sizes |

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/reddit/subreddit_posts/programming?sort=new&limit=10"
```

Returns `data` as an array of post objects (`id`, `title`, `permalink`, `url`, `score`, `author`, `subreddit`, `created_at`, `source`).

## `GET /v1/reddit/post_by_id/{id}`

$0.001 (1000 USDC micros). Requires `Authorization: Bearer *** API key>` or x402 v2 payment.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `id` | path | yes | Reddit's base-36 post id, e.g. the `1w65ged` in `/r/x/comments/1w65ged/...` |

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/reddit/post_by_id/EXAMPLE_POST_ID"
```

Returns `data` as a single post object (same fields as the list route above).

## `GET /v1/reddit/post_by_permalink`

$0.001 (1000 USDC micros). Requires `Authorization: Bearer *** API key>` or x402 v2 payment.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `url` | query | yes | Full Reddit post URL |

```bash
curl -H "Authorization: Bearer ***" \
  -G --data-urlencode "url=https://www.reddit.com/r/programming/comments/EXAMPLE_POST_ID/example_post_title/" \
  "https://api.replynodes.com/v1/reddit/post_by_permalink"
```

Returns `data` as a single post object (same fields as the list route above).

## `GET /v1/reddit/search_posts`

$0.001 (1000 USDC micros). Requires `Authorization: Bearer *** API key>` or x402 v2 payment.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `q` | query | yes | Search text |
| `subreddit` | query | no | Scopes the search to one subreddit |
| `limit` | query | no | Positive integer page size; no published maximum |

```bash
curl -H "Authorization: Bearer ***" \
  --data-urlencode "q=rust async" -G \
  --data-urlencode "subreddit=programming" \
  --data-urlencode "limit=10" \
  "https://api.replynodes.com/v1/reddit/search_posts"
```

Returns `data` as an array of post objects (same fields as the list route).

## `GET /v1/reddit/user_posts/{username}`

$0.001 (1000 USDC micros). Requires `Authorization: Bearer *** API key>` or x402 v2 payment.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `username` | path | yes | Reddit username |
| `sort` | query | no | `new`/`hot`/`top` confirmed working |
| `limit` | query | no | Positive integer page size; no published maximum — request conservative sizes |

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/reddit/user_posts/example_user?sort=new&limit=10"
```

Returns `data` as an array of post objects (same fields as the list route).

## `GET /v1/reddit/user_activity/{username}`

$0.001 (1000 USDC micros). Requires `Authorization: Bearer *** API key>` or x402 v2 payment.

| Parameter | Location | Required | Notes |
| --- | --- | --- | --- |
| `username` | path | yes | Reddit username |
| `limit` | query | no | Positive integer page size; no published maximum — request conservative sizes |

```bash
curl -H "Authorization: Bearer ***" \
  "https://api.replynodes.com/v1/reddit/user_activity/example_user?limit=10"
```

Returns `data` as an array of objects representing combined post and comment activity (with `type` field indicating "post" or "comment"), same fields as individual post/comment objects.

## Errors

See the [Errors table in `SKILL.md`](../SKILL.md#errors) for the full
`code` → HTTP status → meaning mapping, and the retry policy for transient
`422`/`429`/`502`/`503`/`504` upstream failures.