# Legitimate distribution growth plan

Status: P0 implementation baseline. This document separates source work from external index state.

## Canonical install funnel

Use the canonical GitHub source and `--full-depth` for focused nested skills:

```bash
# Umbrella routing
npx --yes skills add https://github.com/replynodes/replynodes-agent-skills --skill replynodes --full-depth

# Priority focused skills
npx --yes skills add https://github.com/replynodes/replynodes-agent-skills --skill company-research --full-depth
npx --yes skills add https://github.com/replynodes/replynodes-agent-skills --skill url-to-markdown --full-depth
npx --yes skills add https://github.com/replynodes/replynodes-agent-skills --skill app-store-api --full-depth
```

The current official CLI can stop at the root `SKILL.md` for a remote repository. Therefore a bare focused command is not treated as passing. Do not remove the umbrella or create duplicate top-level copies merely to hide this upstream/index limitation. Internal validation uses `DISABLE_TELEMETRY=1`; user CTAs do not.

## 30-query discovery baseline

Run the query set in `references/discovery-query-baseline.csv` against the public find/search surface available at the time. Record UTC time, exact query, target slug, visibility, rank only when the response exposes rank, competing result names, URL, and method. `not observable` is a valid rank value; it is not a negative result.

Query families:

- company research: company profile, business intelligence, prospect/account research, vendor due diligence, company domain research, first-party company brief;
- URL conversion: URL to Markdown, webpage to Markdown, article extraction, docs page for LLM, HTML to Markdown, clean web context;
- App Store: iOS app search, App Store reviews, app ratings, app privacy, developer apps, similar iPhone apps;
- combined workflows: research SaaS competitors, public web research for agents, RAG page extraction, current public product research, no-key web research.

## Daily baseline

Record one immutable daily row in `references/distribution-daily-baseline.csv` after public readback:

- external: Skills.sh visible installs, ClawHub downloads/installs/stars, GitHub stars, repository views/clones/referrers;
- product: distinct downstream callers, requests, API-key creation after first attributed use, sibling-skill adoption, and two-UTC-day retention;
- attribution: source URL/campaign, skill header/run ID where the existing contract supports it, and exclusions.

External counters are display signals. They are never called genuine users, conversions, or retention. The 30-day window starts only after a verified post-merge readback and remains `PENDING` until the second eligible UTC day exists.

## Upstream distribution actions

1. Submit a focused correction PR/request to `vercel-labs/skills` for stale Skills.sh entries with canonical repo, branch, exact paths, source SHA, expected slugs, and install commands.
2. Keep ClawHub links as acquisition surfaces only; reconcile `replynodes-ai` owner/slugs through the authenticated owner path. The current `brand-kit@1.0.0` reservation is blocked and must not be bypassed with a duplicate or invented version.
3. Prefer useful integrations and community directories that accept canonical GitHub links and read-only capability descriptions. Measure referral traffic with existing UTM attribution; do not mass-submit or repeat submissions.
4. Promote the five workflow examples through changelog/docs/community posts only when they solve a real developer task; never ask users to install repeatedly.

## Acceptance evidence

- exact source commit and changed-file list;
- `git diff --check`, package validator, distribution tests;
- clean focused and umbrella install logs with installed paths/content hashes;
- one safe keyless smoke for each priority skill;
- 30-query baseline with unavailable ranks called out;
- public Skills.sh/ClawHub readback, including stale/soft-200 classification;
- independent review of the exact PR head.
