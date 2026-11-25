# /rigstrategy — Orchestrator Architecture (IMPLEMENTED 2026-11-24; supersedes the 2026-11-23 DRAFT)

Status: built and verified locally. Mike-confirmation of the original DRAFT design is on record
as approved-as-drafted (gold set relay, conductor cFR6tOtuaCNqap8m, 2026-11-23 23:29 MT).
The DRAFT is preserved at ARCHITECTURE-2026-11-23-DRAFT.md.

## What exists now (evidence, not plan)

- **L0 Command:** `/rigstrategy` is a registered layer-1 meta on the Aside skill surface
  (meta #67 of 83; owner iris-strategy; `skill-surface where rigstrategy` resolves;
  hosted route PASS 1.00, decision 341156; route eval 100/115 = 0.87 with no ask-theft
  from `/strategy`). SKILL.md generated per /repotoskill from this repo.
- **L1 Orchestrator:** `strategy-studio route --json` (deterministic scoring.py router;
  no LLM in the routing path) + hash-chained audit log. Both CLIs live:
  `strategy-route` (12-archetype legacy, batch/playbooks/records/jev_head) and
  `strategy-studio` (route/explain/worksheet/methods/eval/audit).
- **L2 Metaskills (10):** rs-frame, rs-diagnose, rs-options, rs-numbers, rs-stress,
  rs-commit, rs-operate, rs-visual-quality, rs-antipattern, rs-learn.
- **L3 Step skills (110):** 11 methods x 10 stages, all filed as layer-3 subs under their
  stage metaskill; each with a compiled `.workflow.js` (skilltoworkflow check 110/110 ok).
- **Agents (6):** framer, analyst, red-teamer, numbers-checker, visual-judge,
  goldfish-verifier (zero-context).
- **Hooks (4):** pre-route-redact, post-route-audit, pre-done-jev, post-run-learn.
- **Loops (3):** corpus-refresh, eval, improve. Harness: rs-harness. Meta-harness:
  rs-meta-harness (Pareto search over step-skill prompts on a fixed eval set).
- **Skills-for-architects patterns applied:** single owner per concern (rs-* under
  rigstrategy, strat-* under strategy; rigstrategy wraps /strategy, never forks it),
  authority map (OWNERS: iris-strategy), skill vs tool vs record boundary (skills in the
  Aside surface; the deterministic router in this repo; corpus records as URL+hash+license).

## Corpus ("what good / bad looks like")

- Scraped (Wikimedia Commons, URL+hash+license only): **1326 good candidates /
  881 bad candidates** — count targets met (1000 / 300). Bad rows each carry the
  antipattern they illustrate.
- Rendered (RIG's own SVG->PNG set): 1801 images.
- Jev-image verification (hosted, rubric well_designed | poorly_designed | photo):
  bad **316 confirmed** (target met); good **379 scraped + 527 rendered = 906 confirmed**,
  background verification of the remainder in progress 2026-11-24
  (rigstrategy/verify_gate.py; 429-backoff; purges zero-byte cached downloads, the failure
  that silently nulled the first pass). A 40-image gold set carries Mike-approved labels.
- Gate: rs-agent-visual-judge + rs-loop-corpus-refresh-loop re-verify on refresh.

## Verification receipts (2026-11-24)

- `make verify`: 151 pytest passed; 110/110 workflows; corpus counts OK; surface resolves.
- Commits: ee56093 (skill tree 136 + harvester), 5c1a65e (110 workflows + corpus verifier),
  6537977 (gate verifier + gold set + verified indexes), e9be778 (cli.py merge),
  d5c7356 (recovery of batch/integration/metadata/playbooks/records + expanded router
  from stash 20cfd44 — main's cli.py imported modules that existed only in that stash),
  plus the origin/main CI merge. 151 tests green after recovery.
- Held: `git push origin main` is BLOCKED by rig-github-steward
  (`public_push_grant_missing`) — a public push needs Mike's approval artifact; none
  self-minted. Local main carries the full build.

## Non-goals (unchanged)

No outward publishing, no LLM in the routing path, no copyrighted images redistributed
(URL + hash + license only).

## Done-test

`make verify` (Makefile): pytest green w/o PYTHONPATH; 110/110 skilltoworkflow checks;
corpus good>=1000 bad>=300; `skill-surface where rigstrategy` resolves. Jev done.claim
gates the delivery report.
