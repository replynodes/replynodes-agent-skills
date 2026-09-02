# Fomo App Crypto Trading API

Published skill slug: `fomo-app-data-api`.

This skill provides x402 pay-per-request access to the documented read-only
Fomo App crypto trading data API for agent research across Solana, meme coins
trading, crypto, social trading, and on-chain data. Responses are normalized
JSON; the package does not sign wallets or execute trades.

Portable ClawHub-ready skill for the documented FOMO API surface at
`https://api.replynodes.com/v1/fomo/*`.

The gateway advertises exact x402 payment negotiation for pay-per-request
reads; HTTP 402 is not evidence of payment or settlement. Bearer/prepaid
access may be available as a separate mode. The package
contains instructions only: it has no service code, dependencies, credentials,
wallet data, or upstream API access.

The supported routes and access-mode handling are in
[`SKILL.md`](SKILL.md). The package deliberately excludes wallet signing,
transactions, trading, and all mutations.
