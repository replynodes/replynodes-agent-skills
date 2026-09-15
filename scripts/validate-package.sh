#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 - "$root" <<'PY'
import pathlib, re, sys
root = pathlib.Path(sys.argv[1])
skill = (root / "SKILL.md").read_text()
lines = skill.splitlines()
assert lines and lines[0] == "---"
try:
    end = lines.index("---", 1)
except ValueError:
    raise AssertionError("SKILL.md must have YAML frontmatter and a body")
front = "\n".join(lines[1:end])
body = "\n".join(lines[end + 1:])
assert re.search(r"^name:\s*replynodes\s*$", front, re.M)
m = re.search(r"^description:\s*(.+)$", front, re.M)
assert m and 1 <= len(m.group(1).strip()) <= 1024
assert "https://mcp.replynodes.com/mcp" in body
assert "Authorization: Bearer ${REPLYNODES_API_KEY}" in body
assert "references/live-capability-routing.md" in body
assert "references/research-workflows.md" in body
assert not re.search(r"Bearer\s+[A-Za-z0-9_-]{40,}", skill)
for rel in ("SKILL.md", "README.md", "LICENSE", "PROVENANCE.md", "references/live-capability-routing.md", "references/research-workflows.md"):
    assert (root / rel).is_file(), rel
print("SKILL.md frontmatter and package invariants passed")
PY

grep -F 'npx skills add https://github.com/replynodes/replynodes-agent-skills --skill replynodes' "$root/README.md" >/dev/null
grep -F 'https://skills.sh/b/replynodes/replynodes-agent-skills' "$root/README.md" >/dev/null
grep -F 'https://mcp.replynodes.com/mcp' "$root/SKILL.md" >/dev/null
grep -F '51' "$root/references/live-capability-routing.md" >/dev/null
! rg -n '(client_secret[" ]*[:=][" ]*[A-Za-z0-9_-]{12,}|api[_-]?key[" ]*[:=][" ]*[A-Za-z0-9_-]{12,}|Bearer [A-Za-z0-9_-]{40,})' "$root" --glob '!scripts/validate-package.sh' >/dev/null
echo 'ReplyNodes umbrella skill validation passed'
