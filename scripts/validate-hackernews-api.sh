#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/../skills/hackernews-api" && pwd)"
for f in SKILL.md INSTALL.md PUBLICATION.md LICENSE llms.txt manifest.json CHECKSUMS.txt skill-card.md PROVENANCE.md evidence/publication-evidence.json references/hackernews-mcp.schema.json references/hackernews-public-v1.openapi.json references/endpoints.md; do
  [[ -f "$root/$f" ]] || { echo "missing $f" >&2; exit 1; }
done
python3 - "$root" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
for rel in ['manifest.json','evidence/publication-evidence.json','references/hackernews-mcp.schema.json','references/hackernews-public-v1.openapi.json']:
    json.loads((root / rel).read_text())
m = json.loads((root / 'manifest.json').read_text())
assert m['version'] == '1.0.0'
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
got = {c['path'] for c in m['capabilities']}
assert got == expected, f"capability paths mismatch: got {sorted(got)} want {sorted(expected)}"
assert all(c['method'] == 'GET' for c in m['capabilities']), 'all capabilities must be GET-only'
assert m['source_of_truth']['repository'] == 'replynodes/replynodes-agent-skills'
assert m['source_of_truth']['path'] == 'skills/hackernews-api'
assert m['mode'] == 'readonly'
assert m['platform'] == 'hackernews'
# Sanity: every auth-required capability entry is explicitly false (HN is public).
assert all(c['auth_required'] is False for c in m['capabilities']), 'all capabilities must be unauthenticated (x402/bearer are gateway-level)'
# Sanity: prohibited_claims present.
assert 'prohibited_claims' in m and len(m['prohibited_claims']) >= 5
PY
(cd "$root" && sha256sum -c CHECKSUMS.txt >/dev/null)
# Reject private implementation topology and secret-like material from distributable assets.
if rg -n -I '(services/(hackernews-fetcher|social-data-skills)|replynodes-fetcher|/home/hermes|HACKERNEWS_FETCHER_|internal/(capabilities|contract|providerclient))' "$root"; then
  echo 'private implementation reference found' >&2; exit 1
fi
if rg -n -I '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|Bearer[[:space:]]+[A-Za-z0-9._-]{24,}|(api[_-]?key|client[_-]?secret|access[_-]?token|session[_-]?token)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{16,})' "$root"; then
  echo 'credential-like value found' >&2; exit 1
fi
# All nine documented routes must appear in SKILL.md.
# Use fixed-string matching because route templates contain {id}/{handle}.
for path in stories_top stories_new stories_best stories_ask stories_show stories_job 'item/' 'user/' search; do
  needle="/v1/hackernews/$path"
  if ! rg -q -F "$needle" "$root/SKILL.md"; then
    echo "documented route $needle missing from SKILL.md" >&2; exit 1
  fi
done
# Truthful access documentation must mention both auth modes.
if ! rg -qi 'x402 v2' "$root/SKILL.md" || ! rg -qi 'Bearer workspace' "$root/SKILL.md"; then
  echo 'truthful access documentation missing' >&2; exit 1
fi
# No write-capability claims allowed.
if rg -qi '(submit|vote|favorite)[[:space:]]+(post|stories|comments)' "$root/SKILL.md"; then
  echo 'write-capability claim found' >&2; exit 1
fi
echo 'public Hacker News package validation passed (v1.0.0)'