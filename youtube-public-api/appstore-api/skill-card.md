# App Store Data API

- **Slug:** `appstore-api`
- **Version:** `1.1.0`
- **License:** `Apache-2.0`
- **Mode:** `readonly`
- **Summary:** Read-only, normalized public-data reads of App Store applications through the ReplyNodes fetcher domain: app lookup by track id or bundle id, bounded term search, and related-app listings. Bearer workspace-key authentication or x402 v2 pay-per-request payment in USDC (no account or API key required on the x402 path), transparent bounded pages, normalized errors, and an explicit unsupported-capability matrix. Public reads only: no purchase, review, account, or other mutation exists, and no platform login material is involved.

This card describes only the documented GET capabilities in `manifest.json`.
It does not claim registry publication, live availability, payment settlement,
platform endorsement, or write/account access.
