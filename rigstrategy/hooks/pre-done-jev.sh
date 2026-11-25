#!/usr/bin/env bash
# Pre-done Jev quality gate hook for /rigstrategy.
# Requires --subject <kind:id@sha12> and --text <claim> (or --file <path>).
# Calls hosted rig-s1gate; fails closed (DEFERRED/BLOCK) if unreachable. Never self-certifies.
set -euo pipefail

GATE=""
for cand in "$HOME/Developer/rig-capabilities/bin/rig-s1gate" "$HOME/.rig/bin/rig-s1gate"; do
  if [ -x "$cand" ]; then
    GATE="$cand"
    break
  fi
done

if [ -z "$GATE" ]; then
  echo '{"verdict":"DEFERRED","reason":"rig-s1gate CLI not found"}' >&2
  exit 2
fi

SUBJECT=""
TEXT=""
FILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --subject) SUBJECT="${2:-}"; shift 2 ;;
    --text) TEXT="${2:-}"; shift 2 ;;
    --file) FILE="${2:-}"; shift 2 ;;
    *) echo "pre-done-jev: unknown arg $1" >&2; exit 3 ;;
  esac
done

if [ -z "$SUBJECT" ]; then
  echo '{"verdict":"BLOCK","reason":"--subject kind:id@sha12 is required"}' >&2
  exit 3
fi

if [ -n "$FILE" ]; then
  exec "$GATE" check done.claim --file "$FILE" --subject "$SUBJECT" --json
elif [ -n "$TEXT" ]; then
  exec "$GATE" check done.claim --text "$TEXT" --subject "$SUBJECT" --json
else
  echo '{"verdict":"BLOCK","reason":"--text or --file is required"}' >&2
  exit 3
fi
