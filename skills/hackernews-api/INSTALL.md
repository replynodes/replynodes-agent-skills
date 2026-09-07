# Installing the `hackernews-data-api` skill package

This package performs anonymous, read-only HTTPS GETs against the public Hacker News gateway.

1. Copy this package directory into the agent's skills folder so `SKILL.md` and `llms.txt` are discovered.
2. Use `https://api.replynodes.com` as the gateway base URL; never use localhost or an untrusted endpoint.
3. No API key, wallet, payment proof, cookie, session, or other credential is required or requested for the documented Hacker News reads.

For source maintainers, run repository-level validation before distribution. For an extracted package, verify the immutable inventory directly:

```sh
sha256sum -c CHECKSUMS.txt
```

## OpenClaw

1. Load the copied skill package.
2. Call the documented HTTPS GET route without an `Authorization` header.
3. Report `meta.availability`, `meta.missing_fields`, cursors, and null counters honestly; never invent values.

## Hermes

1. Register the nine function definitions in [references/endpoints.md](references/endpoints.md).
2. Execute the mapped anonymous HTTPS GET for each function.
3. Feeds and search return one bounded page (default 20, max 50) and may include an opaque `meta.next_cursor`; `get_item` and `get_user` do not paginate.

## ChatGPT

1. Import [references/hackernews-public-v1.openapi.json](references/hackernews-public-v1.openapi.json) as an action schema.
2. Use the anonymous server definition; do not configure Bearer credentials or payment actions.
3. Exactly nine operations exist and all are GET-only: `get_stories_top`, `get_stories_new`, `get_stories_best`, `get_stories_ask`, `get_stories_show`, `get_stories_job`, `get_item`, `get_user`, and `search`.

## Claude / MCP

1. Load [references/hackernews-mcp.schema.json](references/hackernews-mcp.schema.json).
2. Use the streamable HTTP transport without an authentication header.
3. Expose only the nine declared read-only tools.

## Generic HTTP client

Every documented route is a single anonymous HTTPS GET against the gateway with optional documented query or path parameters. There is no SDK, credential setup, wallet signing, payment flow, or write capability.

Uninstalling removes only the copied skill directory; the package installs no daemons, hooks, scripts, or background activity.