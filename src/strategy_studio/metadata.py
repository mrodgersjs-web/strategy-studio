"""Archetype metadata — enriches routing with complexity, horizon, stakeholders."""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class ArchetypeMeta:
    archetype: str
    complexity: str        # low / medium / high / critical
    time_horizon: str      # days / weeks / months / quarters / years
    stakeholders: int
    reversibility: str     # easy / moderate / hard / irreversible
    decision_speed: str    # fast / deliberate / slow
    recommended_tools: list[str]
    description: str
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

METADATA: dict[str, ArchetypeMeta] = {
    "A1": ArchetypeMeta("A1", "high", "months", 8, "hard", "deliberate",
        ["RACI matrix", "span-of-control calculator", "org chart"],
        "Org design decisions have long-lasting structural impact and are hard to reverse."),
    "A2": ArchetypeMeta("A2", "medium", "weeks", 4, "moderate", "deliberate",
        ["TCO calculator", "evidence table", "decision matrix"],
        "Build vs buy decisions require structured comparison with clear kill criteria."),
    "A3": ArchetypeMeta("A3", "high", "quarters", 3, "easy", "slow",
        ["base rate table", "calibration tracker", "Brier score"],
        "Forecasting requires calibration, base rates, and disconfirming evidence."),
    "A4": ArchetypeMeta("A4", "medium", "days", 5, "moderate", "fast",
        ["checklist", "rollback runbook", "staged rollout plan"],
        "Go-live decisions need eval gates, rollback plans, and named owners."),
    "A5": ArchetypeMeta("A5", "medium", "months", 4, "moderate", "deliberate",
        ["competitor matrix", "moat audit", "positioning canvas"],
        "Competitive positioning requires evidence of differentiation and moat durability."),
    "A6": ArchetypeMeta("A6", "high", "months", 6, "hard", "slow",
        ["Van Westendorp", "value metric canvas", "tier fence matrix"],
        "Pricing decisions are high-stakes and hard to reverse once customers anchor."),
    "A7": ArchetypeMeta("A7", "high", "quarters", 7, "hard", "slow",
        ["TAM/SAM/SOM", "barrier analysis", "beachhead selector"],
        "Market entry requires sizing, barrier analysis, and sequenced GTM."),
    "A8": ArchetypeMeta("A8", "medium", "quarters", 5, "easy", "deliberate",
        ["impact/effort grid", "dependency map", "RICE score"],
        "Portfolio prioritization is about what you say NO to."),
    "A9": ArchetypeMeta("A9", "medium", "months", 4, "moderate", "deliberate",
        ["value exchange canvas", "partnership scorecard", "exit clause template"],
        "Partnerships need clear value exchange, exclusivity terms, and exit clauses."),
    "A10": ArchetypeMeta("A10", "high", "quarters", 5, "moderate", "deliberate",
        ["unit economics calculator", "cohort analysis", "growth loop mapper"],
        "Growth decisions require unit economics, growth loops, and capacity limits."),
    "A11": ArchetypeMeta("A11", "critical", "months", 6, "irreversible", "slow",
        ["requirement matrix", "control gap analysis", "audit trail"],
        "Compliance decisions are high-stakes with regulatory consequences."),
    "A12": ArchetypeMeta("A12", "low", "weeks", 3, "easy", "fast",
        ["process map", "automation ROI calculator", "toil tracker"],
        "Ops efficiency is about automating the repetitive and measuring the rest."),
}

def get_metadata(archetype: str) -> ArchetypeMeta | None:
    return METADATA.get(archetype)

def list_metadata() -> list[dict[str, Any]]:
    return [m.to_dict() for m in METADATA.values()]
