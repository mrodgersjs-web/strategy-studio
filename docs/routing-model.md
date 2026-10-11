# Routing model

```text
question
  -> normalize (lowercase, collapse spaces)
  -> score every method in data/methods.json
       score = sum of weights of matched keyword phrases
       a phrase inside a longer matched phrase does not count twice
       spelling variants ("go live" / "go-live") count once
  -> rank: score desc, then priority asc, then id asc
  -> winner (or the fallback "frame-problem" when every score is 0)
  -> decision: method, score, margin, confidence, explanation
  -> audit entry (hash-chained JSONL)
  -> worksheet for the chosen method (+ calculator where defined)
```

Confidence labels:

| Label | Rule |
| --- | --- |
| `clear` | margin over runner-up >= 0.4 of the winner's score |
| `narrow` | margin > 0 and < 0.4 |
| `tie-break` | runner-up has the same score; priority then id decided |
| `fallback` | no keyword matched any method |

Each audit entry records `methods_version` (a hash of the methods file), so a changed
keyword table is visible in the log. `strategy-studio audit verify` recomputes every
entry hash and the `prev` link; an edited or deleted line fails the check.

The legacy archetype router (`strategy-route`, A1-A4 cells in `router.py`) is kept
unchanged for existing callers.
