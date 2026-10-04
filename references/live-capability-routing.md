# Live capability routing snapshot

This snapshot was read from `https://mcp.replynodes.com/mcp` with
`initialize` and `tools/list` on 2026-10-04. The live server returned 66 tools.
The server remains authoritative if this file and production differ. Inspect the
current input schema before every call.

## Web and website research (5)

- `web_search`
- `webcontext_scrape`
- `webcontext_crawl`
- `webcontext_map`
- `webcontext_brand`

## Brand research and assets (6)

- `brand_retrieve`
- `brand_search`
- `brand_styleguide`
- `brand_fonts`
- `brand_logo`
- `read_document`

## Apple App Store (9)

- `search`
- `suggest`
- `app`
- `reviews`
- `ratings`
- `developer`
- `privacy`
- `similar`
- `list`

These unprefixed names are the current live App Store inventory. Do not infer
provider tool names from older snapshots or internal prefixes. No verified
no-key App Store data path is claimed by this package.

## Google Play (11)

- `googleplay_app_details`
- `googleplay_search`
- `googleplay_similar_apps`
- `googleplay_permissions`
- `googleplay_reviews`
- `googleplay_developer`
- `googleplay_categories`
- `googleplay_category_apps`
- `googleplay_suggest`
- `googleplay_availability`
- `googleplay_data_safety`

## YouTube (7)

- `youtube_search`
- `youtube_video`
- `youtube_channel`
- `youtube_comments`
- `youtube_playlist`
- `youtube_related`
- `youtube_transcript`

## Reddit (6)

- `search_posts`
- `subreddit_posts`
- `post_by_id`
- `post_by_permalink`
- `user_activity`
- `user_posts`

## Hacker News (9)

- `hackernews_stories_top`
- `hackernews_stories_new`
- `hackernews_stories_best`
- `hackernews_stories_ask`
- `hackernews_stories_show`
- `hackernews_stories_job`
- `hackernews_search`
- `hackernews_item`
- `hackernews_user`

## Company intelligence and monitors (9)

- `get_company_events`
- `get_company_history`
- `get_recent_company_events`
- `get_company_intelligence`
- `monitor_list`
- `monitor_create`
- `monitor_get`
- `monitor_update`
- `monitor_changes`
- `monitor_runs`

## Gateway health and capabilities (4)

- `get_fetcher_healthz`
- `get_fetcher_readyz`
- `get_v1_hackernews_capabilities`

## Routing rules

- Use the exact live tool name and inspect its current schema before supplying
  arguments; this snapshot is evidence, not a substitute for `tools/list`.
- Use search/discovery tools to resolve identifiers before detail tools when the
  user has provided only a name or keyword.
- Keep the source URL, provider, and retrieval context with the result.
- Do not advertise or call provider families absent from the current inventory.
- This MCP surface is read-only for public research; do not infer write,
  account-management, purchase, publishing, or private-data capabilities.
