# Copilot instructions

## What this repo is

`strategy-studio` is a question router for strategy work: it sends each question
to one of several named methods (disagreement, difference, duplication and
neighbours), keeps a hash-chained audit log of what was asked and answered, and
scores accuracy on a labelled set and a held-out set. The `strategy_studio`
Python package holds the router, the methods catalog, the audit chain, the
scoring gates and a worksheet CLI.

## Layout

- `src/strategy_studio/` - package: `router.py`, `methods.py`, `audit.py`,
  `scoring.py`, `evaluate.py`, `worksheet.py`, `cli.py`.
- `src/strategy_studio/data/` - `methods.json`, `labelled_questions.jsonl`,
  `holdout_questions.jsonl` (the two question sets are kept apart on purpose).
- `tests/` - pytest suite: router, methods, audit chain, scoring gates, CLI,
  docs claims, CI install, repo hygiene.
- `docs/` - architecture, accuracy notes, upstream excerpt, public boundary.
- `examples/` - sample questions and a worked run.
- `scripts/smoke.sh` - routes six sample questions, checks the audit log hash
  chain, and runs the accuracy gates. It runs in CI as well.

## Commands

Run from the repository root in a virtual environment:

```bash
pip install -e '.[dev]'    # installs pytest, pytest-cov, ruff
ruff check .               # lint
pytest -q                  # full test suite
pytest -q --cov=strategy_studio
bash scripts/smoke.sh      # smoke
```

## Conventions

- Conventional commit messages: `feat:`, `fix:`, `test:`, `docs:`, `ci:`, `chore:`.
- Every behavior change lands with a test that exercises it and passes on a clean install.
- The labelled set and the held-out set never mix: a question used for tuning does
  not belong in `holdout_questions.jsonl`.
- No secrets, credentials, client PII or private monorepo content in any tracked
  file. No machine paths such as `/Users/...` or `~/Developer/...`.
- Keep the audit log hash-chained; a change that breaks the chain breaks the point
  of the repository.

## Truth rule

Any number in docs, comments, or commit messages must come from a command run in
this repository, for example a test count from `pytest -q` or an accuracy figure
from `pytest -q tests/test_accuracy.py`. Quote the command and its output rather
than a memory of it.
