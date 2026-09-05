# Scenarios

One worked `curl` example per endpoint. All examples assume:

```bash
export REDDIT_API_KEY="<your workspace API key>"
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
curl -H "Authorization: Bearer $REDDIT_API_KEY" \
  "https://api.replynodes.com/v1/reddit/subreddits/programming/posts?sort=new&limit=10"
```

## A single post by id

```bash
curl -H "Authorization: Bearer $REDDIT_API_KEY" \
  "https://api.replynodes.com/v1/reddit/posts/EXAMPLE_POST_ID"
```

## A post's comments

`subreddit` is required — the gateway needs it to resolve the comment thread.

```bash
curl -H "Authorization: Bearer $REDDIT_API_KEY" \
  "https://api.replynodes.com/v1/reddit/posts/EXAMPLE_POST_ID/comments?subreddit=programming&limit=20"
```

## Search, optionally scoped to one subreddit

```bash
curl -H "Authorization: Bearer $REDDIT_API_KEY" \
  --data-urlencode "q=rust async" -G \
  --data-urlencode "subreddit=programming" \
  --data-urlencode "limit=10" \
  "https://api.replynodes.com/v1/reddit/search"
```

## Handling a transient upstream error

The gateway already retries `422`/`429`/`502`/`503`/`504` upstream failures
with bounded backoff before returning. If a `502 upstream_unavailable` or
`503 degraded` error still reaches you, treat it as a final failure for that
request — wait briefly and retry the same idempotent `GET` yourself rather
than looping tightly:

```bash
curl -sS -H "Authorization: Bearer $REDDIT_API_KEY" \
  "https://api.replynodes.com/v1/reddit/posts/EXAMPLE_POST_ID"
# {"error":{"code":"upstream_unavailable","message":"The data provider is temporarily unavailable.","request_id":"..."}}
```
