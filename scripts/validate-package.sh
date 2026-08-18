#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
test -f "$root/SKILL.md"
test -f "$root/README.md"
test -f "$root/LICENSE"
test -f "$root/PROVENANCE.md"
head -n 1 "$root/SKILL.md" | grep -Fx -- '---' >/dev/null
sed -n '2,8p' "$root/SKILL.md" | grep -Fx -- 'name: replynodes' >/dev/null
grep -F 'description: Publish, cross-post, and schedule social media through ReplyNodes in OpenClaw.' "$root/SKILL.md" >/dev/null
grep -Fx -- 'homepage: https://replynodes.com/openclaw' <(sed -n '2,8p' "$root/SKILL.md") >/dev/null
grep -F 'npx skills add replynodes/replynodes-agent-skills --skill replynodes --agent openclaw --yes' "$root/README.md" >/dev/null
grep -F 'openclaw skills install skills-sh:replynodes/replynodes-agent-skills/replynodes' "$root/README.md" >/dev/null
! rg -n '(client_secret[" ]*[:=][" ]*[A-Za-z0-9_-]{12,}|api[_-]?key[" ]*[:=][" ]*[A-Za-z0-9_-]{12,}|Bearer [A-Za-z0-9_-]{40,})' "$root" --glob '!scripts/validate-package.sh' >/dev/null
echo 'ReplyNodes skill package validation passed'
