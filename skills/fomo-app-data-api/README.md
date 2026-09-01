# FOMO Market Intelligence Reads

Published skill slug: `fomo-app-data-api`.

Portable ClawHub-ready skill for the documented read-only FOMO API surface at
`https://api.replynodes.com/v1/fomo/*`.

Install this directory as a skill and configure a gateway API key from
`https://app.replynodes.com/developers` in the host’s secret store. The package
contains instructions only: it has no service code, dependencies, credentials,
wallet data, or upstream API access.

The supported routes and exact `Authorization: Bearer ` handling are in
[`SKILL.md`](SKILL.md). The package deliberately excludes wallet signing,
transactions, trading, and all mutations.
