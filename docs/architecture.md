# Architecture - Strategy Studio

## One-liner
Deterministic routing of a business question to a named strategy method, with a scored
explanation, an audit log and a worksheet.

## Modules
| Module | Role |
| --- | --- |
| `data/methods.json` | method definitions: keywords and weights, priority, gates, worksheet fields |
| `methods.py` | load + validate the methods file; version hash |
| `scoring.py` | keyword scoring, ranking, decision, loser explanations |
| `audit.py` | append-only hash-chained JSONL log; verify |
| `worksheet.py` | worksheet builder, markdown render, unit-economics and expected-value calculators |
| `evaluate.py` | accuracy on labelled question sets |
| `cli.py` | `strategy-studio` (new) and `strategy-route` (legacy) |
| `router.py` | legacy A1-A4 archetype router |

## Trust boundaries
- Public inputs only in examples and fixtures
- Secrets never enter the repo
- No network calls and no LLM in the routing path
