# Installing the `hackernews-data-api` skill package

Prerequisites:

1. Optional: a ReplyNodes workspace API key (minted from the console); scope and entitlement checks happen at the shared control plane.
2. Use `https://api.replynodes.com` by default, unless your workspace is explicitly issued another HTTPS gateway URL; never use localhost.
3. Keep the key in an environment variable or secret store; do not commit or embed it anywhere.

Before distributing this package, verify it:

```sh
bash scripts/validate-hackernews-api.sh   # from this public repository; must exit 0
```

## OpenClaw

1. Copy this package directory into the OpenClaw agent's skills folder so `SKILL.md` and `llms.txt` are discovered automatically.
2. Set `BASE_URL=https://api.replynodes.com` (or an explicitly issued HTTPS gateway URL). Provide `API_KEY` only through secret configuration when using the Bearer workspace-key path; never print or commit it.
3. If no workspace key is available, stop after an HTTP 402 response and use the returned x402 v2 requirements only with a separately configured payer; this package does not claim settlement or paid success.
4. Instruct naturally, for example: "Look up item 1 with the hackernews-data-api skill and report meta.availability and meta.missing_fields honestly."

## Hermes

1. Register the nine function definitions printed in [references/endpoints.md](references/endpoints.md) (Hermes-style function-calling section).
2. Execute each call by issuing the mapped HTTPS GET with the Authorization header set.
3. There are no continuation tokens for `get_item` or `get_user`; feeds and search return one bounded page (default 20, max 50) plus an opaque `meta.next_cursor` when more pages exist.

## ChatGPT

1. Import [references/hackernews-public-v1.openapi.json](references/hackernews-public-v1.openapi.json) as an action schema.
2. Choose API-key authentication with the Bearer scheme; save the workspace key as a stored credential rather than pasting it into conversations.
3. Exactly nine operations exist (`get_stories_top`, `get_stories_new`, `get_stories_best`, `get_stories_ask`, `get_stories_show`, `get_stories_job`, `get_item`, `get_user`, `search`) and all are GET-only; nothing else can be invoked.

## Claude

1. Preferred: point an MCP-compatible client at [references/hackernews-mcp.schema.json](references/hackernews-mcp.schema.json) (streamable HTTP transport, bearer authentication).
2. Alternative: declare the native tool-use JSON from [references/endpoints.md](references/endpoints.md) directly in your tool list.
3. Surface `meta.availability`, `meta.missing_fields`, and null counters honestly to the user instead of inventing plausible values; do not retry on `unavailable` without an explicit user instruction.

## Generic HTTP client

Every documented route is a single HTTPS GET against the base URL with optional query parameters. Auth is one of:

- `Authorization: Bearer ***` — workspace key path.
- (no auth header) — receive HTTP 402 with `payment-required` header, then re-issue the request including `X-PAYMENT` with an x402 v2 payload signed by a configured payer.

There is no other auth mode. There is no SDK; everything is plain HTTP.