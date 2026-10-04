# Skill-surface inventory

Observed 2026-10-04 from the current `feat/issue-666-canonical-skill-surface`
worktree and the public GitHub/skills.sh URLs linked below. This is an
inventory and disposition record, not a claim that external repositories or
marketplace indexes have already changed.

## CLI behavior

The current CLI checked for this change is `skills` 1.7.0:

```text
$ npx --yes skills@latest --version
1.7.0
```

Its documented and observed metadata contract is `metadata.internal: true`:
the skill is hidden from normal discovery and is visible/installable only when
`INSTALL_INTERNAL_SKILLS=1` (also accepted as `true`) is set. Public skills
therefore declare `metadata.internal: false` explicitly; internal/provider
skills declare `metadata.internal: true` explicitly. `DISABLE_TELEMETRY=1` is
required here for an exact internal install so the CLI does not emit telemetry.

Observed against this worktree: normal discovery reported 6 skills and
internal opt-in discovery reported 18 skills. The normal list was exactly the
six public names below; the opt-in list was exactly those six plus the twelve
retained internal/provider names classified below.

Classification and CLI checks:

```bash
# Every SKILL.md has YAML metadata, a directory-matching name, and an explicit boolean.
./scripts/validate-package.sh

# Normal discovery: exactly the six public names below (root plus five nested skills).
npx --yes skills@1.7.0 add . --list --full-depth

# Opt-in discovery: the retained internal/provider skills become visible too.
INSTALL_INTERNAL_SKILLS=1 DISABLE_TELEMETRY=1 \
  npx --yes skills@1.7.0 add . --list --full-depth

# Exact internal install example.
INSTALL_INTERNAL_SKILLS=1 DISABLE_TELEMETRY=1 \
  npx --yes skills@1.7.0 add . --skill web-search --full-depth --yes
```

The public normal-discovery set is exactly:

| Directory | Name | Classification |
| --- | --- | --- |
| `SKILL.md` | `replynodes` | KEEP / public |
| `skills/company-research` | `company-research` | KEEP / public |
| `skills/competitor-research` | `competitor-research` | KEEP / public |
| `skills/url-to-markdown` | `url-to-markdown` | KEEP / public |
| `skills/brand-kit` | `brand-kit` | KEEP / public |
| `skills/app-store-research` | `app-store-research` | KEEP / public |

All other existing nested skills are preserved and internal/provider:
`brand-fonts`, `brand-intelligence`, `brand-logo`, `brand-profile`,
`brand-search`, `brand-styleguide`, `google-play-research`,
`pdf-to-markdown`, `reddit-research`, `web-scraping`, `web-search`, and
`youtube-research`. Each is classified KEEP / internal-provider. In
particular, `pdf-to-markdown` remains internal until its production gate/readback
passes.

## ReplyNodes repositories

This bounded inventory contains only the 22 repositories in the fresh
organization API evidence supplied for this repair. The `archived` and
`private` values and descriptions below are observed GitHub metadata; URLs are
the exact repository URLs. `ARCHIVE` is observed GitHub archive state, while
`REDIRECT` is a requested user-facing disposition and does not claim that
GitHub redirect configuration was performed. No external repository changes
are performed by this issue.

