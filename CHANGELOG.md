# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
