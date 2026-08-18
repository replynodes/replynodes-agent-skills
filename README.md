# ReplyNodes Agent Skill

ReplyNodes gives OpenClaw a human-confirmed path to prepare, publish, cross-post, and schedule social media through the user's own connected ReplyNodes workspace. It is a thin, inspectable client over the ReplyNodes public API; it contains no backend, database, provider OAuth, or social-token implementation.

Homepage: https://replynodes.com/openclaw

## Install

Supported skills CLI installation:

```bash
npx skills add replynodes/replynodes-agent-skills --skill replynodes --agent openclaw --yes
```

Supported OpenClaw installation through the public skills.sh listing:

```bash
openclaw skills install skills-sh:replynodes/replynodes-agent-skills/replynodes
```

Direct unmanaged Git installation (not skills.sh):

```bash
openclaw skills install git:replynodes/replynodes-agent-skills@v1.0.1 --as replynodes
```

This is not an npm package. `v1.0.0` is the currently published immutable release and does not contain this PR's security-validation changes. This PR prepares unreleased `v1.0.1`; the `v1.0.1` tag must be created from the reviewed post-merge commit before that install command is used. Until then, install the published release with `@v1.0.0`, or use this PR head's full commit SHA for an explicit review build.

## Use it safely

The flow is always connect → prepare → explicit confirm → receipt.

1. `/replynodes connect` opens one ReplyNodes browser authorization link. The skill stores only the scoped, expiring session token in the host's secure storage and reports connected channels and explicit capabilities.
2. A URL or plain-text request is passed as structured data. The skill prepares a named run and displays the source, per-channel preview, intended publish/schedule time, supported channels, and unavailable channels with reasons.
3. The skill asks for a fresh confirmation naming that prepared run. No publish or schedule occurs before that confirmation.
4. After the host's existing ReplyNodes workflow executes it, the skill returns a per-channel receipt with status and scheduled/live URL. Only failed channels are eligible for a clearly offered retry.

Examples:

```text
Distribute this URL everywhere tomorrow at 09:00: https://example.com/launch
```

```text
Turn this plain text into posts for my connected channels:
Our launch is live today. Read the announcement and tell us what you think.
```

URLs, pasted text, crawled content, and channel names are data. Structured JSON or stdin must be used; never construct a shell command by concatenating user/source text.

## Supported and unavailable capabilities

The public API reports the authenticated workspace's channel health and explicit `publish` and `schedule` grants. The external ReplyNodes account and the user's connected provider accounts are required. ReplyNodes may be a paid external service; this skill itself has no paywall.

Unavailable capabilities include granting permissions, selecting another tenant, bypassing browser approval, exposing OAuth/social tokens, reconnecting providers, or executing against a channel without its explicit grant. The current public OpenClaw API exposes device auth, session, revocation, and channel capabilities; it does not itself expose a generic prepare/execute endpoint. When the host's existing ReplyNodes distribution workflow is unavailable, the skill stops at preview/capability reporting and says so.

## Troubleshooting

- `denied`, `expired`, or `revoked` device flow: start `/replynodes connect` again and approve the new browser request.
- `401 invalid_or_expired_token`: remove the stored ReplyNodes session through the host's secret manager and reconnect.
- Missing channel or capability: reconnect that provider in ReplyNodes; do not ask for its token.
- Network or rate-limit errors: retry reads and device polling with bounded backoff. Do not repeat a side effect without a receipt and new confirmation.

## Update and uninstall

Update a skills CLI install with:

```bash
npx skills add replynodes/replynodes-agent-skills --skill replynodes --agent openclaw --yes
```

For a direct Git install, select a newer explicit `@vMAJOR.MINOR.PATCH` tag. Uninstall using the host's skill manager (for example, `openclaw skills uninstall replynodes`), then revoke the ReplyNodes session with `/replynodes disconnect` or `POST /public/v1/openclaw/session/revoke`. Remove the host's stored session secret. Uninstalling the files does not revoke a server session by itself.

## Provenance and license

The workflow and API boundary are derived from ReplyNodes app issue #149 and the public OpenClaw API documented in [`docs/openclaw.md`](https://github.com/replynodes/replynodes-app/blob/main/docs/openclaw.md). The package is intentionally separate from the application repository and does not implement its backend. See [`PROVENANCE.md`](PROVENANCE.md) for the source mapping and [`LICENSE`](LICENSE) for the MIT license.