| Repository | Observed GitHub metadata (archived/private/description) | Disposition/evidence |
| --- | --- | --- |
| [replynodes-agent-skills](https://github.com/replynodes/replynodes-agent-skills) | `archived: false`; `private: false`; “Web and public-data research skills for AI agents -- web search, scraping, brand intelligence, Reddit, YouTube, App Store, Google Play and MCP.” | KEEP — canonical agent-skills source. |
| [agent-skills](https://github.com/replynodes/agent-skills) | `archived: true`; `private: false`; “ReplyNodes Agent Skills” | ARCHIVE / REDIRECT — ARCHIVE is observed GitHub state; REDIRECT is requested user-facing disposition. |
| [replynodes-brand-logo-fetch](https://github.com/replynodes/replynodes-brand-logo-fetch) | `archived: true`; `private: false`; “Retired legacy repository; use the canonical ReplyNodes brand-logo skill.” | ARCHIVE / REDIRECT — ARCHIVE is observed GitHub state; REDIRECT is requested user-facing disposition. |
| [social-data-skills](https://github.com/replynodes/social-data-skills) | `archived: false`; `private: false`; “Retired historical social-provider skill repository; pending archival decision.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-markdown](https://github.com/replynodes/replynodes-markdown) | `archived: false`; `private: false`; “Legacy Markdown endpoint documentation; use free-markdown-brand-logo-api as the unified Markdown, Brand, and Logo acquisition hub.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-youtube-research](https://github.com/replynodes/replynodes-youtube-research) | `archived: false`; `private: false`; “Read-only youtube-research research skill for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-google-play-research](https://github.com/replynodes/replynodes-google-play-research) | `archived: false`; `private: false`; “Read-only google-play-research research skill for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-brand-intelligence](https://github.com/replynodes/replynodes-brand-intelligence) | `archived: false`; `private: false`; “Read-only brand-intelligence research skill for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-brand-search](https://github.com/replynodes/replynodes-brand-search) | `archived: false`; `private: false`; “Read-only brand-search research skill for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-app-store-research](https://github.com/replynodes/replynodes-app-store-research) | `archived: false`; `private: false`; “Read-only app-store-research research skill for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-brand-profile](https://github.com/replynodes/replynodes-brand-profile) | `archived: false`; `private: false`; “Read-only brand-profile research skill for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-brand-styleguide](https://github.com/replynodes/replynodes-brand-styleguide) | `archived: false`; `private: false`; “Read-only brand-styleguide research skill for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-brand-fonts](https://github.com/replynodes/replynodes-brand-fonts) | `archived: false`; `private: false`; “Read-only brand-fonts research skill for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-competitor-research](https://github.com/replynodes/replynodes-competitor-research) | `archived: false`; `private: false`; “Read-only competitor and market research skills for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-web-search](https://github.com/replynodes/replynodes-web-search) | `archived: false`; `private: false`; “Read-only web search and source discovery skills for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-web-scraping](https://github.com/replynodes/replynodes-web-scraping) | `archived: false`; `private: false`; “Read-only website scraping, Markdown extraction, crawling, and mapping skills for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [replynodes-reddit-research](https://github.com/replynodes/replynodes-reddit-research) | `archived: false`; `private: false`; “Read-only Reddit research skills for AI agents using ReplyNodes MCP.” | OWNER ACTION — unarchived duplicate/legacy standalone repository; owner action remains pending. |
| [brand-kit](https://github.com/replynodes/brand-kit) | `archived: false`; `private: false`; “Pure Node.js CLI for generating deterministic brand kits from the ReplyNodes public aggregate” | KEEP. |
| [free-markdown-brand-logo-api](https://github.com/replynodes/free-markdown-brand-logo-api) | `archived: false`; `private: false`; “Free Markdown API, Brand API, and Logo API for developers and AI agents — no signup, no API key.” | KEEP. |
| [awesome-social-media-skills](https://github.com/replynodes/awesome-social-media-skills) | `archived: false`; `private: false`; “Curated, portable AI agent skills for researching, creating, repurposing, publishing, and analyzing social-media content. 26 skills, MIT licensed.” | KEEP. |
| [x-thought](https://github.com/replynodes/x-thought) | `archived: false`; `private: false`; “Independent legacy X writing skill for Hermes Agent; not a current ReplyNodes publishing or MCP surface.” | KEEP. |
| [linkedin-skills](https://github.com/replynodes/linkedin-skills) | `archived: false`; `private: false`; “Claude skills for LinkedIn. 11 Claude Code and Codex skills that write human-sounding LinkedIn posts, craft comments that get noticed, analyze your feed, and build a publishing cadence, all from your terminal. Content engineering by Creative Content Crafts. MIT.” | KEEP. |

## skills.sh external index/cleanup

The four URLs below were freshly probed and each returned HTTP 200 with the
exact title shown. They are external cleanup items, not evidence that a legacy
directory remains in this repository. Each is OWNER ACTION / external cleanup
pending.

| URL | Observed evidence | Disposition |
| --- | --- | --- |
| [brandkitfetch](https://www.skills.sh/replynodes/replynodes-agent-skills/brandkitfetch) | HTTP 200; title `brandkitfetch — replynodes/replynodes-agent-skills` | OWNER ACTION / external cleanup pending |
| [brand-kit-fetch](https://www.skills.sh/replynodes/replynodes-agent-skills/brand-kit-fetch) | HTTP 200; title `brand-kit-fetch — replynodes/replynodes-agent-skills` | OWNER ACTION / external cleanup pending |
| [brand-kit](https://www.skills.sh/replynodes/replynodes-agent-skills/brand-kit) | HTTP 200; title `brand-kit — replynodes/replynodes-agent-skills` | OWNER ACTION / external cleanup pending |
| [pdf-to-markdown](https://www.skills.sh/replynodes/replynodes-agent-skills/pdf-to-markdown) | HTTP 200; title `pdf-to-markdown — replynodes/replynodes-agent-skills` | OWNER ACTION / external cleanup pending |

External cleanup/contact remains pending; this issue does not claim it was
completed.
