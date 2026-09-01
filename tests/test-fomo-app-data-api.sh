#!/usr/bin/env bash
set -euo pipefail
repo="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
validator="$repo/scripts/validate-fomo-app-data-api.sh"
"$validator" "$repo/skills/fomo-app-data-api"

archive_root="$(mktemp -d /home/hermes/worktrees/fomo-archive.XXXXXX)"
install_root="$(mktemp -d /home/hermes/worktrees/fomo-extract.XXXXXX)"
trap 'rm -rf "$archive_root" "$install_root"' EXIT
tree="$(git -C "$repo" write-tree)"
git -C "$repo" archive --format=tar --prefix=fomo-app-data-api/ "$tree" -- skills/fomo-app-data-api | tar -C "$archive_root" -xf -
"$validator" "$archive_root/fomo-app-data-api/skills/fomo-app-data-api"
tar -C "$archive_root/fomo-app-data-api/skills/fomo-app-data-api" -cf - . | tar -C "$install_root" -xf -
"$validator" "$install_root"
echo 'deterministic FOMO archive and extracted-package tests passed'
