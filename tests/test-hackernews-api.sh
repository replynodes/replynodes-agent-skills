#!/usr/bin/env bash
set -euo pipefail
repo="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"$repo/scripts/validate-hackernews-api.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
tar -C "$repo" --exclude=.git -cf - skills/hackernews-api | tar -C "$tmp" -xf -
# Validate a clean extracted archive using the same invariant checks that do not depend on repo paths.
(cd "$tmp/skills/hackernews-api" && sha256sum -c CHECKSUMS.txt >/dev/null && python3 - <<'PY'
import json
m = json.load(open('manifest.json'))
expected = {
    '/v1/hackernews/stories_top',
    '/v1/hackernews/stories_new',
    '/v1/hackernews/stories_best',
    '/v1/hackernews/stories_ask',
    '/v1/hackernews/stories_show',
    '/v1/hackernews/stories_job',
    '/v1/hackernews/item/{id}',
    '/v1/hackernews/user/{handle}',
    '/v1/hackernews/search',
}
assert {c['path'] for c in m['capabilities']} == expected
assert m['mode'] == 'readonly'
assert m['version'] == '1.0.0'
PY
)
# Ensure no unexpected artifacts would be included in the published package.
expected='CHECKSUMS.txt INSTALL.md LICENSE PROVENANCE.md PUBLICATION.md SKILL.md evidence/publication-evidence.json llms.txt manifest.json references/endpoints.md references/hackernews-mcp.schema.json references/hackernews-public-v1.openapi.json skill-card.md'
actual="$(cd "$tmp/skills/hackernews-api" && find . -type f -printf '%P\n' | sort | tr '\n' ' ' | sed 's/ $//')"
[[ "$actual" == "$expected" ]] || { echo "unexpected archive layout: $actual" >&2; exit 1; }
echo 'clean public archive and Hacker News package tests passed'