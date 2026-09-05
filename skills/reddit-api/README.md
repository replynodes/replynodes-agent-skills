# Reddit Public Data API

Published skill slug: `reddit-api`.

This skill provides Bearer-key, pay-per-request access to the documented
read-only Reddit data API for agent research: a subreddit's posts, a single
post, a post's comments, and keyword search, through one HTTPS gateway.
Responses are normalized JSON; Arctic Shift is the primary source and Reddit
RSS is a fallback.

Portable ClawHub-ready skill for the documented Reddit API surface at
`https://api.replynodes.com/v1/reddit/*`.

The gateway uses Bearer workspace-key authentication only; no OAuth, no
Reddit credentials, and no x402 payment challenge is observed on any Reddit
route. The package contains instructions only: it has no service code,
dependencies, credentials, or upstream API access.

The supported routes and access-mode handling are in
[`SKILL.md`](SKILL.md). The package deliberately excludes posting, voting,
commenting, messaging, and all other mutations.
