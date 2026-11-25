#!/usr/bin/env bash
# End-to-end smoke: route real sample questions, check the audit log, check accuracy.
# Assumes the package is installed (pip install -e ".[test]").
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LOG="$(mktemp -d)/audit.jsonl"

# Legacy archetype router still answers.
strategy-route --json "Should we build or buy an eval harness?" | grep -q '"archetype": "A2"'

n=0
while IFS= read -r q; do
  [ -z "$q" ] && continue
  strategy-studio route "$q" --log "$LOG"
  n=$((n + 1))
done < examples/sample-questions.txt

entries=$(wc -l < "$LOG" | tr -d ' ')
[ "$entries" -eq "$n" ] || { echo "expected $n audit entries, got $entries"; exit 1; }
strategy-studio audit verify --log "$LOG"

# Each sample question must land on its intended method.
expected="build-vs-buy future-back jobs-to-be-done pre-mortem wardley-mapping unit-economics"
got=$(python3 -c 'import json,sys; print(" ".join(json.loads(l)["method"] for l in open(sys.argv[1])))' "$LOG")
[ "$got" = "$expected" ] || { echo "routing mismatch: got [$got] expected [$expected]"; exit 1; }

strategy-studio explain "Should we build or buy, and what could go wrong?"
strategy-studio worksheet "Are we profitable per customer?" \
  --set revenue_per_unit=40 --set variable_cost_per_unit=25 --set cac=120 --set retention=18 --json \
  | grep -q '"ltv_to_cac": 2.25'
strategy-studio eval --min-accuracy 0.95
strategy-studio eval --holdout --min-accuracy 0.85
echo "strategy-studio smoke PASS"
