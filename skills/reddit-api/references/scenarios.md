# Scenarios

One worked `curl` example per endpoint. All examples assume:

```bash
export REPLYNODES_API_KEY="<your fetcher API key>"
```

`EXAMPLE_POST_ID` is an illustrative placeholder in every example below — not
a real post id. Get real ids from a list or search response before calling a
single-post route.

## Confirm the gateway and current pricing (free)

```bash
curl "https://api.replynodes.com/v1/reddit/capabilities"
```

## Newest posts in a subreddit

```bash
curl -H "Authorization: Bearer $REPLYNODES_API_KEY" \
  "https://api.replynodes.com/v1/reddit/subreddit_posts/programming?sort=new&limit=10"
```

## A single post by id

```bash
curl -H "Authorization: Bearer $REPLYNODES_API_KEY" \
  "https://api.replynodes.com/v1/reddit/post_by_id/EXAMPLE_POST_ID"
```

## A single post by full URL (permalink)

```bash
curl -H "Authorization: Bearer $REPLYNODES_API_KEY" \
  -G --data-urlencode "url=https://www.reddit.com/r/programming/comments/EXAMPLE_POST_ID/example_post_title/" \
  "https://api.replynodes.com/v1/reddit/post_by_permalink"
```

## Search, optionally scoped to one subreddit

```bash
curl -H "Authorization: Bearer $REPLYNODES_API_KEY" \
  --data-urlencode "q=rust async" -G \
  --data-urlencode "subreddit=programming" \
  --data-urlencode "limit=10" \
  "https://api.replynodes.com/v1/reddit/search_posts"
```

## A user's submitted posts

```bash
curl -H "Authorization: Bearer $REPLYNODES_API_KEY" \
  "https://api.replynodes.com/v1/reddit/user_posts/example_user?sort=new&limit=10"
```

## A user's full activity (posts + comments)

```bash
curl -H "Authorization: Bearer $REPLYNODES_API_KEY" \
  "https://api.replynodes.com/v1/reddit/user_activity/example_user?limit=10"
```

## Handling a missing or invalid fetcher key

A missing, malformed, expired, or revoked `REPLYNODES_API_KEY` returns HTTP
`401` with `code: invalid_or_expired_token`; there is no anonymous or
pay-per-call fallback. Stop and report rather than retrying unchanged:

```bash
curl -sS -H "Authorization: Bearer $REPLYNODES_API_KEY" \
  "https://api.replynodes.com/v1/reddit/post_by_id/EXAMPLE_POST_ID"
# {"error":{"code":"invalid_or_expired_token","message":"...","request_id":"..."}}
```

## Handling a transient upstream error

The gateway already retries `422`/`429`/`502`/`503`/`504` upstream failures
with bounded backoff before returning. If a `502 upstream_unavailable` or
`503 degraded` error still reaches you, treat it as a final failure for that
request — wait briefly and retry the same idempotent `GET` yourself rather
than looping tightly. Failed requests are never charged credits:

```bash
curl -sS -H "Authorization: Bearer $REPLYNODES_API_KEY" \
  "https://api.replynodes.com/v1/reddit/post_by_id/EXAMPLE_POST_ID"
# {"error":{"code":"upstream_unavailable","message":"The data provider is temporarily unavailable.","request_id":"..."}}
```
