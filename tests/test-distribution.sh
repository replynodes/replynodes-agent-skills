#!/usr/bin/env bash
set -euo pipefail
root="${1:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
python3 - "$root" <<'PY'
import json
import re
import sys
from pathlib import Path
import csv

root = Path(sys.argv[1]).resolve()
readme = (root / "README.md").read_text(encoding="utf-8")
distribution = (root / "references/company-research-distribution.md").read_text(encoding="utf-8")
skill = (root / "skills/company-research/SKILL.md").read_text(encoding="utf-8")
taxonomy = json.loads((root / "skills.sh.json").read_text(encoding="utf-8"))
baseline_path = root / "references/discovery-query-baseline.csv"
with baseline_path.open(newline="", encoding="utf-8") as handle:
    baseline = list(csv.DictReader(handle))

FOCUSED_CTA = "npx skills add https://github.com/replynodes/replynodes-agent-skills/tree/main/skills/company-research"

assert "https://github.com/replynodes/replynodes-agent-skills" in readme
assert "https://replynodes.com/?skill=company-research&campaign=company-research" in readme
assert FOCUSED_CTA in readme
assert FOCUSED_CTA in distribution
assert FOCUSED_CTA in skill
assert "npx skills add replynodes/replynodes-agent-skills" in readme
assert "--skill company-research --full-depth" not in readme
assert "company-research-distribution.md" in readme
assert len(baseline) == 30, f"discovery baseline must contain 30 rows, found {len(baseline)}"
assert len({row["query"] for row in baseline}) == 30, "discovery queries must be unique"
assert all(row["target_slug"] for row in baseline), "every discovery query needs a target slug"

examples = sorted((root / "examples/github-actions").glob("*.yml"))
assert len(examples) == 5, f"expected five workflow examples, found {len(examples)}"
for example in examples:
    text = example.read_text(encoding="utf-8")
    assert "npx --yes skills add" not in text.replace("# npx --yes skills add", ""), (
        f"{example.name} must not run a recurring install"
    )
    assert "https://github.com/replynodes/replynodes-agent-skills" in text
assert "PENDING" in distribution
assert re.search(r"two\s+separate UTC calendar days", distribution)
assert "owner-IP" in distribution
assert "https://clawhub.ai/replynodes-ai/skills/company-research" in distribution
assert "https://www.skills.sh/replynodes/replynodes-agent-skills/company-research" in distribution

skills = {
    skill_name
    for grouping in taxonomy["groupings"]
    for skill_name in grouping["skills"]
}
assert "company-research" in skills, "company-research missing from skills.sh taxonomy"
# Preserve the approved #714/#56 public skill, including the renamed provider slug.
assert "app-store-api" in skills, "app-store-api missing from skills.sh taxonomy"
# Every production skill marked public must be represented in the canonical
# taxonomy; this prevents a public focused skill from silently becoming an
# ungrouped registry surface.
public = set()
for skill_file in [root / "SKILL.md", *sorted((root / "skills").glob("*/SKILL.md"))]:
    text = skill_file.read_text(encoding="utf-8")
    match = re.search(r"(?m)^name:\s*([A-Za-z0-9_-]+)\s*$", text)
    internal = re.search(r"(?m)^\s*internal:\s*(true|false)\s*$", text)
    assert match and internal, f"{skill_file} must declare name and internal"
    if internal.group(1) == "false":
        public.add(match.group(1))
assert public == skills & public, (
    "all public production skills must be present in skills.sh taxonomy: "
    f"missing={sorted(public - skills)}"
)
# Legacy/internal aliases must not be presented as public acquisition choices.
for legacy in (
    "app-store-research",
    "google-play-research",
    "reddit-research",
    "youtube-research",
    "brandkitfetch",
    "brand-kit-fetch",
):
    assert legacy not in skills, f"legacy alias {legacy} must not be a public taxonomy entry"

# Keep this repository canonical: the attribution entry must not point at a
# marketplace fork or imply that a public counter is a retained-user metric.
assert not re.search(r"clawhub\.ai[^\n]*skill=company-research", readme)
assert re.search(r"marketplace install and\s+listing counts are external signals", readme)

print("distribution metadata and measurement contract passed")
PY
