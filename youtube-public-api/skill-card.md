# YouTube Data API

- **Slug:** `youtube-public-api`
- **Version:** `1.0.4`
- **Purpose:** Read-only YouTube public-data agent intents — search YouTube videos, video/channel/playlist metadata, public comments, related videos, and transcripts — as normalized structured JSON through seven `GET` routes.
- **Payment:** Pay-per-request in USDC via x402 v2 on Base (`eip155:8453`); no ReplyNodes account or API key required on that path. Optional Bearer workspace API key is a separate, non-payment path.
- **Authentication:** Optional ReplyNodes workspace Bearer API key when supported; never request secrets in chat.
- **Safety:** No login, cookies, private data, writes, wallet access, payment signing, or settlement.
- **x402:** HTTP 402 is payment-requirement negotiation evidence only. It does not prove payment or data access.
- **Transcript:** May be unavailable; report the returned unavailable/error status verbatim.
