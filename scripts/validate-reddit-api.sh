#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/../skills/reddit-api" && pwd)"
for f in SKILL.md README.md INSTALL.md PUBLICATION.md PROVENANCE.md LICENSE llms.txt manifest.json CHECKSUMS.txt skill-card.md references/reddit-api-mcp.schema.json references/endpoints.md references/scenarios.md; do
  [[ -f "$root/$f" ]] || { echo "missing $f" >&2; exit 1; }
done
python3 - "$root" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
for rel in ['manifest.json', 'references/reddit-api-mcp.schema.json']:
    json.loads((root / rel).read_text())
m = json.loads((root / 'manifest.json').read_text())
assert m['version'] == '1.1.0', m['version']
assert m['distribution']['version'] == '1.1.0'
expected = {
    '/v1/reddit/capabilities',
    '/v1/reddit/subreddit_posts/{subreddit}',
    '/v1/reddit/post_by_id/{id}',
    '/v1/reddit/post_by_permalink',
    '/v1/reddit/search_posts',
    '/v1/reddit/user_posts/{username}',
    '/v1/reddit/user_activity/{username}',
}
got = {c['path'] for c in m['capabilities']}
assert got == expected, f"capability paths mismatch: got {sorted(got)} want {sorted(expected)}"
assert all(c['method'] == 'GET' for c in m['capabilities']), 'all capabilities must be GET-only'
assert m['source_of_truth']['repository'] == 'replynodes/replynodes-agent-skills'
assert m['source_of_truth']['path'] == 'skills/reddit-api'
assert m['mode'] == 'readonly'
# Current prepaid-credit contract: a single Bearer fetcher key, no anonymous or pay-per-call path.
auth = m['auth']
assert auth['mode'] == 'bearer_prepaid_credit'
assert auth['credential_required'] is True
assert auth['credential_env_var'] == 'REPLYNODES_API_KEY'
assert auth['free_plan_one_time_credits'] == 500
assert auth['cost_credits_per_request'] == 2
assert auth['cost_credits_on_failure'] == 0
assert auth['invalid_credential_http_status'] == 401
assert auth['invalid_credential_code'] == 'invalid_or_expired_token'
priced = [c for c in m['capabilities'] if c['operation'] != 'capabilities']
assert all(c['auth_required'] is True for c in priced), 'priced routes must require auth'
assert all(c['price_credits'] == 2 for c in priced), 'priced routes must cost 2 credits'
free = [c for c in m['capabilities'] if c['operation'] == 'capabilities'][0]
assert free['auth_required'] is False
assert free['price_credits'] == 0
PY
(cd "$root" && sha256sum -c CHECKSUMS.txt >/dev/null)
# Reject private implementation topology and secret-like material from distributable assets.
if rg -n -I '(services/(reddit-fetcher|social-data-skills)|replynodes-fetcher|/home/hermes|REDDIT_FETCHER_|internal/(capabilities|contract|providerclient))' "$root"; then
  echo 'private implementation reference found' >&2; exit 1
fi
if rg -n -I '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|Bearer[[:space:]]+[A-Za-z0-9._-]{24,}|(api[_-]?key|client[_-]?secret|access[_-]?token|session[_-]?token)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{16,})' "$root"; then
  echo 'credential-like value found' >&2; exit 1
fi
# The current contract is prepaid-credit Bearer auth only: no x402/USDC/wallet/chain-payment claims.
if rg -n -I -i '(x402|USDC|eip155|X-PAYMENT|top-?up|0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913|payment-required|payment challenge)' "$root"; then
  echo 'legacy payment (x402/USDC/wallet) claim found' >&2; exit 1
fi
if rg -q 'REDDIT_API_KEY' "$root"; then
  echo 'stale REDDIT_API_KEY env var reference found; use REPLYNODES_API_KEY' >&2; exit 1
fi
# All seven documented routes must appear in SKILL.md.
for path in capabilities subreddit_posts post_by_id post_by_permalink search_posts user_posts user_activity; do
  needle="/v1/reddit/$path"
  if ! rg -q -F "$needle" "$root/SKILL.md"; then
    echo "documented route $needle missing from SKILL.md" >&2; exit 1
  fi
done
# The Setup block and the current prepaid-credit contract must be documented up front.
for needle in 'app.replynodes.com/auth' 'app.replynodes.com/developers' '500 one-time credits' 'REPLYNODES_API_KEY' 'YOUR_FETCHER_KEY'; do
  if ! rg -qF "$needle" "$root/SKILL.md"; then
    echo "Setup content missing from SKILL.md: $needle" >&2; exit 1
  fi
  if ! rg -qF "$needle" "$root/llms.txt"; then
    echo "Setup content missing from llms.txt: $needle" >&2; exit 1
  fi
done
if ! rg -qi '2 prepaid credits' "$root/SKILL.md" || ! rg -qi '401' "$root/SKILL.md"; then
  echo 'prepaid-credit pricing or 401 error behavior missing from SKILL.md' >&2; exit 1
fi
# No write-capability claims allowed.
if rg -qi '(submit|vote|favorite)[[:space:]]+(post|posts|comments)' "$root/SKILL.md"; then
  echo 'write-capability claim found' >&2; exit 1
fi
echo 'public Reddit package validation passed (v1.1.0)'
