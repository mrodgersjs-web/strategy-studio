#!/usr/bin/env bash
# Post-run learning ledger hook for /rigstrategy.
# Appends a structured run record (method, stage, audit_hash, jev_verdict, note)
# to rigstrategy/run-ledger.jsonl (gitignored) for improve-loop and meta-harness.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LEDGER="${RIGSTRATEGY_LEDGER:-$ROOT/rigstrategy/run-ledger.jsonl}"
METHOD="${1:-}"
STAGE="${2:-all}"
AUDIT_HASH="${3:-}"
JEV_VERDICT="${4:-DEFERRED}"
NOTE="${5:-}"

if [ -z "$METHOD" ] || [ -z "$AUDIT_HASH" ]; then
  echo "usage: post-run-learn.sh <method> <stage> <audit_hash> [jev_verdict] [note]" >&2
  exit 2
fi

python3 - "$LEDGER" "$METHOD" "$STAGE" "$AUDIT_HASH" "$JEV_VERDICT" "$NOTE" <<'PY'
import datetime, json, pathlib, sys
ledger, method, stage, ahash, verdict, note = sys.argv[1:7]
rec = {
    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "method": method,
    "stage": stage,
    "audit_hash": ahash,
    "jev_verdict": verdict,
    "note": note,
}
p = pathlib.Path(ledger)
p.parent.mkdir(parents=True, exist_ok=True)
with p.open("a", encoding="utf-8") as f:
    f.write(json.dumps(rec) + "\n")
print(json.dumps(rec))
PY
