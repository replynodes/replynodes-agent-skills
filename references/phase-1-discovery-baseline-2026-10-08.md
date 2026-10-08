# Phase 1 discovery baseline re-run

Recorded: 2026-10-08T15:25:32Z
Repository: `replynodes/replynodes-agent-skills`
Source head: `4aa42f65980056d3464f596d0fd749c3be17eca7` (`origin/main`)

This re-runs the identical task-language query strings from
[phase-1-discovery-baseline-2026-10-04.md](phase-1-discovery-baseline-2026-10-04.md)
after the focused-install change. It is a public/external baseline, not a
claim about genuine users. Internal validation installs set `DISABLE_TELEMETRY=1`.

## Method

For each query, URL-encode the query and GET `https://skills.sh/?q=<query>`
(the redirect resolves to `https://www.skills.sh/search?q=<query>`), then record
the final URL, HTTP status, and any observable ReplyNodes appearance or rank.
The public response is client-rendered and did not expose a ranked result
payload, so `appears`, `position`, and `notable competing skills` are recorded
as `not observable` (not negative claims). Raw rows are in
[phase-1-discovery-baseline-2026-10-08.json](phase-1-discovery-baseline-2026-10-08.json).

## Repeatable task-query discovery baseline (re-run)

| # | Query | Target skill | ReplyNodes appears | Position | Notable competing skills | HTTP | Method |
|---:|---|---|---|---|---|---:|---|
| 1 | research a company | company-research | not observable | not observable | not observable | 200 | skills.sh query URL |
| 2 | company research | company-research | not observable | not observable | not observable | 200 | skills.sh query URL |
| 3 | company profile and facts | company-research | not observable | not observable | not observable | 200 | skills.sh query URL |
| 4 | investigate a company | company-research | not observable | not observable | not observable | 200 | skills.sh query URL |
| 5 | compare competitors | competitor-research | not observable | not observable | not observable | 200 | skills.sh query URL |
| 6 | competitor analysis | competitor-research | not observable | not observable | not observable | 200 | skills.sh query URL |
| 7 | compare products and rivals | competitor-research | not observable | not observable | not observable | 200 | skills.sh query URL |
| 8 | competitive intelligence research | competitor-research | not observable | not observable | not observable | 200 | skills.sh query URL |
| 9 | URL to Markdown | url-to-markdown | not observable | not observable | not observable | 200 | skills.sh query URL |
| 10 | convert webpage to Markdown | url-to-markdown | not observable | not observable | not observable | 200 | skills.sh query URL |
| 11 | scrape a webpage as Markdown | url-to-markdown | not observable | not observable | not observable | 200 | skills.sh query URL |
| 12 | webpage content extraction | url-to-markdown | not observable | not observable | not observable | 200 | skills.sh query URL |
| 13 | fetch a brand kit | brand-kit | not observable | not observable | not observable | 200 | skills.sh query URL |
| 14 | find brand logo and colors | brand-kit | not observable | not observable | not observable | 200 | skills.sh query URL |
| 15 | brand identity research | brand-kit | not observable | not observable | not observable | 200 | skills.sh query URL |
| 16 | get website brand assets | brand-kit | not observable | not observable | not observable | 200 | skills.sh query URL |
| 17 | research App Store apps | app-store-api | not observable | not observable | not observable | 200 | skills.sh query URL |
| 18 | App Store reviews | app-store-api | not observable | not observable | not observable | 200 | skills.sh query URL |
| 19 | App Store privacy and competitors | app-store-api | not observable | not observable | not observable | 200 | skills.sh query URL |
| 20 | research iOS app ratings | app-store-api | not observable | not observable | not observable | 200 | skills.sh query URL |

## Observations

- All 20/20 query URLs resolved with HTTP 200 and no observable ranked payload.
- The App Store queries target the renamed canonical slug `app-store-api`
  (the 2026-10-04 baseline recorded the legacy `app-store-research` name).
- The measured two-day retention window in
  [company-research-distribution.md](company-research-distribution.md) remains `PENDING`;
  marketplace install/listing counters stay separate from distinct and retained callers.

