#!/usr/bin/env bash
# Deterministic, network-free checks for the 2026-10-07 registry readback.
# Verifies the inventory/sync artifacts are consistent with the raw readback
# JSON, that every registry claim carries a recorded live HTTP 200, that no
# fabricated registry host appears, and that relative links resolve.
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 - "$root" <<'PY'
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
inv = (root / "references/registry-inventory-2026-10-07.md").read_text(encoding="utf-8")
sync = (root / "references/registry-sync-2026-10-07.md").read_text(encoding="utf-8")
rb = json.loads((root / "references/registry-readback-2026-10-07.json").read_text(encoding="utf-8"))

# 1. readback schema and totals
assert rb["schema"] == "replynodes-registry-readback/v1"
assert rb["source_head"] == "166f0f515afb27e7cc393fa5b0c236005661b9fc"
assert rb["skills_sh"]["badge_total_installs"] == 32
real = rb["skills_sh"]["real_listings"]
assert len(real) == 17, f"expected 17 skills.sh real listings, got {len(real)}"
assert sum(v["installs"] for v in real.values()) == 32, "skills.sh install total must be 32"

# 2. every recorded registry claim must carry a live HTTP 200
for slug, v in real.items():
    assert v["http"] == 200, f"{slug}: {v['http']}"
    assert f"`{slug}`" in inv, f"inventory missing skills.sh slug {slug}"
    assert v["url"] in inv, f"inventory missing skills.sh url {v['url']}"
packages = rb["clawhub"]["packages"]
assert len(packages) == 13, f"expected 13 clawhub packages, got {len(packages)}"
for slug, v in packages.items():
    assert v["http"] == 200, f"{slug}: {v['http']}"
    assert f"`{slug}`" in inv, f"inventory missing clawhub slug {slug}"
    assert v["page_url"] in inv, f"inventory missing clawhub url {v['page_url']}"

# 3. no fabricated registry hosts in the new artifacts
allowed_hosts = {"www.skills.sh", "skills.sh", "clawhub.ai", "github.com"}
for name, text in (("inventory", inv), ("sync", sync)):
    for m in re.finditer(r"https?://([^/\s)`]+)", text):
        assert m.group(1) in allowed_hosts, f"{name}: unexpected host {m.group(1)}"

# 4. relative markdown links and backticked repo paths resolve
for name, text in (("inventory", inv), ("sync", sync)):
    for m in re.finditer(r"\(([^)]+\.(?:md|json))\)", text):
        rel = m.group(1)
        if rel.startswith("http"):
            continue
        assert (root / rel).exists(), f"{name}: broken relative link {rel}"
    for m in re.finditer(r"`((?:references|docs|tests|scripts|skills)/[^`]+\.(?:md|json|sh))`", text):
        assert (root / m.group(1)).exists(), f"{name}: broken reference path {m.group(1)}"

# 5. the referenced artifacts exist
for rel in (
    "references/registry-inventory-2026-10-07.md",
    "references/registry-sync-2026-10-07.md",
    "references/registry-readback-2026-10-07.json",
):
    assert (root / rel).is_file(), f"missing {rel}"

# 6. registry counts must be labelled external signals, not users
assert "external display signals" in inv
assert "external display signals" in sync
assert "real users or API callers" in sync or "not users" in sync

print("registry link and evidence-consistency checks passed")
PY
