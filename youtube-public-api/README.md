# YouTube Public Data

Neutral OpenClaw/ClawHub skill for read-only public YouTube data through the ReplyNodes gateway. It documents all seven deployed YouTube routes, Bearer authorization when available, and truthful x402 v2 negotiation handling. It never logs in, writes to YouTube, signs payments, or claims settlement from HTTP 402.

## Install

```sh
openclaw skills install @replynodes-ai/youtube-public-api --version 1.0.2
```

See `SKILL.md` for exact paths, parameters, transcript-unavailable behavior, and safety boundaries.
