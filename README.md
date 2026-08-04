# strategy-studio

> Deterministic strategy routing — map a question to a bounded cell and gates before agents improvise.

![status](https://img.shields.io/badge/status-public-studio-blue)

## Employer summary

FDE judgment as **routing, not vibes**. Classify the question, select a cell, list gates, emit a decision record. Deep client cell packs stay private; this public surface is the router.

## Proof in 60 seconds

```bash
git clone https://github.com/mrodgersjs-web/strategy-studio.git
cd strategy-studio
python3 -m pip install -e ".[test]"
pytest -q
strategy-route --json "Should we build or buy an eval harness?"
```

Expected: archetype `A2`, cell `cell.build-vs-buy`, non-empty gates.

## Architecture

```text
question → archetype (A1–A4) → cell id → gates → decision record
```

## Public boundary
See [docs/public-boundary.md](docs/public-boundary.md).

## Related
- [fde-portfolio](https://github.com/mrodgersjs-web/fde-portfolio) · [doctrine](https://github.com/mrodgersjs-web/doctrine) · [jake-studio](https://github.com/mrodgersjs-web/jake-studio)
