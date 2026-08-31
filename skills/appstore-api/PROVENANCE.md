# Public provenance

This directory is the public, sanitized provenance source for the ReplyNodes App Store read skill published as `@replynodes-ai/appstore-api`. It contains only portable skill instructions, public API schemas, illustrative fixtures, license text, checksums, and release evidence.

It intentionally excludes service implementation, deployment material, environment files, credentials, payment/payer secrets, and private repository history. The authoritative public routes are `GET /v1/appstore/app`, `GET /v1/appstore/search`, and `GET /v1/appstore/similar`.

The package documents two truthful access outcomes: callers may use a configured Bearer workspace key, or receive HTTP 402 and follow the returned x402 v2 requirements with a separately configured payer. A 402 response is not payment settlement or successful access.
