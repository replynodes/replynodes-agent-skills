#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
validator="$root/scripts/validate-package.sh"

"$validator" "$root"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

tar -C "$root" --exclude=.git --exclude='*.swp' -cf - . | tar -C "$tmp" -xf -
"$validator" "$tmp"
cmp "$root/SKILL.md" "$tmp/SKILL.md"
cmp "$root/references/live-capability-routing.md" "$tmp/references/live-capability-routing.md"
cmp "$root/references/research-workflows.md" "$tmp/references/research-workflows.md"

# The official Agent Skills validator is run separately because it expects the
# skill directory itself to be named `replynodes`; this repository is the source
# repository and intentionally has a different directory name.

echo 'deterministic package and archive tests passed'
