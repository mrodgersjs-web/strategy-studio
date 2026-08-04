# Architecture — Strategy Studio

## One-liner
Deterministic strategy routing with gated decision records

## Flow
```text
input → feature vector → route table → decision record → gate
```

## Trust boundaries
- Public inputs only in examples/fixtures
- Secrets never enter the repo
- Completion claims require smoke/proof

## Related
- Profile: https://github.com/mrodgersjs-web
- Doctrine: https://github.com/mrodgersjs-web/doctrine
- Proof entry: https://github.com/mrodgersjs-web/proof-studio
