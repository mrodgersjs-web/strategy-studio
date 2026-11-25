"""Batch routing and archetype analytics.

Route multiple questions from file/stdin, then produce aggregate
statistics from the decision store.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .records import DecisionRecord, DecisionStore, make_decision
from .router import Route


# ── Batch routing ──────────────────────────────────────────────────────

def route_batch(questions: list[str]) -> list[DecisionRecord]:
    """Route a list of questions, returning one DecisionRecord each."""
    return [make_decision(q) for q in questions if q.strip()]


def route_from_file(path: Path | str) -> list[DecisionRecord]:
    """Route questions from a file (one per line, blank lines skipped)."""
    lines = Path(path).read_text().splitlines()
    return route_batch(lines)


def route_from_stdin() -> list[DecisionRecord]:
    """Route questions from stdin (one per line)."""
    lines = [line for line in sys.stdin if line.strip()]
    return route_batch(lines)


# ── Archetype statistics ───────────────────────────────────────────────

@dataclass
class ArchetypeStats:
    """Aggregate statistics for one archetype."""
    archetype: str
    count: int
    avg_confidence: float
    cells: dict[str, int]  # cell → count
    top_questions: list[str]  # up to 5 most recent


@dataclass
class StoreSummary:
    """Summary statistics across all records in a store."""
    total_records: int
    archetype_distribution: dict[str, int]  # archetype → count
    avg_confidence: float
    confidence_histogram: dict[str, int]  # "0.0-0.2" → count, etc.
    per_archetype: list[ArchetypeStats]
    gate_pass_rates: dict[str, float]  # gate_name → pass rate

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "archetype_distribution": self.archetype_distribution,
            "avg_confidence": round(self.avg_confidence, 4),
            "confidence_histogram": self.confidence_histogram,
            "per_archetype": [
                {
                    "archetype": a.archetype,
                    "count": a.count,
                    "avg_confidence": round(a.avg_confidence, 4),
                    "cells": a.cells,
                    "top_questions": a.top_questions,
                }
                for a in self.per_archetype
            ],
            "gate_pass_rates": {k: round(v, 4) for k, v in self.gate_pass_rates.items()},
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def _confidence_bucket(conf: float) -> str:
    """Map a 0–1 confidence to a histogram bucket."""
    if conf < 0.2:
        return "0.0-0.2"
    if conf < 0.4:
        return "0.2-0.4"
    if conf < 0.6:
        return "0.4-0.6"
    if conf < 0.8:
        return "0.6-0.8"
    return "0.8-1.0"


def summarize_store(store: DecisionStore) -> StoreSummary:
    """Produce aggregate statistics from all records in a store."""
    records = store.read_all()
    if not records:
        return StoreSummary(
            total_records=0,
            archetype_distribution={},
            avg_confidence=0.0,
            confidence_histogram={},
            per_archetype=[],
            gate_pass_rates={},
        )

    # Archetype distribution
    arch_counts: Counter[str] = Counter()
    for r in records:
        arch_counts[r.route.archetype] += 1

    # Confidence
    confidences = [r.confidence for r in records]
    avg_conf = sum(confidences) / len(confidences)

    # Confidence histogram
    hist: Counter[str] = Counter()
    for c in confidences:
        hist[_confidence_bucket(c)] += 1
    # Ensure all buckets exist
    histogram = {b: hist.get(b, 0) for b in
                 ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]}

    # Per-archetype stats
    by_arch: dict[str, list[DecisionRecord]] = {}
    for r in records:
        by_arch.setdefault(r.route.archetype, []).append(r)

    per_archetype = []
    for arch, recs in sorted(by_arch.items()):
        cell_counts: Counter[str] = Counter()
        for r in recs:
            cell_counts[r.route.cell] += 1
        arch_conf = sum(r.confidence for r in recs) / len(recs)
        top_q = [r.question for r in recs[-5:]]  # 5 most recent
        per_archetype.append(ArchetypeStats(
            archetype=arch,
            count=len(recs),
            avg_confidence=arch_conf,
            cells=dict(cell_counts),
            top_questions=top_q,
        ))

    # Gate pass rates
    gate_total: Counter[str] = Counter()
    gate_passed: Counter[str] = Counter()
    for r in records:
        for g in r.gate_results:
            gate_total[g.name] += 1
            if g.passed:
                gate_passed[g.name] += 1
    gate_rates = {name: gate_passed[name] / gate_total[name]
                  for name in gate_total}

    return StoreSummary(
        total_records=len(records),
        archetype_distribution=dict(arch_counts),
        avg_confidence=avg_conf,
        confidence_histogram=histogram,
        per_archetype=per_archetype,
        gate_pass_rates=gate_rates,
    )
