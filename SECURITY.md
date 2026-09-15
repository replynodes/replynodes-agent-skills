# Security reporting

Please report suspected vulnerabilities privately through [GitHub Security Advisories](https://github.com/replynodes/replynodes-agent-skills/security/advisories/new). Do not put API keys, session tokens, provider tokens, or personal data in a public issue or pull request. Include the affected commit/tag, reproduction steps, impact, and a safe contact method.

This repository contains portable research instructions and deterministic validation scripts. It does not contain backend credentials, provider tokens, account identifiers, or API keys. The installed agent host owns any API key in its secure secret storage.

## Access boundaries

The skill only routes read-only public research through the official ReplyNodes MCP. It cannot grant permissions, select another tenant, access private accounts, operate provider sessions, perform writes, or bypass the host's MCP approval and secret-storage boundaries.

Inspect a release from its explicit Git commit or tag and review `SKILL.md`, `README.md`, `PROVENANCE.md`, and validation results before installing. Keep `REPLYNODES_API_KEY` in the host's secret/environment store; never put it in prompts, URLs, source files, tool output, or logs.
