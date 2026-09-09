# Reddit Public Data API

Published skill slug: `reddit-api`.

This skill provides Bearer-key, prepaid-credit access to the documented
read-only Reddit data API for agent research: a subreddit's posts, a single
post, a user's activity, and keyword search, through one HTTPS gateway.
Responses are normalized JSON; Arctic Shift is the primary source and Reddit
RSS is a fallback.

Portable ClawHub-ready skill for the documented Reddit API surface at
`https://api.replynodes.com/v1/reddit/*`.

The gateway accepts a single Bearer ReplyNodes fetcher API key that draws
down prepaid credit; there is no anonymous, wallet, or pay-per-call path,
and no OAuth or Reddit credentials are involved. See [`SKILL.md`](SKILL.md)'s
Setup section to create the account and mint the key. The package contains
instructions only: it has no service code, dependencies, credentials, or
upstream API access.

The supported routes and access-mode handling are in
[`SKILL.md`](SKILL.md). The package deliberately excludes posting, voting,
commenting, messaging, and all other mutations.
