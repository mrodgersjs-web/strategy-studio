#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m pip install -e ".[test]" -q
pytest -q
strategy-route --json "Should we build or buy an eval harness?"
echo "strategy-studio smoke PASS"
