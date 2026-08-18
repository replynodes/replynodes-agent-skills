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
if output="$("$validator" "$tmp/invalid-layout" 2>&1)"; then
  echo 'expected invalid layout fixture to fail' >&2
  exit 1
else
  status=$?
fi
[[ "$status" -eq 1 ]] || { echo "invalid layout fixture exited $status" >&2; exit 1; }
grep -F 'validation failed: unexpected package path: extra.txt' <<<"$output" >/dev/null || {
  echo "invalid layout fixture failed for an unexpected reason: $output" >&2
  exit 1
}

cp -R "$root/tests/fixtures/injected-secret" "$tmp/injected-secret"
if output="$("$validator" "$tmp/injected-secret" 2>&1)"; then
  echo 'expected injected secret fixture to fail' >&2
  exit 1
else
  status=$?
fi
[[ "$status" -eq 1 ]] || { echo "injected secret fixture exited $status" >&2; exit 1; }
grep -F 'validation failed: credential-like value found' <<<"$output" >/dev/null || {
  echo "injected secret fixture failed for an unexpected reason: $output" >&2
  exit 1
}

echo 'deterministic package, archive, and negative-fixture tests passed'
