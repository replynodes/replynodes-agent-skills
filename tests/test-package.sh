#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
validator="$root/scripts/validate-package.sh"

"$validator" "$root"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
tar -C "$root" --exclude=.git --exclude='*.swp' -cf - . | tar -C "$tmp" -xf -
"$validator" "$tmp"

cp -R "$root/tests/fixtures/invalid-layout" "$tmp/invalid-layout"
if "$validator" "$tmp/invalid-layout" >/dev/null 2>&1; then
  echo 'expected invalid layout fixture to fail' >&2
  exit 1
fi

cp -R "$root/tests/fixtures/injected-secret" "$tmp/injected-secret"
if "$validator" "$tmp/injected-secret" >/dev/null 2>&1; then
  echo 'expected injected secret fixture to fail' >&2
  exit 1
fi

echo 'deterministic package, archive, and negative-fixture tests passed'
