#!/usr/bin/env bash
# Stable TORCH entrypoint for the device-local caido-mode SDK client.
set -euo pipefail

CLIENT="${CAIDO_CLIENT:-}"
if [ -z "$CLIENT" ]; then
  for candidate in \
    "$HOME/.agents/skills/caido-mode/caido-client.ts" \
    "$HOME/.claude/skills/caido-mode/caido-client.ts" \
    "$HOME/.codex/skills/caido-mode/caido-client.ts"; do
    if [ -f "$candidate" ]; then CLIENT="$candidate"; break; fi
  done
fi

[ -f "$CLIENT" ] || {
  echo "caido-client: caido-mode is not installed; set CAIDO_CLIENT to caido-client.ts" >&2
  exit 2
}

TSX="${CAIDO_TSX:-$(dirname "$CLIENT")/node_modules/.bin/tsx}"
if [ ! -x "$TSX" ]; then
  TSX=$(command -v tsx 2>/dev/null || true)
fi
[ -x "$TSX" ] || {
  echo "caido-client: tsx missing next to $CLIENT; install the caido-mode dependencies" >&2
  exit 2
}

exec "$TSX" "$CLIENT" "$@"
