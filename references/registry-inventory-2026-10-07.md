# Registry inventory — skills.sh and ClawHub (2026-10-07)

Live read-only readback observed **2026-10-07 UTC** for
`replynodes/replynodes-agent-skills` (public). Source head at refresh:
`166f0f515afb27e7cc393fa5b0c236005661b9fc` (`origin/main`, merged agent-skills #57).
Refreshes `references/canonical-skill-inventory-2026-10-06.md` (issue #56). This is the
issue [#58](https://github.com/replynodes/replynodes-agent-skills/issues/58) pre-release
registry readback. Raw rows: `references/registry-readback-2026-10-07.json`; outcome
and next actions: `references/registry-sync-2026-10-07.md`.

## Method, boundaries, and reading rules

- Read-only public reads only. No credentials, cookies, registry writes, installs, or
  downloads were used. No secret value appears here.
- Registry install/download counts are **external display signals**, not users and not
  active API callers; they are kept separate from product/API usage.
- **skills.sh soft pages.** Every slug under the repo path — including a nonexistent
  slug — returns HTTP 200 with generated text. A slug is a **real listing** only when
  the page renders a real description plus an install count.
- **skills.sh public API** (`/api/v1/skills…`) returned HTTP 401
  `authentication_required` (Vercel OIDC token required); it was not used.
- **ClawHub public row** (`/api/v1/skills/<slug>?owner=replynodes-ai`) exposes
  `displayName`, `summary`, `description`, `topics`, `tags`, `stats` (`downloads`,
  `installs`, `stars`, `versions`), `createdAt`, `updatedAt`, and `latestVersion` — and
  **no source repository or commit**, so a row is not asserted byte-identical to this repo.

## skills.sh readback

- Collection `https://www.skills.sh/replynodes/replynodes-agent-skills`: **HTTP 200**.
- Badge `https://skills.sh/b/replynodes/replynodes-agent-skills`: **Skills: 32**
  (total installs across indexed listings).
- Real listings: **17**, with the **same slug set and same 32 total installs** as the
  issue #56 readback on 2026-10-06 — the index did not pick up the #57 renames.

| slug | exact URL | HTTP | installs | state | description vs current canonical |
| --- | --- | --- | --- | --- | --- |
| `company-research` | https://www.skills.sh/replynodes/replynodes-agent-skills/company-research | 200 | 8 | match (display-truncated) |
| `replynodes` | https://www.skills.sh/replynodes/replynodes-agent-skills/replynodes | 200 | 6 | differs (pre-#57 wording) |
| `brand-kit` | https://www.skills.sh/replynodes/replynodes-agent-skills/brand-kit | 200 | 2 | differs (pre-#57 wording) |
| `competitor-research` | https://www.skills.sh/replynodes/replynodes-agent-skills/competitor-research | 200 | 2 | differs (pre-#57 wording) |
| `url-to-markdown` | https://www.skills.sh/replynodes/replynodes-agent-skills/url-to-markdown | 200 | 2 | differs (pre-#57 wording) |
| `app-store-research` | https://www.skills.sh/replynodes/replynodes-agent-skills/app-store-research | 200 | 1 | legacy slug (superseded by #57 rename) |
| `brand-fonts` | https://www.skills.sh/replynodes/replynodes-agent-skills/brand-fonts | 200 | 1 | differs (pre-#57 wording) |
| `brand-intelligence` | https://www.skills.sh/replynodes/replynodes-agent-skills/brand-intelligence | 200 | 1 | differs (pre-#57 wording) |
| `brand-profile` | https://www.skills.sh/replynodes/replynodes-agent-skills/brand-profile | 200 | 1 | differs (pre-#57 wording) |
| `brand-search` | https://www.skills.sh/replynodes/replynodes-agent-skills/brand-search | 200 | 1 | differs (pre-#57 wording) |
| `brand-styleguide` | https://www.skills.sh/replynodes/replynodes-agent-skills/brand-styleguide | 200 | 1 | differs (pre-#57 wording) |
| `pdf-to-markdown` | https://www.skills.sh/replynodes/replynodes-agent-skills/pdf-to-markdown | 200 | 1 | match |
| `reddit-research` | https://www.skills.sh/replynodes/replynodes-agent-skills/reddit-research | 200 | 1 | legacy slug (superseded by #57 rename) |
| `web-scraping` | https://www.skills.sh/replynodes/replynodes-agent-skills/web-scraping | 200 | 1 | differs (pre-#57 wording) |
| `web-search` | https://www.skills.sh/replynodes/replynodes-agent-skills/web-search | 200 | 1 | differs (pre-#57 wording) |
| `brandkitfetch` | https://www.skills.sh/replynodes/replynodes-agent-skills/brandkitfetch | 200 | 1 | legacy (no canonical repo path) |
| `brand-kit-fetch` | https://www.skills.sh/replynodes/replynodes-agent-skills/brand-kit-fetch | 200 | 1 | legacy (no canonical repo path) |

### skills.sh soft-only slugs (HTTP 200 generic page, not real listings)

Canonical #57 slugs with **no** real skills.sh listing (generic repo-path page only):
`app-store-api`, `brand-logo`, `google-play-api`, `google-play-research`, `reddit-api`, `youtube-api`, `youtube-research`. Of these, `google-play-research` and `youtube-research` were
never listed on skills.sh in #56 either.

## ClawHub readback (owner `replynodes-ai`)

Publisher `https://clawhub.ai/replynodes-ai`: **HTTP 200**. **13** packages; every row
below returned **HTTP 200** on 2026-10-07.

| slug | page URL | HTTP | latest version | downloads | installs | updated (UTC) | description sha256 (16) | display name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `replynodes` | https://clawhub.ai/replynodes-ai/skills/replynodes | 200 | 1.0.3 | 396 | 0 | 2026-08-19T01:20:14Z | `06472446326750bb` | Social Media Scheduler — Publish, Cross-Post & Auto-Post via ReplyNodes for OpenClaw |
| `company-research` | https://clawhub.ai/replynodes-ai/skills/company-research | 200 | 1.0.3 | 58 | 0 | 2026-10-05T02:33:42Z | `ae229c47e35cdc77` | Free Company Research & Business Intelligence |
| `url-to-markdown` | https://clawhub.ai/replynodes-ai/skills/url-to-markdown | 200 | 1.1.2 | 121 | 1 | 2026-09-27T03:23:24Z | `0bd3282ab1b9faeb` | url-to-markdown |
| `brand-logo` | https://clawhub.ai/replynodes-ai/skills/brand-logo | 200 | 1.0.0 | 131 | 0 | 2026-09-27T03:23:33Z | `d66ebe8f0eac86ff` | brand-logo |
| `appstore-api` | https://clawhub.ai/replynodes-ai/skills/appstore-api | 200 | 2.1.3 | 735 | 1 | 2026-09-12T16:55:48Z | `203e0d58be1258b7` | Apple App Store API |
| `googleplay-public-data-api` | https://clawhub.ai/replynodes-ai/skills/googleplay-public-data-api | 200 | 1.1.2 | 463 | 1 | 2026-09-24T22:03:28Z | `4d9866a935edb56f` | Google Play Public Data API |
| `reddit-api` | https://clawhub.ai/replynodes-ai/skills/reddit-api | 200 | 1.1.0 | 271 | 0 | 2026-09-09T11:28:49Z | `42d398cee0aadb25` | Reddit Api |
| `youtube-public-api` | https://clawhub.ai/replynodes-ai/skills/youtube-public-api | 200 | 2.0.1 | 462 | 1 | 2026-09-09T10:09:49Z | `28e1eb55f89e56f8` | Youtube Public Api |
| `brandkitfetch` | https://clawhub.ai/replynodes-ai/skills/brandkitfetch | 200 | 1.0.0 | 119 | 0 | 2026-09-28T00:53:51Z | `41acd637f103b0c8` | Brand Kit Fetch |
| `hackernews-api` | https://clawhub.ai/replynodes-ai/skills/hackernews-api | 200 | 2.0.1 | 521 | 3 | 2026-09-09T10:09:37Z | `e8541610342342a3` | Hackernews Api |
| `fomo-app-data-api` | https://clawhub.ai/replynodes-ai/skills/fomo-app-data-api | 200 | 2.0.1 | 508 | 1 | 2026-09-09T10:10:38Z | `7af604aa314fd396` | Fomo App Data Api |
| `seo-geo-growth-agent` | https://clawhub.ai/replynodes-ai/skills/seo-geo-growth-agent | 200 | 1.0.0 | 299 | 0 | 2026-08-21T02:03:20Z | `a5c29e4f65c99a88` | SEO & GEO Growth Agent |
| `web-research-public-data` | https://clawhub.ai/replynodes-ai/skills/web-research-public-data | 200 | 1.0.2 | 237 | 1 | 2026-09-16T11:09:24Z | `cfbd3311d2c0dc53` | Web Search, Web Scraping, Crawl, Reddit, YouTube & App Research API |

ClawHub package totals: **downloads 4321**, **installs 9** (external display signals).

### Canonical slugs absent from ClawHub (HTTP 404 as owner `replynodes-ai`)

`app-store-api`, `brand-fonts`, `brand-intelligence`, `brand-kit`, `brand-kit-fetch`, `brand-profile`, `brand-search`, `brand-styleguide`, `competitor-research`, `google-play-api`, `pdf-to-markdown`, `web-scraping`, `web-search`, `youtube-api`

## Source / version / description mismatch

- **skills.sh:** the real listings still render **pre-#57** wording for almost every
  slug (only `company-research` — display-truncated — and `pdf-to-markdown` match the
  current canonical `description:`). The renamed provider slugs still appear as
  `app-store-research` and `reddit-research`, and the legacy `brandkitfetch` and
  `brand-kit-fetch` entries remain live. The five new canonical slugs are not indexed.
  skills.sh exposes **no version or source commit** for a listing.
- **ClawHub:** the 13 packages are owned by `replynodes-ai` but expose **no source
  repo/commit** and their slugs partly differ from the canonical taxonomy
  (`appstore-api` vs `app-store-api`; `googleplay-public-data-api` vs `google-play-api`;
  `youtube-public-api` vs `youtube-api`). The umbrella slug `replynodes` renders as
  `Social Media Scheduler — Publish, Cross-Post & Auto-Post…`, which is not this
  repository's read-only umbrella. `company-research` carries #57-era wording but its
  stored version is `1.0.3`, not the repository's `2.0.0`.

## Official documented refresh / submission path

- **skills.sh:** no self-serve author write API. The public read API requires a Vercel
  OIDC token. The official contact page (`https://www.skills.sh/contact`) states that a
  publisher wanting a listing **corrected, hidden, or redirected** must open a pull
  request against `vercel-labs/skills` using its skills manifest. Upstream owner action.
- **ClawHub:** an owner write path exists. The authenticated `clawhub` CLI (verified
  `whoami` → `replynodes-ai`, exit 0) provides `skill publish`, `skill rename` (old slug
  becomes a redirect), `skill merge`, `sync`, `hide`, and `delete`. Outcome and exact
  next action are in `references/registry-sync-2026-10-07.md`.
