# Publication status & evidence - `appstore-api` package

Status: **PREPARED** for ClawHub as `@replynodes-ai/appstore-api`.
Version `1.1.0`. Moderation status: **PENDING**.

Prepared for ClawHub publication as @replynodes-ai/appstore-api; registry evidence is recorded only after independent inspect and moderation checks.

## Evidence bundle

| Item | Location |
| --- | --- |
| Package manifest with per-file sizes and SHA-256 digests | `manifest.json` |
| `sha256sum`-style checksums | `CHECKSUMS.txt` |
| Machine-readable facts and prohibited-claims policy | `evidence/publication-evidence.json` |

Digests are deterministic SHA-256 values over the committed bytes; regenerating
twice produces byte-identical trees (enforced by `../check_appstore.sh`).

## Local verification (must pass before any distribution decision)

```sh
bash services/social-data-skills/contracts/validate.sh
bash services/social-data-skills/catalog/check.sh
bash services/social-data-skills/catalog/package_check.sh
bash services/social-data-skills/catalog/check_appstore.sh
bash services/social-data-skills/catalog/package_check_appstore.sh
```

## What this package does not claim

- No registry or marketplace listing, download statistics, ratings, or community metrics exist for it.
- No live availability, latency, uptime, or success-rate figures are asserted anywhere; example payloads are illustrative fixtures, not captured responses.
- No official platform partnership, endorsement, license grant, or data-sharing arrangement is claimed.
- No purchase, review-submission, account, login, or other write/authenticated capability exists or is advertised; the surface is GET-only public reads.
- Route paths in this package are stable capability identifiers; public gateway exposure for this platform is issued to your workspace at onboarding.

## Publication boundaries

- The package is read-only and all documented routes are HTTP GET.
- The gateway supports a Bearer workspace-key path and x402 v2 negotiation.
- A 402 payment requirement is not evidence of settlement or successful paid access.
- No credentials, payer secrets, or fallback claims are included in this package.
