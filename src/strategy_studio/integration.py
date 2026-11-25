"""Integration module — wires routing + gates + playbooks into one response.

The full strategy response for a question includes:
- Route (archetype, cell, gates, rationale)
- Gate evaluation results + confidence
- Cell playbook (steps, questions, template, pitfalls)
- Decision record (persistable)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .playbooks import Playbook, get_playbook
from .metadata import ArchetypeMeta, get_metadata
from .records import DecisionRecord, DecisionStore, GateResult, make_decision
from .router import Route


@dataclass
class StrategyResponse:
    """Complete strategy analysis for a single question."""
    question: str
    route: Route
    gate_results: list[GateResult]
    confidence: float
    playbook: Playbook | None
    metadata: ArchetypeMeta | None
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "question": self.question,
            "route": {
                "archetype": self.route.archetype,
                "cell": self.route.cell,
                "gates": self.route.gates,
                "rationale": self.route.rationale,
            },
            "confidence": round(self.confidence, 4),
            "timestamp": self.timestamp,
        }
        if self.gate_results:
            d["gate_results"] = [
                {"name": g.name, "passed": g.passed, "evidence": g.evidence}
                for g in self.gate_results
            ]
        if self.playbook:
            d["playbook"] = {
                "title": self.playbook.title,
                "description": self.playbook.description,
                "steps": [
                    {"order": s.order, "name": s.name, "instruction": s.instruction}
                    for s in self.playbook.steps
                ],
                "key_questions": self.playbook.key_questions,
                "template": self.playbook.template,
                "pitfalls": self.playbook.pitfalls,
            }
        if self.metadata:
            d["archetype_meta"] = self.metadata.to_dict()
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def format_text(self) -> str:
        """Human-readable text output."""
        lines = [
            f"  Question    : {self.question}",
            f"  Archetype   : {self.route.archetype}",
            f"  Cell        : {self.route.cell}",
            f"  Rationale   : {self.route.rationale}",
            f"  Confidence  : {self.confidence:.0%}",
            f"  Gates       : {', '.join(self.route.gates)}",
        ]
        if self.gate_results:
            lines.append(f"  Gate results:")
            for g in self.gate_results:
                mark = "✓" if g.passed else "✗"
                lines.append(f"    {mark} {g.name}: {g.evidence}")
        if self.playbook:
            pb = self.playbook
            lines.append(f"\n  Playbook: {pb.title}")
            lines.append(f"  {pb.description}")
            lines.append(f"\n  Steps:")
            for s in pb.steps:
                lines.append(f"    {s.order}. {s.name}: {s.instruction}")
            lines.append(f"\n  Key questions:")
            for q in pb.key_questions:
                lines.append(f"    • {q}")
            lines.append(f"\n  Pitfalls:")
            for pit in pb.pitfalls:
                lines.append(f"    ⚠ {pit}")
        if self.metadata:
            m = self.metadata
            lines.append(f"\n  Meta: complexity={m.complexity} horizon={m.time_horizon} stakeholders={m.stakeholders} reversibility={m.reversibility} speed={m.decision_speed}")
            lines.append(f"  Tools: {chr(44).join(m.recommended_tools)}")
        return "\n".join(lines)


def analyze_question(question: str, store: DecisionStore | None = None) -> StrategyResponse:
    """Full strategy analysis: route → gates → playbook → persist."""
    rec = make_decision(question)
    playbook = get_playbook(rec.route.cell)
    if store:
        store.append(rec)
    return StrategyResponse(
        question=question,
        route=rec.route,
        gate_results=rec.gate_results,
        confidence=rec.confidence,
        playbook=playbook,
        metadata=get_metadata(rec.route.archetype),
        timestamp=rec.timestamp,
    )


def analyze_batch(questions: list[str],
                  store: DecisionStore | None = None) -> list[StrategyResponse]:
    """Analyze multiple questions, optionally persisting all."""
    return [analyze_question(q, store) for q in questions if q.strip()]
