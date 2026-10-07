# ReplyNodes research recipes

These are routing recipes, not fixed API contracts. The free Markdown and Brand
hosts and the keyless `GET https://api.replynodes.com/v1/brand/logo` endpoint are
anonymous at Tier A (20 requests/UTC day per capability); the
`img.replynodes.com` Logo host is a separate anonymous surface with no published
fixed limit. The reviewed keyless `/v1` primitives — `GET /v1/web/search`,
`GET /v1/webcontext/scrape`, and the `/v1/appstore/*`, `/v1/googleplay/*`,
`/v1/reddit/*`, and `/v1/youtube/*` reads — are anonymous at Tier B (10/day per
capability). The remaining `/v1` routes (site `map`/`crawl`/`brand`, deeper
`/v1/brand/*`, and `/v1/hackernews/*`) are keyed: confirm the current route names,
parameters, and schemas with the live
[capabilities document](https://api.replynodes.com/v1/capabilities) or MCP
`tools/list` before execution. Over the anonymous limit the free routes return
`429 anonymous_limit_reached` with a `Retry-After` header and an
<https://docs.replynodes.com/docs/auth> continuation (an existing authenticated
free account has 500 credits).

## Company profile

For a general company profile or context request, route to `company-research`.
Identity-only requests route to `brand-kit`; competitor comparisons route to
`competitor-research`.

1. Free Markdown homepage: `GET https://md.replynodes.com/https://<domain>/`.
2. Free Brand JSON: `GET https://brand.replynodes.com/<domain>.json`.
3. Keyed `GET /v1/webcontext/map` to discover the site structure.
4. Keyed `GET /v1/webcontext/crawl` for bounded relevant pages.
5. Keyed `GET /v1/brand/retrieve`, then `/v1/brand/fonts` or
   `/v1/brand/styleguide` for public identity and design signals.
6. Keyed `/v1/reddit/search_posts` and `/v1/hackernews/search` for independent
   discussion.

Return official facts separately from community observations.

## Competitor comparison

1. Search each competitor and resolve its official domain.
2. Scrape or crawl the official sites using the same page/depth budget.
3. Retrieve comparable brand fields with the brand routes.
4. Resolve mobile apps in App Store (`/v1/appstore/*`) or Google Play
   (`/v1/googleplay/*`) and collect the same detail, review, rating,
   privacy/data-safety, and similar-app fields where supported.
5. Use YouTube (`/v1/youtube/*`), Reddit (`/v1/reddit/*`), and Hacker News
   (`/v1/hackernews/*`) for external coverage and discussion.
6. Produce a normalized comparison with URLs and a confidence note.

## Mobile app research

1. Use the correct store search for the platform, or use both when platform is
   unknown: `/v1/appstore/search` or `/v1/googleplay/search`.
2. Resolve the canonical app identifier.
3. Fetch the app detail and developer record.
4. Add ratings/reviews and privacy or data-safety disclosures.
5. Check availability, categories, and similar apps where relevant.
6. Use web, YouTube, and community routes only for context outside the store
   record.

## Content and community research

1. Free keyless `/v1/web/search` (Tier B) to establish the topic and primary
   sources.
2. Free keyless `/v1/youtube/search` (Tier B), video details, transcripts,
   comments, and related videos.
3. Free keyless `/v1/reddit/search_posts` (Tier B) and inspect relevant posts or
   subreddit listings.
4. Keyed `/v1/hackernews/search` and inspect high-value items with comments.
5. Synthesize themes while preserving which claims came from which source.

## Brand reconstruction

1. Confirm the official domain with the free keyless `/v1/web/search` (Tier B)
   plus a primary-site scrape, or start from a known domain with the free Brand
   host; use keyed routes only for continuation or deeper enrichment.
2. Free Brand host: `GET https://brand.replynodes.com/<domain>.json`.
3. Keyed `/v1/brand/fonts` and `/v1/brand/styleguide` signals where needed.
4. Map/crawl selected official pages for supporting copy and assets.
5. Report observed assets and source URLs; do not infer private guidelines or
   claim ownership beyond the public evidence.
