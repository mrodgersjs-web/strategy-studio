# strategy-studio

[![CI](https://img.shields.io/github/actions/workflow/status/mrodgersjs-web/strategy-studio/smoke.yml?branch=main)](https://github.com/mrodgersjs-web/strategy-studio/actions/workflows/smoke.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

> Deterministic strategy routing: a business question goes in, a named strategy method comes out, with a scored explanation, an audit log entry and a worksheet.

**Outcome:** `bash scripts/smoke.sh` routes six sample questions to six different methods, checks the hash-chained audit log, and runs the accuracy gates on a labelled set and a held-out set.

## What it does

Given a question such as *"Are we profitable per customer once you count acquisition cost?"*, `strategy-studio`:

1. Scores the question against every method in [`src/strategy_studio/data/methods.json`](src/strategy_studio/data/methods.json) (keyword phrases with weights; no LLM, no network).
2. Picks the winner by score, then priority, then id, so the same question always gets the same answer.
3. Explains the choice: matched phrases, score, margin over the runner-up, and a confidence label (`clear`, `narrow`, `tie-break`, `fallback`).
4. Appends a hash-chained entry to a JSONL audit log (question hash, all scores, runner-up, methods-file version).
5. Emits a structured worksheet for the chosen method, with a calculator for unit economics and expected value.

Methods shipped as data:

| id | Method |
| --- | --- |
| `future-back` | Future-back planning |
| `ten-types` | Ten Types of Innovation |
| `jobs-to-be-done` | Jobs to be done |
| `pre-mortem` | Pre-mortem |
| `wardley-mapping` | Wardley-style mapping |
| `unit-economics` | Unit economics (with calculator) |
| `build-vs-buy` | Build vs buy |
| `reference-class-forecast` | Reference-class forecast |
| `real-options` | Real options portfolio (with expected-value calculator) |
| `org-design` | Org design |
| `frame-problem` | Problem framing (fallback when nothing matches) |

Add or tune a method by editing the JSON; `strategy-studio --methods my.json ...` loads a custom file.

## Quick start

```bash
git clone https://github.com/mrodgersjs-web/strategy-studio.git
cd strategy-studio
python3 -m pip install -e ".[test]"
bash scripts/smoke.sh
```

## CLI

```bash
strategy-studio route "We launch the new billing system next month. What could go wrong?"
#   Pre-mortem [pre-mortem] score=8 confidence=clear
#   Pre-mortem scored 8 from 'what could go wrong' (+5), 'launch' (+3). No other method matched any keyword.
#   audit: .strategy-studio/audit.jsonl #1

strategy-studio explain "Should we build or buy, and what could go wrong?"   # why every other method lost
strategy-studio worksheet "Are we profitable per customer?" \
  --set revenue_per_unit=40 --set variable_cost_per_unit=25 --set cac=120 --set retention=18
strategy-studio worksheet "..." --method pre-mortem --markdown              # force a method
strategy-studio audit verify                                                # recompute hashes and links
strategy-studio audit show
strategy-studio methods
strategy-studio eval --min-accuracy 0.95                                    # labelled (tuning) set
strategy-studio eval --holdout                                              # held-out set
```

All commands take `--json`. `route` takes `--log PATH`, `--no-log` and `--ts` (fixed timestamp for reproducible logs).

The original archetype router is still available as `strategy-route "question"` (A1-A4 cell and gates).

## Accuracy, honestly

- Labelled set (`data/labelled_questions.jsonl`, 47 hand-written questions): 47/47. The keyword weights were tuned against this set, so it is a regression check, not evidence of generalisation.
- Held-out set (`data/holdout_questions.jsonl`, 22 questions written after the last weight change and not used for tuning): 20/22 on first measurement. Tests fail below 0.85.
- It is a keyword router. Questions phrased without any of a method's vocabulary fall back to `frame-problem` or land on the wrong method. `explain` shows exactly which phrases drove the choice.

## Architecture

```text
question -> score all methods (data/methods.json) -> rank -> decision + explanation
         -> audit entry (hash chain) -> worksheet (+ calculator)
```

Details: [docs/routing-model.md](docs/routing-model.md), [docs/architecture.md](docs/architecture.md).

## Public boundary

See [docs/public-boundary.md](docs/public-boundary.md). Sample questions are synthetic.

## Roadmap

- Routing beyond keywords (for example a small embedding or classifier stage) gated on the held-out accuracy check.
- Gate checking: today worksheet gates are listed with `passed: false`; nothing marks them passed yet.
- Decision records that link a filled worksheet back to its audit entry.

## Related

[fde-portfolio](https://github.com/mrodgersjs-web/fde-portfolio) · [doctrine](https://github.com/mrodgersjs-web/doctrine)

## Video walkthrough

- Script: [`docs/video-script.md`](docs/video-script.md)
- Recording: [`assets/demo.mp4`](assets/demo.mp4) (75s captioned; recorded against the earlier archetype router)
- Preview: [`docs/strategy-studio-demo.gif`](docs/strategy-studio-demo.gif)

![demo preview](docs/strategy-studio-demo.gif)

## Practices in this repo

| Practice | Here |
| --- | --- |
| Smoke proof | `bash scripts/smoke.sh` (also runs in CI) |
| Tests | `pytest -q` |
| Lint | `ruff check .` |
| Public boundary | `docs/public-boundary.md` |
| Claim under test | same question -> same method, logged and verifiable |
| Fleet | [profile](https://github.com/mrodgersjs-web) · [resume](https://github.com/mrodgersjs-web/resume) · [patents](https://github.com/mrodgersjs-web/patents) |

If `scripts/smoke.sh` fails, treat README claims as false until fixed.

---

Built by Mike Rodgers · [rodgersintelligence.com](https://rodgersintelligence.com/)
