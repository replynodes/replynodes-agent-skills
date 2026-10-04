# Phase 1 discovery and measurement baseline

Recorded: 2026-10-04T09:51:00Z (UTC)
Repository: `replynodes/replynodes-agent-skills`
Canonical source: `https://github.com/replynodes/replynodes-agent-skills`

This is a public/external baseline, not a claim about genuine users. Internal
validation installs must set `DISABLE_TELEMETRY=1`.

## Internal CLI audit

Audited `origin/main` in the canonical skills repository. The only install
commands are README/SKILL/reference documentation and package-validation
examples. Public install examples are user commands. Internal-only examples
in `references/skill-surface-inventory.md` use both
`INSTALL_INTERNAL_SKILLS=1` and `DISABLE_TELEMETRY=1`. No CI or release script
in the three audited repositories invokes `npx skills` without that opt-out.
No second telemetry or attribution mechanism was added.

## Current canonical index snapshot

| Field | Observed value | Method |
|---|---|---|
| Source repository | `replynodes/replynodes-agent-skills` | GitHub API, 200 |
| GitHub stars | 2 | `gh api repos/replynodes/replynodes-agent-skills` |
| Public source slugs | `replynodes`, `company-research`, `competitor-research`, `url-to-markdown`, `brand-kit`, `app-store-research` | `skills.sh.json` on `origin/main` |
| Canonical skills.sh source page | HTTP 200 | GET `https://skills.sh/replynodes/replynodes-agent-skills/replynodes` |
| Per-skill pages | HTTP 200 for all six | GET canonical skills.sh URLs |
| Install counts | replynodes 6; company-research 2; competitor-research 1; url-to-markdown 1; brand-kit 1; app-store-research 0 | `InteractionCounter.userInteractionCount` and visible `Installs` value from each canonical skills.sh page, read 2026-10-04T09:51Z; public/external telemetry only |
| Search ranking | Not observable from the public query pages used below | `GET https://skills.sh/?q=<urlencoded query>` returned no ranked skill result payload |

The two legacy brand URLs remain an external skills.sh owner/index action, not
something this repository can delete: `brandkitfetch` and `brand-kit-fetch`.
They are not in `skills.sh.json`, README install commands, or the public
canonical surface.

## Repeatable task-query discovery baseline

Method: for each query, URL-encode the query and GET
`https://skills.sh/?q=<query>`, then record visible ReplyNodes result and
position. Run date: 2026-10-04 UTC. The current public response did not expose
a ranked result payload, so `appears` and `position` are `not observable`, not
negative claims. Re-run this table with the same query strings and record a
position when the site exposes one.

| # | Query | Target skill | ReplyNodes appears | Position | Notable competing skills | Method |
|---:|---|---|---|---|---|---|
| 1 | research a company | company-research | not observable | not observable | not observable | skills.sh query URL |
| 2 | company research | company-research | not observable | not observable | not observable | skills.sh query URL |
| 3 | company profile and facts | company-research | not observable | not observable | not observable | skills.sh query URL |
| 4 | investigate a company | company-research | not observable | not observable | not observable | skills.sh query URL |
| 5 | compare competitors | competitor-research | not observable | not observable | not observable | skills.sh query URL |
| 6 | competitor analysis | competitor-research | not observable | not observable | not observable | skills.sh query URL |
| 7 | compare products and rivals | competitor-research | not observable | not observable | not observable | skills.sh query URL |
| 8 | competitive intelligence research | competitor-research | not observable | not observable | not observable | skills.sh query URL |
| 9 | URL to Markdown | url-to-markdown | not observable | not observable | not observable | skills.sh query URL |
| 10 | convert webpage to Markdown | url-to-markdown | not observable | not observable | not observable | skills.sh query URL |
| 11 | scrape a webpage as Markdown | url-to-markdown | not observable | not observable | not observable | skills.sh query URL |
| 12 | webpage content extraction | url-to-markdown | not observable | not observable | not observable | skills.sh query URL |
| 13 | fetch a brand kit | brand-kit | not observable | not observable | not observable | skills.sh query URL |
| 14 | find brand logo and colors | brand-kit | not observable | not observable | not observable | skills.sh query URL |
| 15 | brand identity research | brand-kit | not observable | not observable | not observable | skills.sh query URL |
| 16 | get website brand assets | brand-kit | not observable | not observable | not observable | skills.sh query URL |
| 17 | research App Store apps | app-store-research | not observable | not observable | not observable | skills.sh query URL |
| 18 | App Store reviews | app-store-research | not observable | not observable | not observable | skills.sh query URL |
| 19 | App Store privacy and competitors | app-store-research | not observable | not observable | not observable | skills.sh query URL |
| 20 | research iOS app ratings | app-store-research | not observable | not observable | not observable | skills.sh query URL |

## Existing attribution contract

The existing bounded attribution contract in `replynodes-fetcher` already
contains the `skill` field in its allowlist. Audited source of truth:
`replynodes/replynodes-fetcher@77f73b1fb40202c10439f17df59ca4fc36371bec7`,
`docs/attribution-audit.md`, lines 1-6 and 36-37 (origin/main at the review
timestamp). No second mechanism is introduced.

| Skill | Attribution ready? | Implementation / blocker |
|---|---|---|
| company-research | Yes | Existing `skill` allowlist; no compatibility gap found |
| competitor-research | Yes | Existing `skill` allowlist; no compatibility gap found |
| url-to-markdown | Yes | Existing `skill` allowlist; no compatibility gap found |
| brand-kit | Yes | Existing `skill` allowlist; canonical slug is `brand-kit` |
| app-store-research | Yes | Existing `skill` allowlist; no compatibility gap found |

## Reproduction commands

```sh
# Internal validation: telemetry opt-out is mandatory
INSTALL_INTERNAL_SKILLS=1 DISABLE_TELEMETRY=1 \
  npx --yes skills@1.7.0 add . --list --full-depth

# Public discovery readback
python3 - <<'PY'
import urllib.parse
import urllib.request
for query in ["research a company", "compare competitors", "URL to Markdown"]:
    url = "https://skills.sh/?q=" + urllib.parse.quote(query)
    with urllib.request.urlopen(url, timeout=20) as response:
        print(query, response.status, response.geturl())
PY
```
