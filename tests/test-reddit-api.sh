#!/usr/bin/env bash
set -euo pipefail
repo="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"$repo/scripts/validate-reddit-api.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
tar -C "$repo" --exclude=.git -cf - skills/reddit-api | tar -C "$tmp" -xf -
# Validate a clean extracted archive using the same invariant checks that do not depend on repo paths.
(cd "$tmp/skills/reddit-api" && sha256sum -c CHECKSUMS.txt >/dev/null && python3 - <<'PY'
import json
m = json.load(open('manifest.json'))
expected = {
    '/v1/reddit/capabilities',
    '/v1/reddit/subreddit_posts/{subreddit}',
    '/v1/reddit/post_by_id/{id}',
    '/v1/reddit/post_by_permalink',
    '/v1/reddit/search_posts',
    '/v1/reddit/user_posts/{username}',
    '/v1/reddit/user_activity/{username}',
}
assert {c['path'] for c in m['capabilities']} == expected
assert m['mode'] == 'readonly'
assert m['version'] == '1.1.0'
assert m['auth']['mode'] == 'bearer_prepaid_credit'
assert m['auth']['credential_env_var'] == 'REPLYNODES_API_KEY'
PY
)
# Ensure no unexpected artifacts would be included in the published package.
expected='CHECKSUMS.txt INSTALL.md LICENSE PROVENANCE.md PUBLICATION.md README.md SKILL.md VERSION llms.txt manifest.json references/endpoints.md references/reddit-api-mcp.schema.json references/scenarios.md skill-card.md'
actual="$(cd "$tmp/skills/reddit-api" && find . -type f -printf '%P\n' | sort | tr '\n' ' ' | sed 's/ $//')"
[[ "$actual" == "$expected" ]] || { echo "unexpected archive layout: $actual" >&2; exit 1; }
echo 'clean public archive and Reddit package tests passed'
