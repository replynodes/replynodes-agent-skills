#!/usr/bin/env bash
set -euo pipefail
root="${1:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
python3 - "$root" <<'PY'
import pathlib, re, sys
root = pathlib.Path(sys.argv[1]).resolve()
paths = [root / "SKILL.md"] + sorted(root.glob("skills/*/SKILL.md"))
assert paths[0].is_file(), "root SKILL.md is required"
for path in paths:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0] == "---", f"{path}: missing YAML frontmatter"
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise AssertionError(f"{path}: missing frontmatter terminator")
    front = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:])
    name = re.search(r"^name:\s*([^\s]+)\s*$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    assert name, f"{path}: name required"
    assert desc and 1 <= len(desc.group(1).strip()) <= 1024, f"{path}: description required"
    expected = "replynodes" if path == root / "SKILL.md" else path.parent.name
    assert name.group(1).strip('"\'') == expected, f"{path}: name must be {expected}"
    assert "https://mcp.replynodes.com/mcp" in body, f"{path}: canonical MCP endpoint missing"
    assert "REPLYNODES_API_KEY" in body, f"{path}: secret-store guidance missing"
    assert re.search(r"read[- ]only", (front + "\n" + body), re.I), f"{path}: read-only boundary missing"
    assert not re.search(r"Bearer\s+[A-Za-z0-9_-]{40,}", front + "\n" + body), f"{path}: possible credential"
print(f"validated {len(paths)} skill files")
PY

# Fail closed on stale payment/auth and social-publishing identity in published skills.
! rg -n -i 'x402|usdc|wallet|blockchain|on-chain|payment-per-call|pay-per-call|social publishing platform|schedule.*publish|publish.*schedule|OpenClaw publishing' "$root/SKILL.md" "$root/skills" "$root/README.md" "$root/references" >/dev/null

grep -F 'https://mcp.replynodes.com/mcp' "$root/SKILL.md" >/dev/null
grep -F 'https://docs.replynodes.com/docs/auth' "$root/README.md" >/dev/null
printf 'ReplyNodes skill validation passed for %s\n' "$root"
