#!/usr/bin/env python3
"""Generate and optimize the 136-skill /rigstrategy tree in Aside.

Writes:
  - ~/.aside/u/0/skills/user/rigstrategy/SKILL.md (Layer 1 meta)
  - ~/.aside/u/0/skill-library/rs-*/SKILL.md      (Layer 2 & Layer 3 children)

Preserves existing <!-- skill-surface:BEGIN --> ... <!-- skill-surface:END -->
blocks so Aside's three-layer skill surface stays intact without duplicates.
Every skill embeds:
  - Method-specific gates, summary, worksheet fields from src/strategy_studio/data/methods.json
  - Doctrine wrapper link to /strategy (references/method-step-map.json)
  - S.U.P.E.R. & skills-for-architects governance (single owner, authority map, skill/tool/record boundary)
  - /skilloptimizer hard-gate structure (numbered steps, fallbacks, anti-patterns, Gate-D, exit gate)
"""
from __future__ import annotations

import json
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
META_ROOT = pathlib.Path(os.path.expanduser("~/.aside/u/0/skills/user"))
LIB_ROOT = pathlib.Path(os.path.expanduser("~/.aside/u/0/skill-library"))
STRAT_MAP_PATH = pathlib.Path(os.path.expanduser("~/.aside/u/0/skills/user/strategy/references/method-step-map.json"))

METHODS = json.loads((ROOT / "src/strategy_studio/data/methods.json").read_text(encoding="utf-8"))["methods"]
STRAT_MAP = (
    {r["method"]: r["step"] for r in json.loads(STRAT_MAP_PATH.read_text(encoding="utf-8")).get("map", [])}
    if STRAT_MAP_PATH.exists()
    else {}
)

