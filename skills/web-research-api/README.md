# Web Research API

Install from the ReplyNodes agent-skills repository:

```bash
clawhub install @replynodes-ai/web-research-api --dir ./skills
```

Or install from a reviewed Git tag:

```bash
git clone --depth 1 --branch v1.0.1 https://github.com/replynodes/replynodes-agent-skills.git
# use skills/web-research-api/SKILL.md as the skill entrypoint
```

The package is a portable instruction-only skill. It calls the public
ReplyNodes read gateway at `https://api.replynodes.com`; it has no runtime
dependencies, credentials, OAuth flow, telemetry, or social write path.

Before a paid operation, fetch `/v1/<provider>/capabilities` and use the
advertised provider-specific prepaid Bearer access. Never paste a key into an
agent conversation. A `401` means the required Bearer access is missing or
invalid.

Supported routing includes Web Search, Scrape Markdown, Web Crawl, Website
Map, Brand Info, Retrieve Brand, Search Brand, Get Styleguide, Get Fonts,
Reddit, YouTube, and the existing read-only ReplyNodes provider APIs. See
[`SKILL.md`](SKILL.md) for the exact routing and safety contract.

## Version

This release is `v1.0.1`.
