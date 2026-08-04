"""Deterministic archetype router — no LLM required."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import re

@dataclass(frozen=True)
class Route:
    archetype: str
    cell: str
    gates: list[str]
    rationale: str

def route_question(q: str) -> Route:
    t = q.lower()
    if re.search(r"\b(buy|build|make vs|vendor|outsource)\b", t):
        return Route("A2", "cell.build-vs-buy", ["evidence-table", "tco-bound", "kill-criteria"], "Choice under alternatives")
    if re.search(r"\b(forecast|predict|probability|risk)\b", t):
        return Route("A3", "cell.forecast-risk", ["base-rate", "calibration", "disconfirm"], "Uncertainty quantification")
    if re.search(r"\b(hire|org|team|role|staff)\b", t):
        return Route("A1", "cell.org-design", ["role-boundary", "span-check"], "Organization design")
    if re.search(r"\b(ship|launch|go-live|deploy|rollout)\b", t):
        return Route("A4", "cell.go-live", ["eval-green", "rollback", "owner-named"], "Execution / go-live")
    return Route("A1", "cell.frame-problem", ["define-outcome", "non-goals"], "Default framing cell")

def to_dict(r: Route) -> dict:
    return asdict(r)
