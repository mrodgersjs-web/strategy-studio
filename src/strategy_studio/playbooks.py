"""Cell-level strategy playbooks.

Each routing cell maps to a structured playbook with ordered steps,
key questions, output templates, and common pitfalls. Playbooks turn
the router's archetype classification into actionable strategy guidance.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlaybookStep:
    """A single step in a strategy playbook."""
    order: int
    name: str
    instruction: str
    output_field: str  # which field this step populates in the template


@dataclass(frozen=True)
class Playbook:
    """Structured strategy playbook for a routing cell."""
    cell: str
    archetype: str
    title: str
    description: str
    steps: list[PlaybookStep]
    key_questions: list[str]
    template: dict[str, str]  # field → placeholder
    pitfalls: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ── Playbook registry ──────────────────────────────────────────────────

PLAYBOOKS: dict[str, Playbook] = {}


def _register(p: Playbook) -> None:
    PLAYBOOKS[p.cell] = p


# A1: Org design
_register(Playbook(
    cell="cell.org-design",
    archetype="A1",
    title="Organization Design",
    description="Structure teams, roles, and reporting for execution clarity.",
    steps=[
        PlaybookStep(1, "Define outcomes", "What must this team/org deliver in 90 days?", "outcomes"),
        PlaybookStep(2, "Map capabilities", "What skills are needed vs. what exists?", "capability_gap"),
        PlaybookStep(3, "Draw boundaries", "Where does ownership start and end?", "role_boundaries"),
        PlaybookStep(4, "Check span", "Can each leader actually manage their span?", "span_assessment"),
        PlaybookStep(5, "Name owners", "Every outcome needs a single accountable person.", "owners"),
    ],
    key_questions=[
        "What outcomes must this team deliver?",
        "Where are the capability gaps?",
        "Is the span of control realistic?",
        "Who is accountable for each outcome?",
    ],
    template={
        "outcomes": "<list 3-5 measurable 90-day outcomes>",
        "capability_gap": "<skills needed minus skills available>",
        "role_boundaries": "<RACI or ownership matrix>",
        "span_assessment": "<leader:direct_report ratio, feasibility>",
        "owners": "<name → outcome mapping>",
    },
    pitfalls=[
        "Reorganizing without changing incentives",
        "Too many direct reports (span > 8)",
        "Unclear ownership — two people 'own' the same thing",
    ],
))

# A2: Build vs buy
_register(Playbook(
    cell="cell.build-vs-buy",
    archetype="A2",
    title="Build vs Buy Decision",
    description="Evaluate alternatives with evidence, TCO, and kill criteria.",
    steps=[
        PlaybookStep(1, "Frame the choice", "What exactly are we deciding between?", "decision_frame"),
        PlaybookStep(2, "Evidence table", "Side-by-side comparison with sourced facts.", "evidence_table"),
        PlaybookStep(3, "TCO bound", "3-year total cost including hidden costs.", "tco_analysis"),
        PlaybookStep(4, "Kill criteria", "When do we stop and reverse this decision?", "kill_criteria"),
        PlaybookStep(5, "Decide with reversibility", "Choose the most reversible option if uncertain.", "decision"),
    ],
    key_questions=[
        "What are we actually comparing?",
        "What does 3-year TCO look like including hidden costs?",
        "What would make us reverse this decision?",
        "Can we start with the most reversible option?",
    ],
    template={
        "decision_frame": "<Option A> vs <Option B> for <specific use case>",
        "evidence_table": "| dimension | build | buy |\n|---|---|---|\n| cost | ... | ... |",
        "tco_analysis": "Year 1: $X | Year 2: $Y | Year 3: $Z | Total: $T",
        "kill_criteria": "Reverse if: <condition 1>, <condition 2>",
        "decision": "<choice> because <evidence>, reversible via <method>",
    },
    pitfalls=[
        "Comparing idealized build cost vs. real vendor cost",
        "Ignoring switching costs and lock-in",
        "No kill criteria — sunk cost fallacy takes over",
    ],
))

# A3: Forecast & risk
_register(Playbook(
    cell="cell.forecast-risk",
    archetype="A3",
    title="Forecast & Risk Quantification",
    description="Quantify uncertainty with base rates, calibration, and disconfirmation.",
    steps=[
        PlaybookStep(1, "Base rate", "What's the historical frequency of this outcome?", "base_rate"),
        PlaybookStep(2, "Calibration", "How confident are we? What's our track record?", "calibration"),
        PlaybookStep(3, "Disconfirm", "What evidence would prove us wrong?", "disconfirming"),
        PlaybookStep(4, "Range estimate", "Provide P10, P50, P90 — not a single number.", "range"),
        PlaybookStep(5, "Monitoring", "What leading indicators tell us if we're off track?", "indicators"),
    ],
    key_questions=[
        "What's the base rate for this type of outcome?",
        "What would prove our forecast wrong?",
        "What's the P10/P50/P90 range?",
        "What leading indicators should we watch?",
    ],
    template={
        "base_rate": "Historical rate: X% (source: <reference>)",
        "calibration": "Our track record on similar forecasts: Y%",
        "disconfirming": "We're wrong if: <condition>",
        "range": "P10: $X | P50: $Y | P90: $Z",
        "indicators": "<indicator 1>: threshold | <indicator 2>: threshold",
    },
    pitfalls=[
        "Anchoring on a single point estimate",
        "Ignoring base rates in favor of narrative",
        "No monitoring — forecast is set and forgotten",
    ],
))

# A4: Go-live
_register(Playbook(
    cell="cell.go-live",
    archetype="A4",
    title="Execution / Go-Live",
    description="Ship with eval gates, rollback plans, and named owners.",
    steps=[
        PlaybookStep(1, "Eval green", "What must pass before we ship?", "eval_criteria"),
        PlaybookStep(2, "Rollback plan", "How do we undo this in < 1 hour?", "rollback_plan"),
        PlaybookStep(3, "Name owner", "Who owns the go-live decision?", "owner"),
        PlaybookStep(4, "Staged rollout", "What's the blast radius at each stage?", "rollout_stages"),
        PlaybookStep(5, "Post-launch check", "What do we verify at +1h, +24h, +7d?", "post_launch"),
    ],
    key_questions=[
        "What must pass before we ship?",
        "How do we undo this in under an hour?",
        "Who owns the go-live decision?",
        "What's the blast radius at each rollout stage?",
    ],
    template={
        "eval_criteria": "<test suite / checklist that must pass>",
        "rollback_plan": "Step 1: <revert method> | Step 2: <verify> | ETA: <time>",
        "owner": "<name> owns the go/no-go decision",
        "rollout_stages": "1% → 10% → 50% → 100% with <gates between each>",
        "post_launch": "+1h: <metric> | +24h: <metric> | +7d: <metric>",
    },
    pitfalls=[
        "No rollback plan — 'we'll figure it out'",
        "Rolling out to 100% on day one",
        "No post-launch monitoring",
    ],
))

# A5: Competitive positioning
_register(Playbook(
    cell="cell.competitive-position",
    archetype="A5",
    title="Competitive Positioning",
    description="Map competitors, audit moats, and prove differentiation.",
    steps=[
        PlaybookStep(1, "Competitor map", "Who are the 3-5 real competitors?", "competitors"),
        PlaybookStep(2, "Moat audit", "What's our defensible advantage?", "moat"),
        PlaybookStep(3, "Differentiation proof", "What evidence proves we're different?", "proof"),
        PlaybookStep(4, "Positioning statement", "For <ICP>, we are <category> that <differentiator>.", "positioning"),
        PlaybookStep(5, "Win/loss signals", "Why do we win? Why do we lose?", "win_loss"),
    ],
    key_questions=[
        "Who are the real competitors (not just the famous ones)?",
        "What's our defensible moat?",
        "What evidence proves our differentiation?",
        "Why do we win and lose deals?",
    ],
    template={
        "competitors": "1. <name>: <strength> | 2. <name>: <strength>",
        "moat": "<moat type>: <evidence it's real>",
        "proof": "<metric/benchmark/customer quote>",
        "positioning": "For <ICP>, we are <category> that <differentiator> because <reason>",
        "win_loss": "Win: <pattern> | Loss: <pattern>",
    },
    pitfalls=[
        "Competing on features instead of outcomes",
        "No moat — 'we're better' without proof",
        "Ignoring indirect competitors",
    ],
))

# A6: Pricing & packaging
_register(Playbook(
    cell="cell.pricing-packaging",
    archetype="A6",
    title="Pricing & Packaging",
    description="Design pricing with value metrics, tier fences, and validation.",
    steps=[
        PlaybookStep(1, "Value metric", "What unit of value does the customer pay for?", "value_metric"),
        PlaybookStep(2, "Tier fences", "What separates free/pro/enterprise?", "tier_fences"),
        PlaybookStep(3, "Willingness to pay", "What does the market bear? Source?", "wtp"),
        PlaybookStep(4, "Price test", "How will we validate this price?", "test_plan"),
        PlaybookStep(5, "Packaging matrix", "Feature → tier mapping.", "matrix"),
    ],
    key_questions=[
        "What unit of value does the customer actually pay for?",
        "What separates each tier?",
        "What's the market's willingness to pay?",
        "How will we validate the price?",
    ],
    template={
        "value_metric": "<metric>: <why it aligns with value>",
        "tier_fences": "Free: <limits> | Pro: <limits> | Enterprise: <limits>",
        "wtp": "$X–$Y (source: <research/competitor/interview>)",
        "test_plan": "<A/B test / survey / price sensitivity meter>",
        "matrix": "| feature | free | pro | enterprise |\n|---|---|---|---|",
    },
    pitfalls=[
        "Pricing on cost instead of value",
        "Too many tiers — analysis paralysis",
        "No willingness-to-pay research",
    ],
))

# A7: Market entry
_register(Playbook(
    cell="cell.market-entry",
    archetype="A7",
    title="Market Entry & Expansion",
    description="Size the market, identify barriers, and sequence GTM.",
    steps=[
        PlaybookStep(1, "TAM/SAM/SOM", "Total, serviceable, and obtainable market.", "market_size"),
        PlaybookStep(2, "Entry barriers", "What blocks entry? Regulation? Incumbents?", "barriers"),
        PlaybookStep(3, "GTM sequence", "Phase 1: beachhead → Phase 2: expand.", "gtm_seq"),
        PlaybookStep(4, "First customers", "Who are the first 10 customers?", "first_customers"),
        PlaybookStep(5, "Success metric", "How do we know entry is working?", "success_metric"),
    ],
    key_questions=[
        "What's the TAM/SAM/SOM?",
        "What barriers block entry?",
        "What's the beachhead segment?",
        "Who are the first 10 customers?",
    ],
    template={
        "market_size": "TAM: $X | SAM: $Y | SOM: $Z",
        "barriers": "1. <barrier>: <mitigation>",
        "gtm_seq": "Phase 1 (0-6mo): <beachhead> | Phase 2 (6-18mo): <expand>",
        "first_customers": "1. <company>: <why them>",
        "success_metric": "<metric>: target by <date>",
    },
    pitfalls=[
        "TAM is huge but SAM is tiny",
        "No beachhead — trying to enter everything at once",
        "Ignoring regulatory barriers",
    ],
))

# A8: Portfolio prioritization
_register(Playbook(
    cell="cell.portfolio-priority",
    archetype="A8",
    title="Portfolio Prioritization",
    description="Rank initiatives by impact/effort, map dependencies, set kill criteria.",
    steps=[
        PlaybookStep(1, "Impact effort grid", "Plot each initiative on impact × effort.", "grid"),
        PlaybookStep(2, "Dependency map", "What blocks what?", "dependencies"),
        PlaybookStep(3, "Kill criteria", "What gets cut if resources tighten?", "kill_list"),
        PlaybookStep(4, "Sequence", "Order by: quick wins → strategic bets → long shots.", "sequence"),
        PlaybookStep(5, "Commit", "What are we NOT doing?", "not_doing"),
    ],
    key_questions=[
        "What's high impact and low effort?",
        "What blocks what?",
        "What gets cut if resources tighten?",
        "What are we explicitly NOT doing?",
    ],
    template={
        "grid": "| initiative | impact | effort | quadrant |\n|---|---|---|---|",
        "dependencies": "<initiative A> blocks <initiative B>",
        "kill_list": "Cut first: <initiative> if <condition>",
        "sequence": "Q1: <quick wins> | Q2: <strategic> | Q3+: <long shots>",
        "not_doing": "Explicitly out: <list>",
    },
    pitfalls=[
        "Everything is 'high priority'",
        "No kill criteria — portfolio only grows",
        "Ignoring dependencies between initiatives",
    ],
))

# A9: Partnerships
_register(Playbook(
    cell="cell.partnership",
    archetype="A9",
    title="Partnership & Alliances",
    description="Define value exchange, check exclusivity, and name exit terms.",
    steps=[
        PlaybookStep(1, "Value exchange", "What does each party give and get?", "value_exchange"),
        PlaybookStep(2, "Exclusivity check", "Is this exclusive? What's the cost of exclusivity?", "exclusivity"),
        PlaybookStep(3, "Exit clause", "How does either party exit?", "exit_terms"),
        PlaybookStep(4, "Success metric", "How do we measure partnership value?", "metric"),
        PlaybookStep(5, "Pilot", "What's the smallest test of this partnership?", "pilot"),
    ],
    key_questions=[
        "What does each party give and get?",
        "Is exclusivity worth the constraint?",
        "How does either party exit?",
        "What's the smallest pilot to test value?",
    ],
    template={
        "value_exchange": "We give: <X> | We get: <Y> | They give: <Z> | They get: <W>",
        "exclusivity": "Exclusive: <yes/no> | Duration: <term> | Cost of exclusivity: <analysis>",
        "exit_terms": "Exit with <notice period> + <data/asset handback>",
        "metric": "<metric>: target by <date>",
        "pilot": "<scope>: <duration>: <success criteria>",
    },
    pitfalls=[
        "Partnership for PR, not revenue",
        "No exit clause — trapped in bad deal",
        "No pilot — full commitment before validation",
    ],
))

# A10: Growth & scaling
_register(Playbook(
    cell="cell.growth-scale",
    archetype="A10",
    title="Growth & Scaling",
    description="Optimize unit economics, design growth loops, and respect capacity limits.",
    steps=[
        PlaybookStep(1, "Unit economics", "CAC, LTV, margin, payback period.", "unit_econ"),
        PlaybookStep(2, "Growth loop", "What's the self-reinforcing acquisition mechanism?", "growth_loop"),
        PlaybookStep(3, "Capacity limit", "Where does the system break?", "capacity"),
        PlaybookStep(4, "Cohort analysis", "Are newer cohorts better or worse?", "cohorts"),
        PlaybookStep(5, "Scale trigger", "What metric tells us to scale spend?", "scale_trigger"),
    ],
    key_questions=[
        "What are CAC, LTV, and payback period?",
        "What's the self-reinforcing growth loop?",
        "Where does the system break at scale?",
        "Are newer cohorts improving?",
    ],
    template={
        "unit_econ": "CAC: $X | LTV: $Y | LTV/CAC: Zx | Payback: N months",
        "growth_loop": "<input> → <action> → <output> → <input> (viral coefficient: K)",
        "capacity": "Breaks at <N> users/$M because <constraint>",
        "cohorts": "Q1 cohort: retention X% | Q2: Y% | trend: <improving/declining>",
        "scale_trigger": "Scale when <metric> exceeds <threshold> for <duration>",
    },
    pitfalls=[
        "Scaling before unit economics work",
        "No growth loop — paid acquisition only",
        "Ignoring cohort decay",
    ],
))

# A11: Risk & compliance
_register(Playbook(
    cell="cell.risk-compliance",
    archetype="A11",
    title="Risk & Compliance",
    description="Map requirements, find control gaps, and assess residual risk.",
    steps=[
        PlaybookStep(1, "Requirement map", "What does the regulation actually require?", "requirements"),
        PlaybookStep(2, "Control gap", "What controls are missing?", "gaps"),
        PlaybookStep(3, "Residual risk", "After controls, what risk remains?", "residual"),
        PlaybookStep(4, "Remediation plan", "Close gaps in priority order.", "remediation"),
        PlaybookStep(5, "Audit trail", "How do we prove compliance?", "audit_trail"),
    ],
    key_questions=[
        "What does the regulation actually require?",
        "What controls are missing?",
        "After controls, what risk remains?",
        "How do we prove compliance to an auditor?",
    ],
    template={
        "requirements": "1. <requirement>: <source citation>",
        "gaps": "1. <gap>: <severity> | mitigation: <approach>",
        "residual": "Residual risk: <level> | accepted because: <reason>",
        "remediation": "Priority 1: <gap> → <fix> by <date>",
        "audit_trail": "<evidence type>: <where stored>: <retention>",
    },
    pitfalls=[
        "Compliance theater — checkboxes without real controls",
        "No residual risk assessment",
        "Audit trail is 'we'll remember'",
    ],
))

# A12: Ops efficiency
_register(Playbook(
    cell="cell.ops-efficiency",
    archetype="A12",
    title="Operational Efficiency",
    description="Document current state, identify automation candidates, and justify ROI.",
    steps=[
        PlaybookStep(1, "Current state", "What's the process today? How long does it take?", "current_state"),
        PlaybookStep(2, "Automation candidate", "Which steps are repetitive and rule-based?", "candidates"),
        PlaybookStep(3, "ROI threshold", "Is the automation worth building?", "roi"),
        PlaybookStep(4, "Implementation", "Build/buy the automation.", "implementation"),
        PlaybookStep(5, "Monitoring", "How do we know the automation is working?", "monitoring"),
    ],
    key_questions=[
        "What's the current process and how long does it take?",
        "Which steps are repetitive and rule-based?",
        "Is the automation worth building (ROI)?",
        "How do we know it's working?",
    ],
    template={
        "current_state": "Process: <name> | Steps: N | Time: X hours/week | Error rate: Y%",
        "candidates": "1. <step>: <frequency> | complexity: <low/med/high>",
        "roi": "Build cost: X hours | Savings: Y hours/week | Payback: Z weeks",
        "implementation": "<tool/approach>: <timeline>: <owner>",
        "monitoring": "<metric>: alert if <threshold>",
    },
    pitfalls=[
        "Automating a broken process",
        "No ROI threshold — automation for automation's sake",
        "No monitoring — automation breaks silently",
    ],
))

# Default: frame problem
_register(Playbook(
    cell="cell.frame-problem",
    archetype="A1",
    title="Problem Framing",
    description="Define the outcome, scope, and non-goals before diving into strategy.",
    steps=[
        PlaybookStep(1, "Define outcome", "What does success look like?", "outcome"),
        PlaybookStep(2, "Non-goals", "What are we explicitly NOT solving?", "non_goals"),
        PlaybookStep(3, "Stakeholders", "Who cares about this and why?", "stakeholders"),
        PlaybookStep(4, "Constraints", "What are the hard constraints?", "constraints"),
        PlaybookStep(5, "Next step", "What's the smallest next action?", "next_step"),
    ],
    key_questions=[
        "What does success look like?",
        "What are we explicitly NOT solving?",
        "Who cares about this and why?",
        "What's the smallest next action?",
    ],
    template={
        "outcome": "<measurable outcome> by <date>",
        "non_goals": "1. <non-goal>: <why it's out of scope>",
        "stakeholders": "<name>: <what they care about>",
        "constraints": "1. <constraint>: <why it's hard>",
        "next_step": "<action> by <date> to <learn what>",
    },
    pitfalls=[
        "Jumping to solutions before framing the problem",
        "No non-goals — scope creep is guaranteed",
        "Too many stakeholders — decision paralysis",
    ],
))


def get_playbook(cell: str) -> Playbook | None:
    """Look up a playbook by cell name."""
    return PLAYBOOKS.get(cell)


def list_playbooks() -> list[dict[str, str]]:
    """List all registered playbooks with cell, archetype, and title."""
    return [{"cell": p.cell, "archetype": p.archetype, "title": p.title}
            for p in PLAYBOOKS.values()]
