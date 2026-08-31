# YouTube Public Data

- **Slug:** `youtube-public-api`
- **Version:** `1.0.1`
- **Purpose:** Read public YouTube data through seven `GET` routes.
- **Authentication:** Optional ReplyNodes workspace Bearer API key when supported; never request secrets in chat.
- **Safety:** No login, cookies, private data, writes, wallet access, payment signing, or settlement.
- **x402:** HTTP 402 is payment-requirement negotiation evidence only. It does not prove payment or data access.
- **Transcript:** May be unavailable; report the returned unavailable/error status verbatim.