STAGE_META = {
    "frame": {
        "purpose": "define the decision boundary, non-goals, and concrete outcome before analysis",
        "deliverable": "markdown framing table + JSON gate receipt",
        "antipatterns": [
            "jumping to solutions before naming the single decision and non-goals",
            "hiding owner accountability or blending multiple unrelated decisions into one run",
            "letting an LLM override the deterministic strategy-studio route",
        ],
        "visual_rule": "Any framing diagram must show one clear decision boundary, explicit non-goals, and labelled axes.",
    },
    "diagnose": {
        "purpose": "surface root-cause evidence, structural constraints, and verifiable facts",
        "deliverable": "evidence-backed diagnosis table + named GAP list",
        "antipatterns": [
            "restating symptoms as causes without cited evidence",
            "inventing baseline metrics instead of marking missing data as UNVERIFIED / GAP",
            "using word clouds or icon-heavy infographics in place of causal evidence",
        ],
        "visual_rule": "Diagnostic charts must separate observed evidence from hypotheses with zero decorative chartjunk.",
    },
    "options": {
        "purpose": "generate mutually exclusive strategic alternatives with explicit trade-offs",
        "deliverable": "structured option comparison matrix in markdown + JSON",
        "antipatterns": [
            "presenting a single disguised preference alongside straw-man options",
            "omitting the do-nothing / status-quo baseline option",
            "spaghetti option trees with unlabelled branches or missing trade-off criteria",
        ],
        "visual_rule": "Option trees and 2x2 matrices must carry labelled axes, named quadrants, and an action title.",
    },
    "numbers": {
        "purpose": "model unit economics, base rates, sensitivities, and sourced quantitative bounds",
        "deliverable": "sourced calculation table + sensitivity bounds + UNVERIFIED log",
        "antipatterns": [
            "quoting point estimates without ranges, base rates, or source citations",
            "truncated y-axes, dual-axis false correlation, or 3D/exploded pie charts",
            "hiding sensitivity assumptions inside prose instead of an explicit table",
        ],
        "visual_rule": "Quantitative charts must start bar/waterfall axes at zero, cite units, and highlight the single driver.",
    },
    "stress": {
        "purpose": "red-team assumptions, run pre-mortem failure paths, and set falsifiable kill criteria",
        "deliverable": "ranked failure register + kill-criteria table + red-team dissent log",
        "antipatterns": [
            "rubber-stamping the preferred option without recording strongest dissent",
            "listing vague risks with no owner, trigger threshold, or abort action",
            "letting the builder agent act as its own sole verifier",
        ],
        "visual_rule": "Risk matrices must define both axes numerically and map every top risk to a named owner.",
    },
    "commit": {
        "purpose": "lock one recommendation, decision rights, explicit trade-offs, and reversible vs irreversible gates",
        "deliverable": "one-page decision memo + authority map + Gate-D approval checklist",
        "antipatterns": [
            "hedging with three parallel recommendations instead of one clear call",
            "committing outward spend, publishing, or sends without Mike's exact-text Gate-D approval",
            "omitting who owns execution and what evidence reverses the decision",
        ],
        "visual_rule": "Decision summaries fit on one scannable page with one headline takeaway and explicit owners.",
    },
    "operate": {
        "purpose": "translate the committed strategy into sequenced milestones, owners, telemetry, and review cadence",
        "deliverable": "90-day execution table + owner matrix + verification command list",
        "antipatterns": [
            "listing milestones without dates, single owners, or runnable verification checks",
            "serializing independent workstreams that can run in parallel",
            "shipping dashboards with rainbow colormaps or unreadable multi-series spaghetti lines",
        ],
        "visual_rule": "Roadmaps and telemetry charts must cap active series and show clear target vs actual thresholds.",
    },
    "visual-quality": {
        "purpose": "audit every strategy diagram against the Jev-verified good/bad visual corpus before handoff",
        "deliverable": "visual QA scorecard + hosted jev-image receipt + fix list",
        "antipatterns": [
            "accepting a chart because it looks polished without checking axis scales, labels, and action titles",
            "self-certifying visual quality when hosted jev-image is unreachable (must return DEFERRED)",
            "redistributing copyrighted third-party images instead of URL + hash + license references",
        ],
        "visual_rule": (
            "Compare every rendered figure against corpus/good/verified.jsonl exemplars "
            "and corpus/bad/verified.jsonl antipatterns via hosted jev-image."
        ),
    },
    "antipattern": {
        "purpose": "screen the strategy draft and its visuals against the catalogued bad-example corpus and analytical failure modes",
        "deliverable": "antipattern audit report + pass/block checklist",
        "antipatterns": [
            "ignoring visual antipatterns (truncated axis, 3D pie, buzzword text wall, dual axis, rainbow scale)",
            "allowing banned hype language or unsourced superlatives into executive copy",
            "treating a clean template scan as proof of substantive soundness",
        ],
        "visual_rule": "Fail any artifact matching a catalogued corpus/bad/verified.jsonl antipattern until corrected and re-checked.",
    },
    "learn": {
        "purpose": "capture falsifiable predictions, outcome receipts, and durable lessons into the run ledger",
        "deliverable": "post-run ledger JSONL entry + calibration notes + improvement backlog",
        "antipatterns": [
            "closing a run without logging audit hash, Jev verdict, and testable predictions",
            "overwriting prior ledger entries instead of appending immutable JSONL receipts",
            "mutating step skills directly without a holdout eval check in rs-meta-harness",
        ],
        "visual_rule": "Calibration and outcome charts must plot predicted vs actual ranges with sample sizes visible.",
    },
}

STAGES = list(STAGE_META.keys())
SURFACE_RE = re.compile(r"\n*<!-- skill-surface:BEGIN -->.*?<!-- skill-surface:END -->\s*$", re.DOTALL)


