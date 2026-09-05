## Changelog (relative to live 1.0.4)
- 1.0.5: Body rewrite to match live prod after fetcher#187 added x402 v2 pay-per-call. Authentication section documents both Bearer workspace-key and x402 v2 paths with link to https://replynodes.com/topup?skill=reddit-api (T3 live). Endpoints table corrected to the 6 actual /v1/reddit/{op} routes at $0.001 each (per /v1/reddit/capabilities). Quick reference, Scenarios, and Response shape sections updated to the new path shape.
- 1.0.4 (already live): force-promote to latest.
- 1.0.3: Bearer-key skill description (was never published — superseded).
- 1.0.2: SEO + topics + categories.
- 1.0.1: initial release.

## Versioning note
v1.0.5 includes the new x402 pay-per-call authentication path. The live
1.0.4 description was stale (still said "One mode only Bearer") because
the force-promote did not carry the body changes. v1.0.5 is the first
release where the full skill body matches the prod fetcher behavior.
