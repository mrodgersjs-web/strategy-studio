# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.1] - 2026-10-19

### Added

- `.github/CODEOWNERS` assigning `*` to `@mrodgersjs-web`.
- `.github/copilot-instructions.md` (2294 bytes): what the repository is, the
  layout, the exact commands (`pip install -e '.[dev]'`, `ruff check .`,
  `pytest -q`, `pytest -q --cov=strategy_studio`, `bash scripts/smoke.sh`),
  conventions (conventional commits, a test for every change, labelled and
  held-out sets kept apart, no secrets, no machine paths) and the truth rule that
  every number in docs comes from a command run in this repository.
- `tests/test_repo_hygiene.py`: 4 checks read from the files on disk that
  `.github/CODEOWNERS` assigns `*` to `@mrodgersjs-web`, that
  `.github/copilot-instructions.md` is non-empty, at most 8000 bytes and names a
  test command, that `README.md` carries a `github/actions/workflow/status` badge,
  the "Built by Mike Rodgers - rodgersintelligence.com" footer, a test command and
  only clones `mrodgersjs-web/strategy-studio`, and that every job under
  `.github/workflows/` sets `timeout-minutes` and never sets `continue-on-error: true`.

### Changed

- `.github/workflows/smoke.yml` and `.github/workflows/rig-lattice.yml`:
  `timeout-minutes: 15` on every job.
- `README.md`: footer is the plain literal "Built by Mike Rodgers -
  rodgersintelligence.com".

### Verified

- Fresh venv `python3.12 -m venv`, `pip install -e '.[dev]'`, `ruff check .` clean,
  `pytest -q --cov=strategy_studio` 51 passed with 89 percent coverage (47 before
  the hygiene tests), `bash scripts/smoke.sh` ends with "strategy-studio smoke PASS".

## [0.3.0] - 2026-10-19

### Added
- CHANGELOG for the project, including the first release below.
- Code of conduct (Contributor Covenant 2.1), issue templates, pull request
  template, and Dependabot config.
- `tests/test_docs.py`: the README's accuracy numbers (47 labelled, 22
  held-out, 20/22 measured) are checked against the data files, and the
  changelog version against the package metadata.

### Changed
- Packaging metadata completed: authors, classifiers, project URLs, and a dev
  extra with pytest-cov. Version 0.2.0 to 0.3.0.
- CI matrix extended to Python 3.10-3.13 and now reports test coverage.
- Security policy gains supported versions and the security contact.

## [0.2.0] - 2026-10-10

### Added
- Data-driven method router: 11 named strategy methods in
  `data/methods.json`, keyword-weight scoring, deterministic tie-breaking,
  and a scored explanation with a confidence label.
- Hash-chained JSONL audit log with `audit verify` and `audit show`.
- Worksheets with unit-economics and expected-value calculators.
- `eval` accuracy gates on a labelled tuning set (47 questions) and a
  held-out set (22 questions) written after the last weight change.

## [0.1.0] - 2026-08-04

### Added
- First public release: the archetype router (A1-A4 cells and gates),
  runnable smokes, and the studio surface.
