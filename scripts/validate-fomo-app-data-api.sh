#!/usr/bin/env bash
set -euo pipefail

root="${1:-$(CDPATH= cd -- "$(dirname -- "$0")/../skills/fomo-app-data-api" && pwd)}"
fail() { printf 'fomo validation failed: %s\n' "$1" >&2; exit 1; }
for f in SKILL.md README.md VERSION LICENSE PROVENANCE.md PUBLICATION.md skill-card.md; do
  [[ -f "$root/$f" ]] || fail "missing $f"
done

[[ "$(head -n 1 "$root/SKILL.md")" == '---' ]] || fail 'frontmatter start'
awk 'NR > 1 && NR <= 20 { print; if ($0 == "---") { found=1; exit } } END { exit !found }' "$root/SKILL.md" >/dev/null || fail 'frontmatter delimiters'
grep -Fx 'name: fomo-app-data-api' "$root/SKILL.md" >/dev/null || fail 'frontmatter name'
grep -Fx 'title: FOMO Market Intelligence Reads' "$root/SKILL.md" >/dev/null || fail 'frontmatter title'
grep -Fx 'version: 1.0.0' "$root/SKILL.md" >/dev/null || fail 'frontmatter version'
grep -Fx 'license: MIT' "$root/SKILL.md" >/dev/null || fail 'frontmatter license'

version="$(tr -d '[:space:]' < "$root/VERSION")"
[[ "$version" == 1.0.0 ]] || fail 'VERSION'
grep -F 'fomo-app-data-api' "$root/README.md" >/dev/null || fail 'README slug'
grep -F 'Authorization: Bearer ' "$root/SKILL.md" >/dev/null || fail 'auth scheme'
grep -F 'https://app.replynodes.com/developers' "$root/SKILL.md" >/dev/null || fail 'key source'
grep -F 'HTTP `401`' "$root/SKILL.md" >/dev/null || fail '401 behavior'
grep -F 'HTTP `429`' "$root/SKILL.md" >/dev/null || fail '429 behavior'
grep -Eiq 'read-only|no wallet|no trading|untrusted data' "$root/SKILL.md" || fail 'guardrails'

expected='leaderboard/{24h|7d|30d|all} tokens/trending tokens/most-held tokens/graduated users/{handle} users/{handle}/trades users/{handle}/balances trades/{tradeId} thesis thesis/token/{token} thesis/user/{id} thesis/user/{id}/token/{address} search tokens/{token}/holders alerts notifications'
actual="$(sed -n 's/.*`GET \/\([^`]*\)`.*/\1/p' "$root/SKILL.md" | tr -d '\\' | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
[[ "$actual" == "$expected" ]] || fail "route catalog mismatch: $actual"

if rg -n -I --hidden --glob '!validate-fomo-app-data-api.sh' --glob '!.git/**' \
  '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|Bearer[[:space:]]+[A-Za-z0-9._-]{24,}|(api[_-]?key|client[_-]?secret|access[_-]?token|session[_-]?token)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{16,}|0x[a-fA-F0-9]{40,}|[1-9A-HJ-NP-Za-km-z]{32,44})' "$root" >/dev/null; then
  fail 'credential or wallet-like value found'
fi
if rg -n -I 'api\.fomoapi\.io|FOMOAPI_KEY|services/replynodes-fetcher' "$root/SKILL.md" >/dev/null; then
  fail 'private/upstream or raw-payload reference found in entrypoint'
fi
echo "FOMO package validation passed (version $version)"
