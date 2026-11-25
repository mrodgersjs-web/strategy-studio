# /rigstrategy - Orchestrator Architecture (IMPLEMENTED 2026-11-24; supersedes the 2026-11-23 DRAFT)

Status: built, optimized, and verified locally. Mike-confirmation of the original DRAFT design
is on record (gold set approved-as-drafted 2026-11-23 23:29 MT). The original draft is preserved
at `blueprints/rigstrategy/ARCHITECTURE-2026-11-23-DRAFT.md`.

## What exists now (evidence, not plan)

- **L0 Command:** `/rigstrategy` is a registered layer-1 meta on the Aside skill surface
  (meta #67 of 83; owner `iris-strategy`; `skill-surface where rigstrategy` resolves;
  hosted route PASS 1.00, decision 341156; route eval 100/115 = 0.87 with no ask-theft
  from `/strategy`). Generated per `/repotoskill` from this repo via `rigstrategy/gen.py`.
- **L1 Orchestrator:** `strategy-studio route --json` (deterministic `scoring.py` router;
  no LLM in the routing path) + hash-chained audit log, wired through `rigstrategy/harness.py`.
  Both CLIs live: `strategy-route` (12-archetype legacy) and `strategy-studio`
  (route/explain/worksheet/methods/eval/audit).
- **L2 Metaskills (10):** `rs-frame`, `rs-diagnose`, `rs-options`, `rs-numbers`, `rs-stress`,
  `rs-commit`, `rs-operate`, `rs-visual-quality`, `rs-antipattern`, `rs-learn`.
- **L3 Step skills (110):** 11 methods x 10 stages in `~/.aside/u/0/skill-library/rs-*/SKILL.md`,
  each populated with real method summaries, gates, worksheet fields from `methods.json`, and
  `/strategy` doctrine links (`method-step-map.json`). Every step has a compiled `.workflow.js`
  (`skilltoworkflow check`: 110/110 pass).
- **Skill optimization (`/skilloptimizer`):** All 136 skills pass `skillopt_eval.py`
  (136/136 PASS, 0 soft words, 0 runtime warnings, mean description >= 14/15, mean SkillLens
  static proxy >= 57/64), audited via `rigstrategy/meta_harness.py`.
- **Agents (6):** `framer`, `analyst`, `red-teamer`, `numbers-checker`, `visual-judge`,
  `goldfish-verifier` (zero-context).
- **Hooks (4, executable in `rigstrategy/hooks/`):**
  - `pre-route-redact.sh` (redacts emails, keys, SSNs, home paths; fails closed on empty)
  - `post-route-audit.sh` (verifies routed JSON and hash-chained audit log)
  - `pre-done-jev.sh` (gates claims via hosted `rig-s1gate` with required subject hash; DEFERRED if down)
  - `post-run-learn.sh` (appends immutable JSONL receipts to `rigstrategy/run-ledger.jsonl`)
- **Loops (3):** `corpus-refresh-loop`, `eval-loop`, `improve-loop`.
- **Harness & Meta-harness:** `rigstrategy/harness.py` (`rs-harness`) and
  `rigstrategy/meta_harness.py` (`rs-meta-harness`).
- **Skills-for-architects patterns applied:** single owner per concern (`rs-*` under
  `rigstrategy`, `strat-*` under `strategy`; `rigstrategy` wraps `/strategy`, never forks it),
  authority map (owner `iris-strategy`), skill vs tool vs record boundary (skills in Aside
  surface; deterministic router + hooks in this repo; records in `.strategy-studio/audit.jsonl`
  and `corpus/MANIFEST.json`).

## Corpus ("what good / bad looks like")

- Scraped (Wikimedia Commons, URL+hash+license only): **1,326 good candidates /
  881 bad candidates** (targets 1,000 / 300 met). Bad rows each tag the antipattern illustrated.
- Rendered (RIG-owned matplotlib diagrams): **1,800 images** (1,400 good + 400 bad).
- Jev-image verification (hosted `jev-image`):
  - **Calibrated v1 rubric** (Mike-approved 40-item gold set 40/40, 60/60 holdout):
    **1,597 verified good** (1,400 rendered + 197 Commons) and **551 verified bad**
    (400 rendered + 151 Commons). Both targets (1,000 good / 300 bad) exceeded.
  - **Strict v0 rubric** (retained in `corpus/MANIFEST.json`): 380 Commons good + 527 rendered
    good, 355 Commons bad + 873 rendered bad.

## Non-goals (unchanged)

No outward publishing, no LLM in the routing path, no copyrighted images redistributed
(URL + hash + license only).

## Done-test

`make verify` (Makefile): pytest green without `PYTHONPATH`; 4/4 hooks executable; 110/110
`skilltoworkflow check`; 136/136 `skillopt_eval.py` via `meta_harness.py`; corpus gate green
(harvested and v1 calibrated); `skill-surface where rigstrategy` resolves. Jev `done.claim`
gates the delivery report.
