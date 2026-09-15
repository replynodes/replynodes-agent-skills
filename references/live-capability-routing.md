# Live capability routing snapshot

This snapshot was checked against `https://mcp.replynodes.com/mcp` with
`initialize` and `tools/list`. The live server returned 51 read-only tools. The
server remains authoritative if this file and production differ.

## Web and website research (5)

- `web_search_web_search` — structured public web search.
- `webcontext_scrape` — clean Markdown for one URL.
- `webcontext_crawl` — bounded same-origin crawl.
- `webcontext_map` — discover and deduplicate site URLs.
- `webcontext_brand` — lightweight website brand signals.

## Brand research and assets (4)

- `brand_retrieve`
- `brand_search`
- `brand_fonts`
- `brand_styleguide`

Use these for public brand profile, discovery, fonts, typography, colors, logos,
and design-system signals. Inspect each live input schema before calling it.

## Apple App Store (9)

- `appstore_app`
- `appstore_developer`
- `appstore_list`
- `appstore_privacy`
- `appstore_ratings`
- `appstore_reviews`
- `appstore_search`
- `appstore_similar`
- `appstore_suggest`

## Google Play (11)

- `googleplay_app_details`
- `googleplay_availability`
- `googleplay_categories`
- `googleplay_category_apps`
- `googleplay_data_safety`
- `googleplay_developer`
- `googleplay_permissions`
- `googleplay_reviews`
- `googleplay_search`
- `googleplay_similar_apps`
- `googleplay_suggest`

## YouTube (7)

- `youtube_channel`
- `youtube_comments`
- `youtube_playlist`
- `youtube_related`
- `youtube_search`
- `youtube_transcript`
- `youtube_video`

## Reddit (6)

- `reddit_post_by_id`
- `reddit_post_by_permalink`
- `reddit_search_posts`
- `reddit_subreddit_posts`
- `reddit_user_activity`
- `reddit_user_posts`

## Hacker News (9)

- `hackernews_item`
- `hackernews_search`
- `hackernews_stories_ask`
- `hackernews_stories_best`
- `hackernews_stories_job`
- `hackernews_stories_new`
- `hackernews_stories_show`
- `hackernews_stories_top`
- `hackernews_user`

## Routing rules

- Use the exact live tool name and inspect its current schema before supplying
  arguments.
- Use search/discovery tools to resolve identifiers before detail tools when the
  user has provided only a name or keyword.
- Keep the source URL, provider, and retrieval context with the result.
- Do not advertise or call provider families absent from this live inventory.
