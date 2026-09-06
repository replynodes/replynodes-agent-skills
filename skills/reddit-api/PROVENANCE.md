# Public provenance

This package is authored documentation for the public gateway route surface
under `https://api.replynodes.com/v1/reddit/*`. Route names, prices, the
success/error envelope shape, and the `arctic-shift` / `reddit-rss` source
labels were checked against live responses from the deployed gateway at
review time: the free `GET /capabilities` route (unauthenticated) and
authenticated calls to all six priced routes, each returning HTTP 200 with a
normalized `{ \"data\", \"meta\": { \"request_id\" } }` body. Live example values
(usernames, post ids, titles, request ids) observed during that review are
not reproduced in this package; every example in `SKILL.md` and
`references/` is an illustrative placeholder, clearly labeled as such.

Authentication supports both Bearer workspace-key and x402 v2 pay-per-call; unauthenticated requests to priced routes return HTTP 402 with x402 challenge, and invalid Bearer tokens return HTTP 401.
and invalid-key requests to every priced route returned HTTP 401
`invalid_or_expired_token`, with no x402 payment challenge observed on any
Reddit route. This package confirms x402 v2 pay-per-call support for Reddit routes.

The package intentionally contains no service implementation, upstream
private API details, internal hostnames or ports, raw live payloads, API
keys, or other secrets. The source repository is
`replynodes/replynodes-agent-skills`; the package path is
`skills/reddit-api`.