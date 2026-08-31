# YouTube Data API

Neutral OpenClaw/ClawHub skill for **read-only YouTube public-data** agent intents: **search YouTube videos**, look up **YouTube video metadata**, **YouTube channel metadata**, public **YouTube comments**, **YouTube playlist items**, **related YouTube videos**, and **YouTube transcripts/captions**. All seven routes return normalized structured JSON through the ReplyNodes gateway.

Access is **pay-per-request in USDC via x402** on Base (`eip155:8453`) — no ReplyNodes account or API key is required on that path. An optional Bearer workspace API key is a separate, non-payment authorization path when configured. This package never logs in, writes to YouTube, signs payments, or claims settlement from HTTP 402.

## Install

```sh
openclaw skills install @replynodes-ai/youtube-public-api --version 1.0.4
```

See `SKILL.md` for exact paths, input schemas, normalized output examples, per-endpoint price/payment modes, transcript-unavailable behavior, and safety boundaries.
