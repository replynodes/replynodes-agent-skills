# Registry sync and migration outcome (agent-skills #58, 2026-10-07)

Live read-only readback observed **2026-10-07 UTC** at source head
`166f0f515afb27e7cc393fa5b0c236005661b9fc` (`origin/main`). Raw rows:
`references/registry-readback-2026-10-07.json`. Per-listing detail:
`references/registry-inventory-2026-10-07.md`. This is the issue
[#58](https://github.com/replynodes/replynodes-agent-skills/issues/58)
distribution step; it re-decides nothing about taxonomy, capability, or auth.

## What this change did — and deliberately did not do

- Refreshed the live readback of both registries (evidence above).
- **Did not** create, hide, correct, or redirect any skills.sh listing.
- **Did not** publish, rename, merge, hide, or delete any ClawHub package.
- **Did not** create a duplicate listing to compensate for a stale third-party
  index.
- Used no credential and printed no secret value.

The stale third-party entries below are owned by upstream indices; a repository
rename cannot fix an index that has not re-crawled, and creating a second
listing to "cover" a stale one is explicitly out of scope.

## skills.sh — sync path, eligible upstream state, next owner action

- **Sync mechanism.** skills.sh indexes public skills that ship through the open
  `skills` CLI and ranks them by anonymous install telemetry; there is **no
  self-serve author write API**. Its public catalog API
  (`https://skills.sh/api/v1/skills…`) returned **HTTP 401
  `authentication_required`** (a Vercel OIDC token is required), so it cannot be
  used for unauthenticated readback.
- **Documented correction path.** The official contact page
  (`https://www.skills.sh/contact`, observed 2026-10-07) states that a publisher
  who wants a listing *corrected, hidden, or redirected* must **open a pull
  request against `vercel-labs/skills`** using that repository's skills
  manifest. A search of the public `vercel-labs/skills` default branch
  (README and `src/`) on 2026-10-07 did **not** surface a hidden/redirected
  skills manifest file, so the exact manifest path needs upstream confirmation.
  This is an owner/upstream action, not a credential this repository holds.
- **Eligible upstream state.** The index did not re-crawl after #57: the four
  renamed provider slugs still appear under old names
  (`app-store-research` → `app-store-api`, `reddit-research` → `reddit-api`),
  the legacy `brandkitfetch` and `brand-kit-fetch` entries are still live, and
  the five new canonical slugs (`app-store-api`, `brand-logo`,
  `google-play-api`, `reddit-api`, `youtube-api`) are not indexed.
- **Exact next owner action.** Open one pull request to `vercel-labs/skills`
  requesting hidden/redirect manifest entries for `brandkitfetch` and
  `brand-kit-fetch` → canonical `brand-kit`, and redirect entries for
  `app-store-research` → `app-store-api` and `reddit-research` → `reddit-api`,
  after confirming the manifest format with the upstream repo. Otherwise wait
  for skills.sh to re-crawl the canonical repository.

## ClawHub — sync path, eligible upstream state, next owner action

- **Owner path exists.** The authenticated `clawhub` CLI was verified as owner
  `replynodes-ai` (`whoami` exit 0). Documented commands: `skill publish`,
  `skill rename` (keeps the old slug as a redirect), `skill merge`, `sync`,
  `hide`, `delete`.
- **Why no publication ran here.** Issue #56 approved **no new ClawHub
  publication**; the canonical-colliding ClawHub rows are recorded as external
  legacy/current registry state, not canonical. Publishing a canonical-colliding
  slug where a differently-sourced row already exists would create a duplicate,
  which this ticket forbids.
- **Approved migration `brandkitfetch` → `brand-kit` is blocked.** Neither
  `clawhub skill merge brandkitfetch brand-kit` nor `skill rename` can run
  truthfully yet: the canonical `brand-kit` target is **HTTP 404** (not an owned
  package), and the `brandkitfetch` content is not canonical. Redirecting
  non-canonical legacy content onto a canonical slug would create a false
  canonical claim.
- **Stale public claims present (owner-controlled).** The `replynodes` row
  renders as `Social Media Scheduler — Publish, Cross-Post & Auto-Post…`, which
  contradicts this repository's read-only taxonomy; `appstore-api`,
  `googleplay-public-data-api`, `youtube-public-api`, and `reddit-api` collide
  with future canonical slugs and carry no source provenance.
- **Exact next owner action (eligible commands, NOT executed here).**
  1. Publish the approved canonical public skills from a clean `git archive` of
     the merged `main` with `--owner replynodes-ai` and explicit
     `--source-repo replynodes/replynodes-agent-skills --source-commit <sha>`
     (`--slug` = canonical slug).
  2. After a canonical `brand-kit` package is live, run
     `clawhub skill merge brandkitfetch brand-kit --yes` and read back the
     redirect.
  3. Republish the canonical read-only umbrella (or `clawhub hide`) so the
     public `replynodes` page no longer claims social publishing.
  4. Read every row back (`clawhub inspect` / `clawhub skill verify` plus the
     public row API) after each write; a successful upload is not a live release.

## Approved migration / deprecation outcome

> **Status of every outcome below: PENDING owner/registry action.** No supported public
> write was performed on either surface in this change, so no unpublish, hide, redirect,
> merge, or deprecation has taken effect. skills.sh outcomes await the upstream
> `vercel-labs/skills` manifest pull request; ClawHub outcomes await owner-run,
> authenticated `clawhub` commands.

| Registry | Legacy slug | Canonical successor | #56 outcome | This run |
| --- | --- | --- | --- | --- |
| skills.sh | `brandkitfetch` | `brand-kit` | migrate (owner-supported) | read back still live; no write (upstream PR path) |
| skills.sh | `brand-kit-fetch` | `brand-kit` | migrate (owner-supported) | read back still live; no write (upstream PR path) |
| skills.sh | `app-store-research` | `app-store-api` | #57 rename | read back still live under old slug; no write |
| skills.sh | `reddit-research` | `reddit-api` | #57 rename | read back still live under old slug; no write |
| ClawHub | `brandkitfetch` | `brand-kit` | migrate | blocked: canonical `brand-kit` target absent; no write |
| ClawHub | `appstore-api` | `app-store-api` | legacy-only / reconcile after #57 | reviewed; no write (would duplicate) |
| ClawHub | `googleplay-public-data-api` | `google-play-api` | legacy-only / reconcile | reviewed; no write |
| ClawHub | `youtube-public-api` | `youtube-api` | legacy-only / reconcile | reviewed; no write |
| ClawHub | `replynodes` | `replynodes` | legacy-only / owner review | reviewed; scheduler claim flagged, no write |
| ClawHub | `hackernews-api`, `fomo-app-data-api`, `seo-geo-growth-agent`, `web-research-public-data` | — | not canonical; owner review | reviewed; no successor inferred, no write |

Internal skills (`brand-profile`, `brand-intelligence` → `brand-kit`) are merged
as internal guidance only (#56 decision 3); they are not newly published.

## Attribution and measurement boundary

- The **canonical slug is the attribution unit**. Where the surface supports it:
  source/channel identifies the registry, campaign equals the canonical skill
  slug, and the skill header/property equals the canonical skill slug. Legacy
  slugs map to the canonical successor only through the approved attribution
  contract; no analytics semantics are rewritten here.
- **Registry install/download counts are external display signals.** They are
  kept separate from the product funnel (anonymous first callers, repeat-day
  callers, limit hits, signup/API-key creation, first authenticated call, paid
  conversion). Registry metrics must never be labeled real users or API callers.

## Gates

See the PR for exact head SHA and command/result output for
`scripts/validate-package.sh`, `tests/test-package.sh`, `tests/test-registry-links.sh`,
`git diff --check`, and the secret scan. No external registry write is part of
these gates.
