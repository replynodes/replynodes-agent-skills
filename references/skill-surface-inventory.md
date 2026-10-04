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

The GitHub API organization listing
(`https://api.github.com/orgs/replynodes/repos?per_page=100`) and each
repository metadata URL (`https://api.github.com/repos/replynodes/<name>`) were
read on 2026-10-04. `ARCHIVE` records an already archived repository. `REDIRECT`
records the requested user-facing disposition for an archived legacy source;
it does not claim GitHub has configured a redirect. `OWNER ACTION` means an
external owner decision/change is still pending.

| Repository | Status | Evidence and disposition |
| --- | --- | --- |
| [`replynodes/replynodes-agent-skills`](https://github.com/replynodes/replynodes-agent-skills) | KEEP | Canonical maintained source; GitHub API reports `archived: false`. |
| [`replynodes/agent-skills`](https://github.com/replynodes/agent-skills) | ARCHIVE; REDIRECT | GitHub API reports `archived: true`; preserve historical provenance and direct users to the canonical source. |
| [`replynodes/replynodes-brand-logo-fetch`](https://github.com/replynodes/replynodes-brand-logo-fetch) | ARCHIVE; REDIRECT | GitHub API reports `archived: true` and describes it as retired; direct users to the canonical internal/public skill surface as appropriate. |
| [`replynodes/social-data-skills`](https://github.com/replynodes/social-data-skills) | OWNER ACTION | GitHub API reports `archived: false` and describes it as a retired historical provider repository; owner should archive it and redirect users where it duplicates this source. |
| [`replynodes/replynodes-app-store-research`](https://github.com/replynodes/replynodes-app-store-research) | OWNER ACTION | Unarchived standalone repository duplicating the canonical `app-store-research` skill; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-brand-fonts`](https://github.com/replynodes/replynodes-brand-fonts) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `brand-fonts` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-brand-intelligence`](https://github.com/replynodes/replynodes-brand-intelligence) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `brand-intelligence` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-brand-profile`](https://github.com/replynodes/replynodes-brand-profile) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `brand-profile` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-brand-search`](https://github.com/replynodes/replynodes-brand-search) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `brand-search` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-brand-styleguide`](https://github.com/replynodes/replynodes-brand-styleguide) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `brand-styleguide` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-competitor-research`](https://github.com/replynodes/replynodes-competitor-research) | OWNER ACTION | Unarchived standalone repository duplicating the canonical `competitor-research` skill; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-google-play-research`](https://github.com/replynodes/replynodes-google-play-research) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `google-play-research` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-markdown`](https://github.com/replynodes/replynodes-markdown) | OWNER ACTION | Unarchived standalone repository duplicating the retained Markdown capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-reddit-research`](https://github.com/replynodes/replynodes-reddit-research) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `reddit-research` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-web-scraping`](https://github.com/replynodes/replynodes-web-scraping) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `web-scraping` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-web-search`](https://github.com/replynodes/replynodes-web-search) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `web-search` capability; owner action is needed to archive and redirect. |
| [`replynodes/replynodes-youtube-research`](https://github.com/replynodes/replynodes-youtube-research) | OWNER ACTION | Unarchived standalone repository duplicating the retained internal `youtube-research` capability; owner action is needed to archive and redirect. |
| [`replynodes/brand-kit`](https://github.com/replynodes/brand-kit) | KEEP | Independent Node CLI/project; not treated as a duplicate of this repository's Agent Skill source. |
| [`replynodes/free-markdown-brand-logo-api`](https://github.com/replynodes/free-markdown-brand-logo-api) | KEEP | Independent API/acquisition hub; not a duplicate of these skill bodies. |
| [`replynodes/awesome-social-media-skills`](https://github.com/replynodes/awesome-social-media-skills) | KEEP | Independent curated social-media skills project. |
| [`replynodes/x-thought`](https://github.com/replynodes/x-thought) | KEEP | Independent legacy X writing skill; not a ReplyNodes MCP skill duplicate. |
| [`replynodes/linkedin-skills`](https://github.com/replynodes/linkedin-skills) | KEEP | Independent LinkedIn writing/research project; not a duplicate of this source. |

Existing unarchived standalone duplicate repositories need owner action to
archive and redirect to this canonical source. No such external repository
change is performed by this issue.

## skills.sh ghost/index entries

These pages are outside this repository and cannot be deleted by changing the
working tree. On 2026-10-04 each URL returned HTTP 200 with the shown page
title. They are therefore external index/cleanup blockers, not evidence that a
legacy directory remains here:

| URL | Status | Observed evidence and pending action |
| --- | --- | --- |
| [`brandkitfetch`](https://www.skills.sh/replynodes/replynodes-agent-skills/brandkitfetch) | OWNER ACTION | HTTP 200; title `brandkitfetch — replynodes/replynodes-agent-skills`. Request skills.sh/index owner cleanup. |
| [`brand-kit-fetch`](https://www.skills.sh/replynodes/replynodes-agent-skills/brand-kit-fetch) | OWNER ACTION | HTTP 200; title `brand-kit-fetch — replynodes/replynodes-agent-skills`. Request removal/redirect as a legacy alias. |
| [`brand-kit`](https://www.skills.sh/replynodes/replynodes-agent-skills/brand-kit) | OWNER ACTION | HTTP 200; title `brand-kit — replynodes/replynodes-agent-skills`; request a fresh readback after the canonical rename. |
| [`pdf-to-markdown`](https://www.skills.sh/replynodes/replynodes-agent-skills/pdf-to-markdown) | OWNER ACTION | HTTP 200; title `pdf-to-markdown — replynodes/replynodes-agent-skills`; request index cleanup or internal-state refresh while the production gate/readback is pending. |

External cleanup/contact action is pending with the skills.sh index owner. This
document makes no claim that any ghost page has been deleted or updated.

## External lookup blocker

The command

```text
gh issue view 666 --repo replynodes/replynodes-agent-skills --json number,title,body,comments,state
```

returned

```text
GraphQL: Could not resolve to an issue or pull request with the number 666. (repository.issue)
```

Implementation proceeded from the user-provided brief and local repository/CLI
evidence; issue metadata was not found.
