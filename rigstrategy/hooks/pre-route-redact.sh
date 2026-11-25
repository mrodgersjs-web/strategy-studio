#!/usr/bin/env bash
# Pre-route redaction hook for /rigstrategy.
# Reads question text from $1 or stdin, redacts emails/keys/SSNs/local home paths,
# and fails closed (exit 1) if input is empty or unredacted secrets remain.
set -euo pipefail

if [ $# -ge 1 ] && [ -n "${1}" ]; then
  INPUT="$1"
else
  INPUT="$(cat || true)"
fi

python3 - "$INPUT" <<'PY'
import re, sys

text = sys.argv[1] if len(sys.argv) > 1 else ""
if not text.strip():
    print("pre-route-redact: BLOCK empty question", file=sys.stderr)
    sys.exit(1)

patterns = [
    (r"\b(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35})\b", "[REDACTED_SECRET]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
    (r"/Users/[A-Za-z0-9._-]+/", "[REDACTED_HOME]/"),
]

redacted = text
for pat, repl in patterns:
    redacted = re.sub(pat, repl, redacted)

for pat, _ in patterns:
    if re.search(pat, redacted):
        print("pre-route-redact: BLOCK residual sensitive pattern after redaction", file=sys.stderr)
        sys.exit(1)

print(redacted)
PY
