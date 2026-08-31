#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/../skills/appstore-api" && pwd)"
for f in SKILL.md INSTALL.md PUBLICATION.md LICENSE llms.txt manifest.json CHECKSUMS.txt skill-card.md PROVENANCE.md evidence/publication-evidence.json references/appstore-mcp.schema.json references/appstore-public-v1.openapi.json references/endpoints.md; do
  [[ -f "$root/$f" ]] || { echo "missing $f" >&2; exit 1; }
done
python3 - "$root" <<'PY'
import json, pathlib, sys
root=pathlib.Path(sys.argv[1])
for rel in ['manifest.json','evidence/publication-evidence.json','references/appstore-mcp.schema.json','references/appstore-public-v1.openapi.json']:
    json.loads((root/rel).read_text())
m=json.loads((root/'manifest.json').read_text())
assert m['version'] == '1.0.10'
routes={c['path'] for c in m['capabilities']}
assert routes == {'/v1/appstore/app','/v1/appstore/search','/v1/appstore/similar'}
assert all(c['method'] == 'GET' for c in m['capabilities'])
assert m['source_of_truth']['repository'] == 'replynodes/replynodes-agent-skills'
assert m['source_of_truth']['path'] == 'skills/appstore-api'
PY
(cd "$root" && sha256sum -c CHECKSUMS.txt >/dev/null)
# Reject private implementation topology and secret-like material from distributable assets.
if rg -n -I '(services/(appstore-fetcher|social-data-skills)|replynodes-fetcher|/home/hermes|APPSTORE_FETCHER_|internal/(capabilities|contract|providerclient))' "$root"; then
  echo 'private implementation reference found' >&2; exit 1
fi
if rg -n -I '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|Bearer[[:space:]]+[A-Za-z0-9._-]{24,}|(api[_-]?key|client[_-]?secret|access[_-]?token|session[_-]?token)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{16,})' "$root"; then
  echo 'credential-like value found' >&2; exit 1
fi
if ! rg -q '/v1/appstore/app' "$root/SKILL.md" || ! rg -q '/v1/appstore/search' "$root/SKILL.md" || ! rg -q '/v1/appstore/similar' "$root/SKILL.md"; then
  echo 'documented routes missing' >&2; exit 1
fi
if ! rg -qi 'x402 v2' "$root/SKILL.md" || ! rg -qi 'Bearer workspace' "$root/SKILL.md"; then
  echo 'truthful access documentation missing' >&2; exit 1
fi
echo 'public App Store package validation passed (v1.0.10)'
