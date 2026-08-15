#!/usr/bin/env bash
# Send one load-bearing request through a named Caido Replay session and capture it.
set -euo pipefail

VAULT="${VAULT:-$(cd "$(dirname "$0")/../.." && pwd)}"
CAIDO_SH="${CAIDO_SH:-$VAULT/scripts/caido/caido-client.sh}"
[ $# -ge 7 ] || {
  echo "usage: caido-hunt.sh <eng> <slug> <host> <port> <https> <method> <path> [bodyfile-local] [highlight-regex]" >&2
  exit 2
}

ENG=$1; SLUG=$2; HOST=$3; PORT=$4; HTTPS=$5; METHOD=$6; RPATH=$7
BODYFILE=${8:-}; HIGHLIGHT=${9:-}
REQUEST_FILE=$(mktemp)
RESULT_FILE=$(mktemp)
trap 'rm -f "$REQUEST_FILE" "$RESULT_FILE"' EXIT

if [ -n "$BODYFILE" ] && [ ! -f "$BODYFILE" ]; then
  echo "caido-hunt: body file does not exist: $BODYFILE" >&2
  exit 2
fi

{
  printf '%s %s HTTP/1.1\r\n' "$METHOD" "$RPATH"
  printf 'Host: %s\r\nAccept: */*\r\nConnection: close\r\n' "$HOST"
  if [ -n "$BODYFILE" ]; then
    printf 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8\r\n'
    printf 'Content-Length: %s\r\n' "$(wc -c < "$BODYFILE")"
  fi
  printf '\r\n'
  [ -n "$BODYFILE" ] && command cat "$BODYFILE"
} > "$REQUEST_FILE"

python3 "$VAULT/scripts/caido/caido-scope-sync.py" "$ENG" >/dev/null

TLS_FLAG=--no-tls
[ "$HTTPS" = "true" ] && TLS_FLAG=--tls
bash "$CAIDO_SH" send-raw \
  --host "$HOST" --port "$PORT" "$TLS_FLAG" \
  --raw "@$REQUEST_FILE" --name "$SLUG" \
  --max-body 0 --max-body-chars 0 > "$RESULT_FILE"

REQUEST_ID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("requestId", ""))' "$RESULT_FILE")
[ -n "$REQUEST_ID" ] || {
  echo "caido-hunt: send succeeded without a requestId" >&2
  exit 1
}

echo "caido-hunt: Replay '$SLUG' sent as request $REQUEST_ID"
bash "$VAULT/scripts/capture.sh" caido "$ENG" "$SLUG" "$REQUEST_ID" "$HIGHLIGHT"
