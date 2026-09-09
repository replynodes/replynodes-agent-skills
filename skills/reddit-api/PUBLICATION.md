# Publication record

Prepared for ClawHub as `reddit-api`, display title **Reddit Public Data API**, version `1.1.0`.

The registry is the source of truth for publication and moderation status.
This file does not claim publication, moderation approval, ratings, or live
availability until verified with `clawhub inspect --json`.

Publication metadata must identify the source repository, reviewed commit, git
ref, and package path. Publish only from a clean extracted archive.

Reviewed source commit: `35e041aa0858ef26c7e5dc9e7b3306679feb4edb` on ref
`feat/fomo-app-data-api-clawhub`, package path `skills/reddit-api`.

The package describes a single Bearer ReplyNodes fetcher API key
authentication path, drawing down prepaid credit, observed at the gateway;
the gateway returns HTTP 401 `invalid_or_expired_token` for a missing,
malformed, expired, or revoked key. There is no anonymous, wallet, or
pay-per-call path. No Reddit credential material is involved.