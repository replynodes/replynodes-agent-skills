# Source provenance

- Package: `replynodes/replynodes-agent-skills`, skill slug `replynodes`.
- Product source: the live ReplyNodes MCP at `https://mcp.replynodes.com/mcp`.
- Documentation source: `https://docs.replynodes.com/docs/mcp` and the official
  ReplyNodes pricing/authentication pages.
- Live capability snapshot: MCP `initialize` and `tools/list` returned 51
  read-only tools across website research, brand assets, Apple App Store,
  Google Play, YouTube, Reddit, and Hacker News.
- Distribution: public GitHub source consumed by the official `skills` CLI;
  skills.sh indexes this source asynchronously and its repository-path pages
  are not proof that each focused skill is a real indexed listing.
- Canonical Agent Skills source: `https://github.com/replynodes/replynodes-agent-skills`.
  The canonical skills.sh repository page is
  `https://www.skills.sh/replynodes/replynodes-agent-skills/replynodes`, with
  `brand-logo` included in the source taxonomy but pending a verified focused
  registry listing.
- Acquisition hub: `https://github.com/replynodes/free-markdown-brand-logo-api`.
  It contains examples only and no duplicate Agent Skills files.
- ClawHub migration: verified. ClawHub latest
  `@replynodes-ai/url-to-markdown` is `1.1.2`, and its published metadata
  repository is `https://github.com/replynodes/replynodes-agent-skills`.
  ClawHub latest `@replynodes-ai/brand-logo` is `1.0.0` from canonical
  `skills/brand-logo`.
- The ClawHub merge already read back:
  `https://clawhub.ai/replynodes-ai/skills/brand-logo-fetch` redirects to
  `https://clawhub.ai/replynodes-ai/skills/brand-logo`.
- The old `https://github.com/replynodes/agent-skills` repository is archived,
  as verified after merged commit
  `713b38db9c7315267466174784ce80a41e27aab3`; it is preserved for historical
  provenance.
- This repository contains authored instructions and deterministic validation
  only. It deliberately excludes backend source, database/provider access,
  credentials, provider tokens, account IDs, workspace IDs, and secrets.
