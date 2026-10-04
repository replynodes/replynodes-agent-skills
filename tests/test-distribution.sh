#!/usr/bin/env bash
set -euo pipefail
root="${1:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
python3 - "$root" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
readme = (root / "README.md").read_text(encoding="utf-8")
distribution = (root / "references/company-research-distribution.md").read_text(encoding="utf-8")
taxonomy = json.loads((root / "skills.sh.json").read_text(encoding="utf-8"))

assert "https://github.com/replynodes/replynodes-agent-skills" in readme
assert "https://replynodes.com/?skill=company-research&campaign=company-research" in readme
assert "--skill company-research --full-depth" in readme
assert "company-research-distribution.md" in readme
assert "PENDING" in distribution
assert re.search(r"two\s+separate UTC calendar days", distribution)
assert "owner-IP" in distribution
assert "https://clawhub.ai/replynodes-ai/skills/company-research" in distribution
assert "https://www.skills.sh/replynodes/replynodes-agent-skills/company-research" in distribution

skills = {
    skill
    for grouping in taxonomy["groupings"]
    for skill in grouping["skills"]
}
assert "company-research" in skills, "company-research missing from skills.sh taxonomy"

# Keep this repository canonical: the attribution entry must not point at a
# marketplace fork or imply that a public counter is a retained-user metric.
assert not re.search(r"clawhub\.ai[^\n]*skill=company-research", readme)
assert re.search(r"marketplace install and\s+listing counts are external signals", readme)

print("distribution metadata and measurement contract passed")
PY
