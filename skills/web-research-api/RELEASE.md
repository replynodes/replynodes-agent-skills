# Release notes

## v1.0.3

- Adds the canonical `summary` frontmatter field used by ClawHub for the
  registry summary, matching the exact public MCP description.
- Preserves the read-only, no-credentials, no-social-write contract and all
  provider routing.

## v1.0.2

- Adds a compact, searchable Web Research API skill covering web search,
  Markdown scraping, crawl and site-map discovery, brand intelligence, Reddit,
  YouTube, and existing ReplyNodes read-only provider APIs.
- Keeps five ClawHub topics: `research`, `web`, `brand`, `reddit`, `youtube`.
- Documents live capability discovery, provider-specific paid/auth behavior,
  no-credentials handling, and the read-only/no-social-write boundary.
- Corrects the public display title and documents provider-specific prepaid
  Bearer access only.
- Sets the public title and summary to the owner-corrected MCP metadata.
