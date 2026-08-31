#!/usr/bin/env bash
set -euo pipefail
repo="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"$repo/scripts/validate-appstore-api.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
tar -C "$repo" --exclude=.git -cf - skills/appstore-api | tar -C "$tmp" -xf -
# Validate a clean extracted archive using the same invariant checks that do not depend on repo paths.
(cd "$tmp/skills/appstore-api" && sha256sum -c CHECKSUMS.txt >/dev/null && python3 - <<'PY'
import json
m=json.load(open('manifest.json'))
assert {c['path'] for c in m['capabilities']} == {'/v1/appstore/app','/v1/appstore/search','/v1/appstore/similar'}
PY
)
# Ensure no unexpected artifacts would be included in the published package.
expected='CHECKSUMS.txt INSTALL.md LICENSE PROVENANCE.md PUBLICATION.md SKILL.md evidence/publication-evidence.json llms.txt manifest.json references/appstore-mcp.schema.json references/appstore-public-v1.openapi.json references/endpoints.md skill-card.md'
actual="$(cd "$tmp/skills/appstore-api" && find . -type f -printf '%P\n' | sort | tr '\n' ' ' | sed 's/ $//')"
[[ "$actual" == "$expected" ]] || { echo "unexpected archive layout: $actual" >&2; exit 1; }
echo 'clean public archive and App Store package tests passed'
