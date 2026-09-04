# Public provenance

This directory is the public, sanitized provenance source for the ReplyNodes Hacker News read skill published as `@replynodes-ai/hackernews-api`. It contains only portable skill instructions, public API schemas, illustrative fixtures, license text, checksums, and release evidence.

It intentionally excludes service implementation, deployment material, environment files, credentials, payment/payer secrets, and private repository history. The authoritative public routes are `GET /v1/hackernews/stories_top`, `GET /v1/hackernews/stories_new`, `GET /v1/hackernews/stories_best`, `GET /v1/hackernews/stories_ask`, `GET /v1/hackernews/stories_show`, `GET /v1/hackernews/stories_job`, `GET /v1/hackernews/item/{id}`, `GET /v1/hackernews/user/{handle}`, and `GET /v1/hackernews/search`.

The package documents two truthful access outcomes: callers may use a configured Bearer workspace key, or receive HTTP 402 and follow the returned x402 v2 requirements with a separately configured payer. A 402 response is not payment settlement or successful access.

This package is read-only. It does not include submit, vote, comment, favorite, login, or any other write/authenticated capability, and it does not include any platform credential material.

The illustrative fixtures are not captured responses from any live gateway and do not represent availability, uptime, latency, or success-rate figures.