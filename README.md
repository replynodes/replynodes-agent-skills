# ReplyNodes Agent Skill

[![skills.sh](https://skills.sh/b/replynodes/replynodes-agent-skills)](https://skills.sh/replynodes/replynodes-agent-skills/replynodes)

ReplyNodes is a unified, read-only research layer for AI agents. The `replynodes`
skill teaches agents when to use the production ReplyNodes MCP, how to route
web, brand, app-store, YouTube, Reddit, and Hacker News research, and how to
combine those sources into useful workflows.

It does not duplicate the MCP schema. The live MCP remains authoritative for
available tools and arguments.

## Install from skills.sh

```bash
npx skills add https://github.com/replynodes/replynodes-agent-skills --skill replynodes
```

Installing the skill gives an agent a safe research playbook and routing guide
for the official ReplyNodes MCP.

## Production MCP

```text
https://mcp.replynodes.com/mcp
```

Production calls require a ReplyNodes API key sent as:

```text
Authorization: Bearer ${REPLYNODES_API_KEY}
```

Keep the key in the agent's secret/environment store. Do not paste it into chat,
URLs, source files, or logs. See the official [MCP documentation](https://docs.replynodes.com/docs/mcp),
[pricing](https://replynodes.com/pricing), and [authentication instructions](https://replynodes.com/auth.md).

## Skill contents

- `SKILL.md` — activation triggers, routing, connection, boundaries, and workflows.
- `references/live-capability-routing.md` — the verified live tool-family snapshot.
- `references/research-workflows.md` — concise multi-source research recipes.

## Validation

```bash
./scripts/validate-package.sh
./tests/test-package.sh
```

The package contains no backend code, provider credentials, social tokens, or
API keys. See [PROVENANCE.md](PROVENANCE.md) and [LICENSE](LICENSE).
