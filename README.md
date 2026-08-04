# strategy-studio

> Deterministic strategy routing — question → archetype → cell → gates.

## Employer summary
FDE judgment as routing, not vibes. Deep client packs stay private; this surface is the router.

## Proof in 60 seconds
```bash
git clone https://github.com/mrodgersjs-web/strategy-studio.git
cd strategy-studio
python3 -m pip install -e ".[test]"
bash scripts/smoke.sh
```

## Architecture
```text
question → A1–A4 archetype → cell id → gates → decision record
```

## Public boundary
See [docs/public-boundary.md](docs/public-boundary.md).

## Related
[fde-portfolio](https://github.com/mrodgersjs-web/fde-portfolio) · [doctrine](https://github.com/mrodgersjs-web/doctrine)


---

## FDE bar (this studio)

| Practice | Here |
| --- | --- |
| Employer summary | top of README |
| Smoke proof | `bash scripts/smoke.sh` |
| Public boundary | `docs/public-boundary.md` |
| Claim under test | strategy-route deterministic |
| Fleet | [profile](https://github.com/mrodgersjs-web) · [resume](https://github.com/mrodgersjs-web/resume) · [patents](https://github.com/mrodgersjs-web/patents) |

If `scripts/smoke.sh` fails, treat README claims as false until fixed.
