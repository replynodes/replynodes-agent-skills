# GitHub Actions examples

These are copyable, bounded examples for real read-only research workflows. They are documentation examples, not an install loop: install a skill once in the agent environment, then reuse it. Each example links to the canonical source and uses public data only.

- `company-research.yml` — produce a bounded company brief from a domain.
- `url-to-markdown.yml` — convert a known public URL to Markdown.
- `app-store-research.yml` — fetch one public App Store result.
- `umbrella-research.yml` — install the umbrella router for mixed research tasks.
- `scheduled-public-research.yml` — scheduled bounded public research with an explicit rate limit.

Canonical source: https://github.com/replynodes/replynodes-agent-skills
Skills.sh pages: https://skills.sh/replynodes/replynodes-agent-skills

For local validation only, use `DISABLE_TELEMETRY=1`; never add that flag to user-facing install commands.
