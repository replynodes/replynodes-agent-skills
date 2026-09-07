# Publication status & evidence - `hackernews-data-api` package

Status: **PREPARED** for ClawHub as `@replynodes-ai/hackernews-api`.
Version `1.1.7`. Moderation status: **PENDING**.

This package is a self-contained, anonymous, read-only Hacker News gateway skill. Registry evidence is recorded only after independent inspect and moderation checks.

## Evidence bundle

| Item | Location |
| --- | --- |
| Package manifest with per-file sizes and SHA-256 digests | `manifest.json` |
| `sha256sum`-style checksums | `CHECKSUMS.txt` |
| Machine-readable facts and prohibited-claims policy | `evidence/publication-evidence.json` |

Digests are generated from exactly the files shipped in the clean archive. The extracted package can verify itself with `sha256sum -c CHECKSUMS.txt`.

## Verification boundary

Repository-level validators and tests are source-repository tooling, not package contents. The distributed artifact is independently verifiable with its checksum inventory; it contains no executable install hooks, daemons, credential handlers, wallet code, or background activity.

## What this package does not claim

- No registry metrics, live availability, latency, uptime, or success-rate figures.
- No official Hacker News partnership, endorsement, or data-sharing arrangement.
- No submit, vote, comment, favorite, login, account, credential, payment, or other write capability; the surface is anonymous GET-only public reads.
- No payment settlement or wallet signing behavior.