def write_skill(path: pathlib.Path, name: str, desc: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    preserved = ""
    if path.exists():
        old = path.read_text(encoding="utf-8")
        m = SURFACE_RE.search(old)
        if m:
            preserved = "\n\n" + m.group(0).strip() + "\n"
    clean_desc = " ".join(desc.split())
    content = f"---\nname: {name}\ndescription: {clean_desc}\n---\n\n# {name}\n\n{body.strip()}\n{preserved}"
    path.write_text(content, encoding="utf-8")


def build_all() -> int:
    # 1. Layer 2 stage metaskills (10) + Layer 3 step skills (110)
    step_count = 0
    for stage in STAGES:
        sm = STAGE_META[stage]
        kids = [f"rs-{m['id']}-{stage}" for m in METHODS]
        stage_desc = (
            f"Route the '{stage}' stage of /rigstrategy to the matching rs-<method>-{stage} step skill so you "
            f"{sm['purpose']}. Use when 'run stage {stage}', 'rigstrategy {stage}', or 'strategy {stage} worksheet' "
            f"is requested after strategy-studio deterministic JSON routing. Produces {sm['deliverable']} with "
            f"audit hash receipts, visual corpus antipattern checks, and hosted Jev exit gates."
        )
        stage_body = f"""## Inputs & Defaults
- **Required inputs:** Routed JSON receipt from `strategy-studio route --json "<question>"` (method ID, score, audit hash)
  and prior stage worksheet markdown.
- **Default owner & boundary:** Owner `iris-strategy`; wraps `/strategy` doctrine without forking it. Tool =
  `strategy-studio` router; record = `.strategy-studio/audit.jsonl`.

## Workflow Steps
1. Read `method` from the deterministic router JSON; never re-route with an LLM.
2. Select exactly ONE child skill matching that method:
{chr(10).join(f"   - `{k}`" for k in kids)}
3. Load the child's `SKILL.md` and execute its numbered steps, producing `{sm['deliverable']}`.
4. Run the visual and analytical check against `corpus/good/verified.jsonl` and `corpus/bad/verified.jsonl`.
5. Run `rigstrategy/hooks/pre-done-jev.sh` with `--subject rigstrategy:{stage}@<sha12>` before advancing.

## Failure & Fallback Handling
- **Missing route JSON:** STOP and invoke `rigstrategy/harness.py "<question>" --json` first.
- **Unknown method ID:** Fall back to `rs-frame-problem-{stage}` and record a named `GAP`.
- **Hosted Jev unreachable:** Emit status `DEFERRED`, never self-certify a PASS.

## Anti-Patterns (Do Not Do)
{chr(10).join(f"- Do not {ap}." for ap in sm['antipatterns'])}
- Never bulk-load all 11 child skills into context at once.

## Gate-D Checkpoint & Exit Gate
- **CHECKPOINT (Gate-D):** Drafts only; stop for Mike's explicit approval of exact text before any outward send, publish, or spend.
- **Output format / Done when:** Child `{sm['deliverable']}` written, sources cited or marked `UNVERIFIED`, audit hash
  attached, and hosted Jev returns `PASS` (or `DEFERRED` if offline).
"""
        write_skill(LIB_ROOT / f"rs-{stage}" / "SKILL.md", f"rs-{stage}", stage_desc, stage_body)

        for m in METHODS:
            mid = m["id"]
            mname = m["name"]
            arch = m.get("archetype", "A1")
            summary = m.get("summary", "")
            gates = m.get("gates", [])
            ws_fields = m.get("worksheet", [])
            doctrine_step = STRAT_MAP.get(mid, "strat-diagnose-frame-problem")
            ws_lines = "\n".join(f"  - `{f['field']}`: {f['prompt']}" for f in ws_fields)
            gate_str = ", ".join(f"`{g}`" for g in gates)

            step_desc = (
                f"Execute stage '{stage}' for the {mname} ({mid}) strategy method inside /rigstrategy to "
                f"{sm['purpose']}. Use when strategy-studio routes to '{mid}', 'run {mid} {stage}', or "
                f"'{mname.lower()} {stage} worksheet'. Consumes routed JSON and worksheet markdown; emits "
                f"{sm['deliverable']}, audit hash receipt, and Jev-gated evidence table."
            )
            step_body = f"""## Inputs & Defaults
- **Method:** `{mid}` - {mname} (Archetype `{arch}`). {summary}
- **Wrapped `/strategy` doctrine:** `{doctrine_step}` (read when domain doctrine detail is needed; never fork it).
- **Method gates:** {gate_str}.
- **Worksheet fields (`src/strategy_studio/data/methods.json`):**
{ws_lines}
- **Default inputs:** Redacted question, deterministic route JSON (`method`, `score`, `audit.hash`), and verified corpus
  indexes (`corpus/good/verified.jsonl`, `corpus/bad/verified.jsonl`).

## Workflow Steps
1. Verify `route.method == "{mid}"` and confirm the audit chain via `rigstrategy/hooks/post-route-audit.sh`.
2. Populate or update the `{mid}` worksheet fields required for stage `{stage}`, citing a source file/URL for every number
  or marking it `UNVERIFIED` / `GAP`.
3. Apply the `{stage}` lens to {mname}: {sm['purpose']}.
4. Check any tables or diagrams against the visual rule: {sm['visual_rule']}
5. Hand the draft to `rs-agent-goldfish-verifier` (zero-context) or run
  `rigstrategy/workflows/rs-{mid}-{stage}.workflow.js`, then gate via `rigstrategy/hooks/pre-done-jev.sh`.

## Failure & Fallback Handling
- **Route mismatch or missing audit hash:** STOP and re-run `rigstrategy/harness.py "<question>" --json`.
- **Missing quantitative evidence:** Record a named `GAP` with the smallest next lookup step; never invent numbers.
- **Hosted Jev or jev-image unavailable:** Return `DEFERRED` with exact error output; never self-certify.

## Anti-Patterns (Do Not Do)
{chr(10).join(f"- Do not {ap}." for ap in sm['antipatterns'])}
- Never skip the `{mid}` method gates ({gate_str}) or claim done without a read-back receipt.

## Gate-D Checkpoint & Exit Gate
- **CHECKPOINT (Gate-D):** Strictly inward drafts only; never send, publish, or commit spend without Mike's explicit approval of exact text.
- **Output format / Done when:** Stage `{stage}` section appended as `{sm['deliverable']}`, method gates checked, audit hash
  linked, and hosted Jev returns `PASS` (or `DEFERRED` if down).
"""
            write_skill(LIB_ROOT / f"rs-{mid}-{stage}" / "SKILL.md", f"rs-{mid}-{stage}", step_desc, step_body)
            step_count += 1

    # 2. Agents (6)
    agent_specs = {
        "framer": (
            "Frame ambiguous business questions into one bounded decision, explicit non-goals, and verifiable success criteria",
            "markdown decision brief + JSON scope boundary",
            "merging multiple decisions or skipping non-goals",
        ),
        "analyst": (
            "Collect grounded evidence, map method worksheet fields, and separate observed facts from named gaps",
            "sourced evidence table + populated method worksheet markdown",
            "citing memory without reading source files or hiding missing data",
        ),
        "red-teamer": (
            "Attack strategy drafts with pre-mortem failure modes, strongest dissent, and falsifiable kill criteria",
            "adversarial dissent report + ranked failure-mode table",
            "softening objections or agreeing with the builder without testing assumptions",
        ),
        "numbers-checker": (
            "Audit every figure, unit-economics formula, base rate, and sensitivity bound for arithmetic and source truth",
            "reconciled numbers table + UNVERIFIED flag log",
            "approving invented numbers, unsourced market sizes, or unverified arithmetic",
        ),
        "visual-judge": (
            "Score strategy charts and diagrams against the Jev-verified good/bad corpus using hosted jev-image",
            "JSON jev-image verdict receipt + antipattern fix list",
            "self-certifying visual quality or redistributing copyrighted source images",
        ),
        "goldfish-verifier": (
            "Verify finished strategy artifacts with zero builder context to catch unsupported claims and gate omissions",
            "independent PASS/FAIL verification report + evidence receipt",
            "sharing builder chat history, editing its own judge, or rubber-stamping claims",
        ),
    }
    for agent_name, (role_do, deliv, bad_thing) in agent_specs.items():
        desc = (
            f"Run the /rigstrategy '{agent_name}' specialist agent to {role_do}. Use when the orchestrator "
            f"dispatches 'rs-agent-{agent_name}', 'strategy {agent_name}', or 'verify with {agent_name}'. "
            f"Reads routed JSON and worksheet markdown; outputs {deliv} under strict Gate-D and Jev rules."
        )
        body = f"""## Inputs & Defaults
- **Role:** `{agent_name}` (owner `iris-strategy`, child of `/rigstrategy`).
- **Context boundary:** `{agent_name}` operates only on the explicit artifact packet passed in (`routed JSON`, `worksheet
  markdown`, `audit hash`); verifier agents never inherit builder context.

## Workflow Steps
1. Inspect the incoming routed JSON receipt and target artifact verbatim before writing any finding.
2. Execute the `{agent_name}` mandate: {role_do}.
3. Tag every empirical claim with its file/URL source or mark it `UNVERIFIED` / `GAP`.
4. Emit `{deliv}` with explicit pass/fail criteria and next corrective action if blocked.
5. Pass the final output through `rigstrategy/hooks/pre-done-jev.sh` before returning to the orchestrator.

## Failure & Fallback Handling
- **Missing or malformed artifact packet:** STOP and report the missing fields; never guess missing evidence.
- **Hosted Jev / jev-image unreachable:** Return `DEFERRED`; never self-certify.

## Anti-Patterns (Do Not Do)
- Do not allow {bad_thing}.
- Never run outward side effects (send, publish, push, spend) from an agent role.
- Never allow a builder agent to serve as its own sole verifier.

## Gate-D Checkpoint & Exit Gate
- **CHECKPOINT (Gate-D):** Drafts and verdicts only; outward actions require Mike's explicit approval of exact text.
- **Output format / Done when:** `{deliv}` emitted, every claim grounded or marked `GAP`, and Jev gate recorded.
"""
        write_skill(LIB_ROOT / f"rs-agent-{agent_name}" / "SKILL.md", f"rs-agent-{agent_name}", desc, body)

    # 3. Hooks (4)
    hook_specs = {
        "pre-route-redact": (
            "Redact emails, API keys, SSNs, and local home paths before any question enters strategy-studio routing",
            "redacted plain-text question or non-zero BLOCK exit",
            "raw strategy question string via arg or stdin",
            "forwarding raw secrets, PII, or unredacted personal paths to downstream tools",
        ),
        "post-route-audit": (
            "Verify the strategy-studio routed JSON payload and hash-chained audit log integrity after every route",
            "JSON verification receipt with audit_hash and chain entry count",
            "routed JSON payload via file arg or stdin",
            "continuing a run when the audit hash is missing or the JSONL chain fails verification",
        ),
        "pre-done-jev": (
            "Gate every /rigstrategy completion claim through hosted rig-s1gate with a required subject hash",
            "JSON Jev verdict (PASS/BLOCK/ESCALATE) and exit code 0/1/2/3",
            "--subject kind:id@sha12 plus --text or --file claim",
            "claiming done without a subject hash or self-certifying when hosted Jev is offline",
        ),
        "post-run-learn": (
            "Append an immutable JSONL run receipt (method, stage, audit hash, Jev verdict, lesson) to the run ledger",
            "appended JSONL record in rigstrategy/run-ledger.jsonl",
            "method, stage, audit_hash, jev_verdict, and concise lesson note",
            "mutating or deleting historical ledger lines or logging unredacted secrets",
        ),
    }
    for hook_name, (h_do, h_out, h_in, h_bad) in hook_specs.items():
        desc = (
            f"Enforce the /rigstrategy '{hook_name}' deterministic shell hook to {h_do}. Use when "
            f"'run {hook_name}', 'strategy hook {hook_name}', or 'check {hook_name} gate' runs in the "
            f"orchestrator pipeline. Accepts {h_in}; emits {h_out}; non-zero exit blocks progression."
        )
        body = f"""## Inputs & Defaults
- **Executable:** `~/Developer/strategy-studio/rigstrategy/hooks/{hook_name}.sh`
- **Inputs:** {h_in}.
- **Exit contract:** Exit `0` = gate passed; non-zero (`1`/`2`/`3`) = hard block or `DEFERRED`.

## Workflow Steps
1. Confirm `rigstrategy/hooks/{hook_name}.sh` exists and is executable (`test -x`).
2. Invoke `rigstrategy/hooks/{hook_name}.sh` with the required arguments or piped stdin.
3. Capture stdout JSON/text and exit code verbatim.
4. Halt the pipeline immediately if exit code is non-zero; log the exact failure reason.

## Failure & Fallback Handling
- **Missing script or non-zero exit:** STOP the pipeline and surface stderr verbatim; never bypass or silently skip a hook.
- **External classifier unavailable (pre-done-jev):** Exit `2` (`DEFERRED`); never fabricate a PASS.

## Anti-Patterns (Do Not Do)
- Do not permit {h_bad}.
- Never bypass pre-commit, audit, or Jev hooks with `--no-verify` or ad-hoc flags.

## Gate-D Checkpoint & Exit Gate
- **CHECKPOINT (Gate-D):** Hooks are deterministic local guards and never perform outward sends or pushes.
- **Output format / Done when:** Hook exits `0` and prints `{h_out}`.
"""
        write_skill(LIB_ROOT / f"rs-hook-{hook_name}" / "SKILL.md", f"rs-hook-{hook_name}", desc, body)

    # 4. Loops (3)
    loop_specs = {
        "improve-loop": (
            "Run bounded /skilloptimizer evaluations across all 136 /rigstrategy skills and keep only measurable wins",
            "JSON meta-harness scorecard + diff summary",
            "rigstrategy/meta_harness.py --json",
            "mutating skills without re-running skillopt_eval.py and skilltoworkflow check",
        ),
        "eval-loop": (
            "Verify strategy-studio deterministic routing accuracy and full test suite stays at or above baseline",
            "pytest report + routing accuracy JSON receipt",
            "make verify",
            "accepting a prompt or keyword change that lowers accuracy below current baseline",
        ),
        "corpus-refresh-loop": (
            "Refresh and Jev-image-verify good/bad strategy visual corpus candidates under URL+hash+license rules",
            "updated corpus/MANIFEST.json + check_corpus.py pass output",
            "python3 rigstrategy/check_corpus.py",
            "adding unverified candidates as confirmed or storing copyrighted third-party binaries in git",
        ),
    }
    for loop_name, (l_do, l_out, l_cmd, l_bad) in loop_specs.items():
        desc = (
            f"Run the bounded /rigstrategy '{loop_name}' loop to {l_do}. Use when 'run {loop_name}', "
            f"'strategy {loop_name}', or 'check rigstrategy {loop_name}' is triggered on a schedule or audit. "
            f"Executes deterministic command checks, enforces max-turn and no-progress caps, and outputs {l_out}."
        )
        body = f"""## Inputs & Defaults
- **Primary check command:** `{l_cmd}` (run from `~/Developer/strategy-studio`).
- **Default guardrails:** Max 5 iterations, stop immediately after 3 consecutive no-progress turns, and never weaken a gate threshold.

## Workflow Steps
1. Read the current baseline receipt (`corpus/MANIFEST.json`, `make verify`, or `rigstrategy/meta_harness.py --json`).
2. Run `{l_cmd}` and record concrete before/after metrics.
3. Propose or apply at most one bounded, reversible improvement per iteration.
4. Re-run `{l_cmd}` and keep the change ONLY if metrics strictly improve with zero regressions.
5. Append the run receipt via `rigstrategy/hooks/post-run-learn.sh` and stop on pass, budget, or 3 stale turns.

## Failure & Fallback Handling
- **Metric regression:** Revert immediately and record the dead end in `rigstrategy/run-ledger.jsonl`.
- **Hosted Jev unreachable:** Stop with status `DEFERRED`; never claim a passing loop run.

## Anti-Patterns (Do Not Do)
- Do not allow {l_bad}.
- Never run unbounded loops without a stop budget or no-progress ceiling.

## Gate-D Checkpoint & Exit Gate
- **CHECKPOINT (Gate-D):** Loops are strictly local and inward; pushing commits or publishing requires Mike's explicit approval.
- **Output format / Done when:** `{l_out}` recorded, zero regressions, and stop condition logged.
"""
        write_skill(LIB_ROOT / f"rs-loop-{loop_name}" / "SKILL.md", f"rs-loop-{loop_name}", desc, body)

    # 5. Harness & Meta-Harness (2)
    harness_desc = (
        "Execute the end-to-end /rigstrategy deterministic harness from redacted question through strategy-studio "
        "JSON routing, 10-stage workflow plan, audit verification, and Jev exit gate. Use when 'run rigstrategy harness', "
        "'route and plan strategy question', or 'rs-harness' is invoked. Produces a verified JSON packet and markdown worksheet."
    )
    harness_body = """## Inputs & Defaults
- **Executable:** `python3 ~/Developer/strategy-studio/rigstrategy/harness.py "<question>" --json`
- **Defaults:** Uses `.strategy-studio/audit.jsonl` (override with `--log`), links `/strategy` doctrine via
  `method-step-map.json`, and attaches verified good/bad corpus samples.

## Workflow Steps
1. Run `rigstrategy/hooks/pre-route-redact.sh` to scrub emails, keys, SSNs, and local paths (fail closed on empty input).
2. Route deterministically via `strategy-studio route --json` (no LLM in the routing path).
3. Verify the hash-chained audit log via `rigstrategy/hooks/post-route-audit.sh`.
4. Walk the 10 stage metaskills (`rs-frame` through `rs-learn`) for the routed method, invoking `rs-agent-goldfish-verifier` independently.
5. Gate final delivery via `rigstrategy/hooks/pre-done-jev.sh` and record the receipt via `rigstrategy/hooks/post-run-learn.sh`.

## Failure & Fallback Handling
- **Hook failure (redaction or audit chain):** STOP immediately; inspect stderr and fix before continuing.
- **Ambiguous question (low margin / fallback):** Route to `frame-problem` (`rs-frame-problem-frame`) before committing to a method.
- **Hosted Jev down:** Emit `DEFERRED`; never self-certify.

## Anti-Patterns (Do Not Do)
- Do not let an LLM pick or override the deterministic router's method.
- Do not skip `pre-route-redact.sh` or `post-route-audit.sh`.
- Never claim completion without a verified audit hash and Jev receipt.

## Gate-D Checkpoint & Exit Gate
- **CHECKPOINT (Gate-D):** Harness outputs drafts and JSON receipts only; outward sends, publishes, or git pushes require
  Mike's explicit approval.
- **Output format / Done when:** Valid `rigstrategy.harness.v1` JSON packet produced, audit chain verified, and Jev gate recorded.
"""
    write_skill(LIB_ROOT / "rs-harness" / "SKILL.md", "rs-harness", harness_desc, harness_body)

    meta_desc = (
        "Evaluate and tune the /rigstrategy 136-skill tree, 110 workflows, and routing baseline using a fixed-model "
        "Pareto meta-harness. Use when 'run rs-meta-harness', 'benchmark rigstrategy skills', or 'optimize strategy harness' "
        "is requested. Outputs a reproducible JSON scorecard from skillopt_eval.py, skilltoworkflow, and pytest."
    )
    meta_body = """## Inputs & Defaults
- **Executable:** `python3 ~/Developer/strategy-studio/rigstrategy/meta_harness.py --json`
- **Fixed evaluation surface:** 136 `/rigstrategy` `SKILL.md` files (`skillopt_eval.py`), 110 `.workflow.js` files
  (`skilltoworkflow check`), 151+ `pytest` tests, and `rigstrategy/check_corpus.py`.

## Workflow Steps
1. Run `python3 rigstrategy/meta_harness.py --json` and `make verify` to capture the locked baseline scorecard.
2. Identify the lowest-scoring dimension (description /15, SkillLens static proxy /64, workflow checks, or routing accuracy).
3. Propose one bounded scaffold or prompt edit while keeping the base model fixed.
4. Re-run `meta_harness.py --json` and `make verify`; keep the variant ONLY on strict Pareto improvement with zero regressions.
5. Log the delta to `rigstrategy/run-ledger.jsonl` via `rigstrategy/hooks/post-run-learn.sh`.

## Failure & Fallback Handling
- **Any critical failure or test regression:** Revert the candidate variant immediately and log the dead end.
- **Missing `skillopt_eval.py` or `skilltoworkflow`:** STOP and report the missing tool path; never estimate scores.

## Anti-Patterns (Do Not Do)
- Do not edit the evaluator to make failing variants pass.
- Do not accept a variant that drops test pass rate or introduces soft words / runtime warnings.
- Never self-certify rubric changes without a labelled holdout set and Mike's approval.

## Gate-D Checkpoint & Exit Gate
- **CHECKPOINT (Gate-D):** Meta-harness edits stay local until verified; pushing to GitHub or publishing requires Mike's explicit approval.
- **Output format / Done when:** JSON scorecard shows 136/136 `skillopt_eval` PASS, 110/110 workflows PASS, and `make verify` exits `0`.
"""
    write_skill(LIB_ROOT / "rs-meta-harness" / "SKILL.md", "rs-meta-harness", meta_desc, meta_body)

    # 6. Layer 1 Meta: rigstrategy
    meta_skill_desc = (
        "Route a business strategy question deterministically through strategy-studio to one of 11 methods, "
        "10 stage metaskills, 110 step skills, 6 agents, 4 hooks, 3 loops, harness, and meta-harness with a "
        "Jev-gated good/bad visual corpus. Use when '/rigstrategy', 'run strategy orchestrator', or "
        "'route business strategy question' is requested. Emits JSON receipts, markdown worksheets, and audit logs; wraps /strategy."
    )
    stg_list = "\n".join(f"- `rs-{s}` - {STAGE_META[s]['purpose']}" for s in STAGES)
    meta_skill_body = f"""## Inputs & Defaults
- **Repository:** `~/Developer/strategy-studio` (`mrodgersjs-web/strategy-studio`).
- **Owner & Authority Map (skills-for-architects):** Single owner `iris-strategy`. `/rigstrategy` owns the deterministic
  routed orchestrator run (`rs-*`); `/strategy` owns domain doctrine (`strat-*`). `/rigstrategy` wraps `/strategy` and never forks it.
- **Skill / Tool / Record Boundaries:** Skills live in Aside's skill surface (`rigstrategy` + `skill-library/rs-*`);
  deterministic tools live in `strategy-studio` + `rigstrategy/hooks/*.sh` + `rigstrategy/harness.py`; records live in
  `.strategy-studio/audit.jsonl` and `corpus/MANIFEST.json` (URL + hash + license only).

## Workflow Steps
1. Run `python3 ~/Developer/strategy-studio/rigstrategy/harness.py "<question>" --json` (executes `pre-route-redact.sh`,
  deterministic `strategy-studio route --json`, and `post-route-audit.sh`).
2. Walk the 10 stage metaskills in order, loading only the single `rs-<method>-<stage>` child for the routed method:
{stg_list}
3. Dispatch specialist roles as needed (`rs-agent-framer`, `rs-agent-analyst`, `rs-agent-red-teamer`,
  `rs-agent-numbers-checker`, `rs-agent-visual-judge`) and always verify independently with `rs-agent-goldfish-verifier`.
4. Audit any visual diagrams against `corpus/good/verified.jsonl` and `corpus/bad/verified.jsonl` via hosted `jev-image`
  (calibrated v1 rubric: 40/40 gold set, 60/60 holdout).
5. Run `rigstrategy/hooks/pre-done-jev.sh` and `rigstrategy/hooks/post-run-learn.sh`; verify repo health via `make verify`.

## Failure & Fallback Handling
- **Low-confidence or ambiguous question:** Fall back to `frame-problem` (`rs-frame-problem-frame`) and name explicit `GAP`s
  before recommending action.
- **Hook or audit-chain failure:** STOP immediately and fix the underlying error; never bypass hooks.
- **Hosted Jev / jev-image unreachable:** Return `DEFERRED`; never self-certify.

## Anti-Patterns (Do Not Do)
- Do not let an LLM pick or override the strategy method; `strategy-studio` routes deterministically.
- Do not invent numbers, hide uncertainty, or redistribute copyrighted third-party images (URL + hash + license only).
- Do not ship charts with truncated axes, 3D/exploded pies, rainbow scales, buzzword walls, or unlabelled axes.
- Do not fork `/strategy` doctrine into `/rigstrategy`.

## Corpus & Verification
- **Visual corpus (`corpus/MANIFEST.json`):** 1,326 good / 881 bad scraped Wikimedia Commons candidates (URL + hash +
  license only) + 1,800 RIG-rendered SVG/PNG diagrams. Calibrated v1 Jev-image rubric (Mike-approved 40-item gold set 40/40,
  60/60 holdout): 1,597 Jev-verified good (1,400 rendered + 197 Commons) and 551 Jev-verified bad (400 rendered + 151
  Commons). Strict v0 rubric also retained in `MANIFEST.json` (380 Commons good, 355 Commons bad, 527 rendered good).
- **Done-test:** `make verify` (pytest, 110/110 `skilltoworkflow check`, 136/136 `skillopt_eval.py`, 4 executable hooks,
  corpus gate, and `skill-surface where rigstrategy`).

## Gate-D Checkpoint & Exit Gate
- **CHECKPOINT (Gate-D):** Drafts only, strictly inward. Never send, publish, spend, or push to a public repo without Mike's
  explicit approval of the exact text/action.
- **Output format / Done when:** Routed JSON receipt, completed stage worksheet markdown, verified audit hash, independent
  verification note, and hosted Jev `PASS` (or `DEFERRED` if offline).
"""
    write_skill(META_ROOT / "rigstrategy" / "SKILL.md", "rigstrategy", meta_skill_desc, meta_skill_body)
    return step_count


if __name__ == "__main__":
    n = build_all()
    total = 1 + 10 + n + 6 + 4 + 3 + 2
    print(f"generated rigstrategy meta + 10 stages + {n} steps + 6 agents + 4 hooks + 3 loops + 2 harnesses = {total} skills")
