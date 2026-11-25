"""Decision record persistence and gate validation.

Every routing decision produces a DecisionRecord that captures the full
context: question, route, gate results, confidence, and timestamp.
Records persist to JSONL for auditability.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .router import Route, route_question


# ── Gate definitions per archetype ──────────────────────────────────────

@dataclass(frozen=True)
class GateSpec:
    """Specification for a single gate."""
    name: str
    check_type: str  # "keyword", "length", "presence", "always_pass"
    description: str
    keywords: list[str] = field(default_factory=list)
    min_length: int = 0


# Gate registry: archetype → list of GateSpec
GATE_REGISTRY: dict[str, list[GateSpec]] = {
    "A1": [
        GateSpec("role-boundary", "keyword", "Question mentions specific roles or boundaries",
                 keywords=["role", "responsibility", "boundary", "scope", "who"]),
        GateSpec("span-check", "keyword", "Question addresses span of control",
                 keywords=["report", "manage", "team", "headcount", "direct"]),
    ],
    "A2": [
        GateSpec("evidence-table", "keyword", "Question implies comparison of alternatives",
                 keywords=["compare", "versus", "vs", "alternative", "option", "pros", "cons"]),
        GateSpec("tco-bound", "keyword", "Total cost of ownership is relevant",
                 keywords=["cost", "price", "budget", "tco", "total", "expense"]),
        GateSpec("kill-criteria", "keyword", "Kill criteria for the decision are named",
                 keywords=["kill", "stop", "fail", "criteria", "threshold", "when"]),
    ],
    "A3": [
        GateSpec("base-rate", "keyword", "Base rate or historical frequency referenced",
                 keywords=["base rate", "historical", "frequency", "average", "typically"]),
        GateSpec("calibration", "keyword", "Calibration or confidence level mentioned",
                 keywords=["confidence", "calibrat", "sure", "certain", "probability"]),
        GateSpec("disconfirm", "keyword", "Disconfirming evidence sought",
                 keywords=["disconfirm", "against", "contrary", "however", "but", "risk"]),
    ],
    "A4": [
        GateSpec("eval-green", "keyword", "Evaluation or testing gate referenced",
                 keywords=["test", "eval", "green", "pass", "ready", "verify"]),
        GateSpec("rollback", "keyword", "Rollback plan mentioned",
                 keywords=["rollback", "revert", "undo", "back", "recover"]),
        GateSpec("owner-named", "keyword", "An owner or responsible party named",
                 keywords=["owner", "responsible", "who", "assign", "lead", "accountable"]),
    ],
    "A5": [
        GateSpec("competitor-map", "keyword", "Competitors identified by name or category",
                 keywords=["competitor", "rival", "alternative", "other", "market"]),
        GateSpec("moat-audit", "keyword", "Moat or defensibility discussed",
                 keywords=["moat", "defensible", "advantage", "unique", "differentiat"]),
        GateSpec("differentiation-proof", "keyword", "Evidence of differentiation provided",
                 keywords=["proof", "evidence", "data", "metric", "benchmark"]),
    ],
    "A6": [
        GateSpec("value-metric", "keyword", "Value metric for pricing identified",
                 keywords=["value", "metric", "measure", "per", "unit", "usage"]),
        GateSpec("tier-fence", "keyword", "Tier boundaries defined",
                 keywords=["tier", "plan", "fence", "limit", "feature", "free", "pro"]),
        GateSpec("price-test", "keyword", "Price testing or validation mentioned",
                 keywords=["test", "experiment", "a/b", "validate", "survey", "willingness"]),
    ],
    "A7": [
        GateSpec("tam-sam-som", "keyword", "Market sizing referenced",
                 keywords=["tam", "sam", "som", "market size", "billion", "million"]),
        GateSpec("entry-barrier", "keyword", "Entry barriers identified",
                 keywords=["barrier", "regulation", "competitor", "capital", "network"]),
        GateSpec("go-to-market-seq", "keyword", "GTM sequencing discussed",
                 keywords=["sequence", "phase", "first", "then", "step", "plan"]),
    ],
    "A8": [
        GateSpec("impact-effort", "keyword", "Impact vs effort tradeoff considered",
                 keywords=["impact", "effort", "high", "low", "quick", "big", "small"]),
        GateSpec("dependency-map", "keyword", "Dependencies between items mapped",
                 keywords=["depend", "block", "prerequisite", "before", "after", "sequence"]),
        GateSpec("kill-criteria", "keyword", "Criteria for dropping items defined",
                 keywords=["kill", "drop", "cut", "remove", "not doing"]),
    ],
    "A9": [
        GateSpec("value-exchange", "keyword", "Value exchange between partners defined",
                 keywords=["value", "exchange", "mutual", "benefit", "both", "give", "get"]),
        GateSpec("exclusivity-check", "keyword", "Exclusivity terms considered",
                 keywords=["exclusive", "non-exclusive", "sole", "only", "lock"]),
        GateSpec("exit-clause", "keyword", "Exit or termination terms named",
                 keywords=["exit", "terminate", "end", "dissolve", "wind"]),
    ],
    "A10": [
        GateSpec("unit-economics", "keyword", "Unit economics referenced",
                 keywords=["cac", "ltv", "margin", "payback", "economics", "cost per"]),
        GateSpec("growth-loop", "keyword", "Growth loop or flywheel described",
                 keywords=["loop", "flywheel", "viral", "referral", "organic", "compound"]),
        GateSpec("capacity-limit", "keyword", "Capacity constraints identified",
                 keywords=["capacity", "limit", "constraint", "bottleneck", "scale"]),
    ],
    "A11": [
        GateSpec("requirement-map", "keyword", "Specific requirements enumerated",
                 keywords=["requirement", "must", "shall", "mandate", "regulation"]),
        GateSpec("control-gap", "keyword", "Control gaps identified",
                 keywords=["gap", "missing", "lack", "absent", "need", "implement"]),
        GateSpec("residual-risk", "keyword", "Residual risk after controls assessed",
                 keywords=["residual", "remaining", "after", "mitigate", "accept"]),
    ],
    "A12": [
        GateSpec("current-state", "keyword", "Current state documented",
                 keywords=["current", "now", "today", "existing", "manual", "status quo"]),
        GateSpec("automation-candidate", "keyword", "Automation candidates identified",
                 keywords=["automat", "script", "tool", "robot", "pipeline", "workflow"]),
        GateSpec("roi-threshold", "keyword", "ROI threshold for automation defined",
                 keywords=["roi", "return", "save", "time", "hours", "worth", "payback"]),
    ],
}


@dataclass
class GateResult:
    """Result of evaluating a single gate."""
    name: str
    passed: bool
    score: float  # 0.0–1.0
    evidence: str  # what triggered or missed


@dataclass
class DecisionRecord:
    """Full record of a routing decision with gate validation."""
    question: str
    route: Route
    timestamp: str
    gate_results: list[GateResult]
    confidence: float  # 0.0–1.0, derived from gate pass rate
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["route"] = asdict(self.route)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def evaluate_gate(gate: GateSpec, question: str) -> GateResult:
    """Evaluate a single gate against a question."""
    t = question.lower()

    if gate.check_type == "always_pass":
        return GateResult(gate.name, True, 1.0, "always-pass gate")

    if gate.check_type == "keyword":
        for kw in gate.keywords:
            if kw.lower() in t:
                return GateResult(gate.name, True, 1.0, f"matched keyword: {kw!r}")
        return GateResult(gate.name, False, 0.0,
                          f"no match from: {', '.join(gate.keywords[:5])}")

    if gate.check_type == "length":
        ok = len(question) >= gate.min_length
        return GateResult(gate.name, ok, 1.0 if ok else 0.0,
                          f"length={len(question)} (min={gate.min_length})")

    return GateResult(gate.name, False, 0.0, f"unknown check_type: {gate.check_type}")


def evaluate_gates(archetype: str, question: str) -> list[GateResult]:
    """Evaluate all gates for an archetype."""
    specs = GATE_REGISTRY.get(archetype, [])
    return [evaluate_gate(g, question) for g in specs]


def compute_confidence(gate_results: list[GateResult], question: str = "") -> float:
    """Confidence = gate pass rate weighted by question detail.

    Longer, more specific questions get a small boost (up to +0.15)
    because they provide more signal for gate matching.
    """
    if not gate_results:
        return 0.0
    base = sum(1 for g in gate_results if g.passed) / len(gate_results)
    if not question:
        return base
    # Detail bonus: word count and keyword density
    words = len(question.split())
    detail_bonus = min(0.15, words * 0.005)  # +0.005 per word, capped at 0.15
    return min(1.0, base + detail_bonus)


def make_decision(question: str) -> DecisionRecord:
    """Route a question and produce a full decision record with gate validation."""
    route = route_question(question)
    gate_results = evaluate_gates(route.archetype, question)
    confidence = compute_confidence(gate_results, question)

    return DecisionRecord(
        question=question,
        route=route,
        timestamp=datetime.now(timezone.utc).isoformat(),
        gate_results=gate_results,
        confidence=confidence,
    )


# ── JSONL persistence ──────────────────────────────────────────────────

DEFAULT_STORE_DIR = Path.home() / ".rig" / "1000x" / "strategy-records"


class DecisionStore:
    """Append-only JSONL store for decision records."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else DEFAULT_STORE_DIR / "decisions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: DecisionRecord) -> Path:
        """Append a decision record to the store as one compact JSON line."""
        with open(self.path, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
        return self.path

    def read_all(self) -> list[DecisionRecord]:
        """Read all records from the store."""
        if not self.path.exists():
            return []
        records = []
        for line in self.path.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            route = Route(**d["route"])
            gate_results = [GateResult(**g) for g in d.get("gate_results", [])]
            records.append(DecisionRecord(
                question=d["question"],
                route=route,
                timestamp=d["timestamp"],
                gate_results=gate_results,
                confidence=d.get("confidence", 0.0),
                metadata=d.get("metadata", {}),
            ))
        return records

    def count(self) -> int:
        """Count records in the store."""
        if not self.path.exists():
            return 0
        return sum(1 for line in self.path.read_text().splitlines() if line.strip())
