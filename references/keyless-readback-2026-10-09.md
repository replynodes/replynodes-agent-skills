# Keyless production readback

Observed **2026-10-09 UTC** against the canonical ReplyNodes production hosts,
without credentials. This readback supersedes the older keyed-only snapshots in
`canonical-skill-inventory-2026-10-06.md` and `slug-migration-2026-10-07.md`.

| GET route | Result | Rate-limit evidence |
| --- | --- | --- |
| `https://api.replynodes.com/v1/brand/logo?domain=replynodes.com` | `200` JSON | limit `20`, remaining `18`, reset at UTC midnight |
| `https://api.replynodes.com/v1/web/search?query=replynodes` | `400 invalid_request` | limit `10`, remaining `8`, reset at UTC midnight |
| `https://api.replynodes.com/v1/appstore/search?term=notion&country=us&num=1` | `200` JSON | limit `10`, remaining `7`, reset at UTC midnight |
| `https://api.replynodes.com/v1/webcontext/scrape?url=https%3A%2F%2Freplynodes.com%2F` | `200` JSON | limit `10`, remaining `9`, reset at UTC midnight |
| `https://api.replynodes.com/v1/googleplay/search?term=notion&country=us&limit=1` | `200` JSON | limit `10`, remaining `9`, reset at UTC midnight |
| `https://md.replynodes.com/https://replynodes.com/` | `429 anonymous_limit_reached` | limit `20`, remaining `0`, `Retry-After` observed |
| `https://brand.replynodes.com/replynodes.com.json` | `429 anonymous_limit_reached` | limit `20`, remaining `0`, `Retry-After` observed |
| `https://api.replynodes.com/v1/brand/retrieve?domain=replynodes.com` | `401 invalid_or_expired_token` | no anonymous quota; keyed control route |

The Markdown and Brand hosts were already exhausted for the shared client-IP
bucket, so this readback does not claim a fresh `200` response for those hosts.
The documented web-search `text` form returned `504 gateway_timeout` twice;
that is recorded as an upstream availability limitation, not converted into a
success claim. Reddit, YouTube, and Hacker News routes were not probed here.

The observed headers and typed `anonymous_limit_reached` envelope support the
Tier A/Tier B wording in the public skills. This file records production
evidence only; it does not create telemetry or claim retained users.