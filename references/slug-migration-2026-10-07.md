# Slug migration map (agent-skills #57)

Observed 2026-10-07 at the issue #57 implementation base
`d93f21b17a2d53ab183b59145ba51c97cd938a5f` (`origin/main`). This record
implements the slug decisions approved in agent-skills #56 (canonical taxonomy,
merged via PR #59) and reconciles capability claims against the production
keyless/auth classification shipped in `replynodes-fetcher` PR #727.

This file records the in-repository migration only. Registry-side unpublish,
redirect, and readback are owned by issue #58; no external registry operation is
performed here.

## Renamed canonical slugs

| Legacy slug / path | Canonical slug / path | Reason |
| --- | --- | --- |
| `app-store-research` (`skills/app-store-research/`) | `app-store-api` (`skills/app-store-api/`) | Exact provider API slug (#56 decision 1). |
| `google-play-research` (`skills/google-play-research/`) | `google-play-api` (`skills/google-play-api/`) | Exact provider API slug (#56 decision 1). |
| `reddit-research` (`skills/reddit-research/`) | `reddit-api` (`skills/reddit-api/`) | Exact provider API slug (#56 decision 1). |
| `youtube-research` (`skills/youtube-research/`) | `youtube-api` (`skills/youtube-api/`) | Exact provider API slug (#56 decision 1). |

Install the canonical slug name; the legacy `--skill <old-slug>` name is
superseded. Directory, frontmatter `name`, description, body, `skills.sh.json`,
and README references were updated together.

## Legacy/deprecated registry slugs

| Legacy slug | Canonical successor | Notes |
| --- | --- | --- |
| `brandkitfetch` (skills.sh + ClawHub) | `brand-kit` | No canonical repo path; external legacy entry (#56 decision 3). |
| `brand-kit-fetch` (skills.sh) | `brand-kit` | No canonical repo path; external legacy entry (#56 decision 3). |

These have no canonical in-repo directory, so the in-repo migration note lives in
`skills/brand-kit/SKILL.md`. Registry redirect/removal is issue #58.

## Merged internal skills

| Slug | Successor | Treatment |
| --- | --- | --- |
| `brand-profile` | `brand-kit` | Retained internal; body converted to migration guidance. |
| `brand-intelligence` | `brand-kit` | Retained internal; body converted to migration guidance. |

Neither slug is deleted in issue #57 (#56 decision 3).

## Metadata reconciliation

`brand-logo` was declared `internal: true` in the repository while its free,
zero-auth `img.replynodes.com` host was already public. Agent-skills #57
reconciled the metadata to `internal: false` to match the shipped public surface
(#56 row for `brand-logo`; production classification in fetcher #715/#727 leaves
the Logo host as an existing anonymous surface). The `brand-logo` slug itself is
unchanged.

## Capability classification used for the rewrite

Source: `replynodes-fetcher` PR #727 and `docs/anonymous-daily-quota.md`
(merged at `fdff0009b17443c513c770414e49ecf786eab16b`).

| Surface | Classification | Keyless limit / contract |
| --- | --- | --- |
| `md.replynodes.com/<target>` | Anonymous, free | 20 admitted requests/UTC day/trusted client-IP bucket; typed `anonymous_limit_reached` 429; `503 degraded` fail-closed |
| `brand.replynodes.com/<domain>` | Anonymous, free | Shared with Markdown; same 20/day quota and typed 429 |
| `img.replynodes.com/<domain>` | Anonymous, free | Existing surface, unchanged by #715/#727; no published fixed quota |
| `/v1/web/search`, `/v1/webcontext/*` | Keyed-only, metered | `auth_required=true`, read-only |
| `/v1/appstore/*`, `/v1/googleplay/*`, `/v1/reddit/*`, `/v1/youtube/*`, `/v1/hackernews/*` | Keyed-only, metered | `auth_required=true`, read-only |
| `/v1/brand/*` | Keyed-only, metered | Not an anonymous alternative to the free Brand host |
| `mcp.replynodes.com/mcp` | Keyed | `Authorization: Bearer ${REPLYNODES_API_KEY}` |

The `anonymous_limit_reached` envelope is
`{"error":{"code":"anonymous_limit_reached","message":"...500 credits.","request_id":"<id>","continuation":{"url":"https://docs.replynodes.com/docs/auth"}}}`,
with `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and
`Retry-After` headers. An existing authenticated free account has 500 credits.

## Out of scope for this migration

- Taxonomy re-decisions (naming, public/private status, keyless eligibility).
- New fetcher/app code and any auth/billing/quota system change.
- Registry publication/readback (#58).
- `pdf-to-markdown` remains internal and not-public-ready: its no-key conversion
  contract is still unverified in production, so it was left unchanged.

## #58 registry readback outcome (2026-10-07)

Issue #58 performed the live read-only registry readback recorded in
[registry-inventory-2026-10-07.md](registry-inventory-2026-10-07.md) (raw rows
in [registry-readback-2026-10-07.json](registry-readback-2026-10-07.json)). No
skills.sh or ClawHub write was performed. At that readback, skills.sh still
listed the pre-rename slugs and the two legacy brand entries, and ClawHub still
had no canonical `brand-kit` target, so the approved `brandkitfetch` -> `brand-kit`
migration remains blocked upstream. Exact next owner actions are in
[registry-sync-2026-10-07.md](registry-sync-2026-10-07.md).
