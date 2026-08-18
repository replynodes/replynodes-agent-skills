#!/usr/bin/env bash
set -euo pipefail
"$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/scripts/validate-package.sh"
echo 'deterministic package test passed'
