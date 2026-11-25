#!/usr/bin/env bash
# Post-route audit verification hook for /rigstrategy.
# Reads routed JSON from $1 (file path) or stdin and verifies both payload fields
# and the strategy-studio hash-chained audit log. Non-zero blocks.
set -euo pipefail

if [ $# -ge 1 ] && [ -f "$1" ]; then
  PAYLOAD="$(cat "$1")"
else
  PAYLOAD="$(cat || true)"
fi

python3 - "$PAYLOAD" <<'PY'
import json, sys, io, contextlib
from strategy_studio.cli import studio

raw = sys.argv[1]
try:
    data = json.loads(raw)
except Exception as exc:
    print(f"post-route-audit: BLOCK invalid JSON ({exc})", file=sys.stderr)
    sys.exit(1)

for key in ("method", "score", "audit"):
    if key not in data:
        print(f"post-route-audit: BLOCK missing required key '{key}'", file=sys.stderr)
        sys.exit(1)

audit = data.get("audit") or {}
log_path = audit.get("log")
if not log_path or not audit.get("hash"):
    print("post-route-audit: BLOCK missing audit log path or hash", file=sys.stderr)
    sys.exit(1)

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = studio(["audit", "verify", "--log", log_path, "--json"])

if rc != 0:
    print(f"post-route-audit: BLOCK audit verify failed (rc={rc})", file=sys.stderr)
    sys.exit(1)

res = json.loads(buf.getvalue())
if not res.get("ok"):
    print(f"post-route-audit: BLOCK audit chain broken: {res}", file=sys.stderr)
    sys.exit(1)

print(json.dumps({"ok": True, "method": data["method"], "audit_hash": audit["hash"], "entries": res.get("entries")}))
PY
