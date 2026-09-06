# Installing the `reddit-data-api` skill package

Prerequisites:
1. Optional: a ReplyNodes workspace API key (minted from the console); scope and entitlement checks happen at the shared control plane.
2. Use `https://api.replynodes.com`; do not use any other gateway.
3. Keep the key in an environment variable or secret store; do not commit or embed it anywhere.

Before distributing this package, verify it:

```sh
bash scripts/validate-reddit-api.sh   # from this public repository; must exit 0
```

## OpenClaw

1. Copy this package directory into the OpenClaw agent's skills folder so `SKILL.md` and `llms.txt` are discovered automatically.
2. Set `BASE_URL=https://api.replynodes.com` (fixed). Provide `API_KEY` only through secret configuration when using the Bearer workspace-key path; never print or commit it.
3. If no workspace key is available, stop after an HTTP 402 response and use the returned x402 v2 requirements only with a separately configured payer; this package does not claim settlement or paid success.
4. Instruct naturally, for example: "Look up r/programming with the reddit-data-api skill, list new posts, and report meta.availability and null counters honestly."

## Hermes

1. Register the seven function definitions printed in [references/endpoints.md](references/endpoints.md) (Hermes-style function-calling section).
2. Execute each call by issuing the mapped HTTPS GET with the Authorization header set.
3. There are no continuation tokens: search returns one bounded page (default 20, max 50).

## ChatGPT

1. Import [references/reddit-public-v1.openapi.json](references/reddit-public-v1.openapi.json) as an action schema.
   Note: This file does not exist in this skill; instead, use the endpoints documented in references/endpoints.md.
2. Choose API-key authentication with the Bearer scheme; save the workspace key as a stored credential rather than pasting it into conversations.
3. Exactly seven operations exist (`get_capabilities`, `get_subreddit_posts`, `get_post_by_id`, `get_post_by_permalink`, `search_posts`, `get_user_posts`, `get_user_activity`) and all are GET-only; nothing else can be invoked.

## Claude

1. Preferred: point an MCP-compatible client at [references/reddit-api-mcp.schema.json](references/reddit-api-mcp.schema.json) (streamable HTTP transport, bearer authentication).
2. Alternative: declare the native tool-use JSON from [references/endpoints.md](references/endpoints.md) directly in your tool list.
3. Surface `meta.availability`, `meta.missing_fields`, and null counters honestly to the user instead of inventing values.

## generic HTTP

1. Call any documented route with the client of your choice; worked curl snippets live in [references/endpoints.md](references/endpoints.md).
2. Send the Authorization header on every documented request.
3. Retry only on 502/503 with backoff; treat 400/404 as terminal for the attempt and honor `Retry-After` on 429.

## MCP agents

1. Load [references/reddit-api-mcp.schema.json](references/reddit-api-mcp.schema.json) as the server manifest.
2. Substitute `{base_url}` in the transport URL with your workspace gateway base URL.
3. Expose exactly the seven declared read-only tools; they map 1:1 onto the implemented operations recorded in `manifest.json`.

Uninstalling removes the copied directory and nothing else: the package installs no daemons, hooks, or background activity of any kind.