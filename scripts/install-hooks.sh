#!/usr/bin/env bash
# Install the kernel-driver pre-commit hook into .git/hooks/
# Usage: bash scripts/install-hooks.sh

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_DST="$REPO_ROOT/.git/hooks/pre-commit"
HOOK_SRC="$REPO_ROOT/scripts/pre-commit.hook"

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
echo "✓ pre-commit hook installed at $HOOK_DST"
