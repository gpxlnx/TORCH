#!/usr/bin/env bash
# Resolve the Caido driver once: native MCP, SDK fallback, or unavailable.
set -uo pipefail

VAULT="${VAULT:-$(cd "$(dirname "$0")/../.." && pwd)}"
CAIDO_SH="${CAIDO_SH:-$VAULT/scripts/caido/caido-client.sh}"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

if [ "${CAIDO_NATIVE:-}" = "1" ]; then
  echo native
  echo "caido-transport: native mcp__caido__* tools are available; use them directly." >&2
  exit 0
fi

if [ "$DRY" = 1 ]; then
  echo down
  echo "caido-transport(--dry-run): native not flagged and the SDK probe was skipped." >&2
  exit 3
fi

if bash "$CAIDO_SH" health >/dev/null 2>&1; then
  echo sdk
  echo "caido-transport: native MCP absent; the Caido SDK client is healthy." >&2
  exit 0
fi

echo down
cat >&2 <<'MSG'
caido-transport: Caido is unavailable through both native MCP and the SDK client.
Recovery:
  1) start Caido on Kali and keep its API bound to loopback,
  2) establish the SSH local-forward documented in setup/caido/README.md,
  3) run caido-client.sh setup <PAT> http://127.0.0.1:8080, and
  4) restart the Claude session if the native MCP was added after session start.
MSG
exit 3
