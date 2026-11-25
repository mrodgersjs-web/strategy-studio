"""Tests for decision record persistence and gate validation."""
import json
import tempfile
from pathlib import Path

from strategy_studio.records import (
    DecisionRecord,
    DecisionStore,
    GateResult,
    GateSpec,
    compute_confidence,
    evaluate_gate,
    evaluate_gates,
    make_decision,
)
from strategy_studio.router import Route


# ── Gate evaluation ────────────────────────────────────────────────────

def test_gate_keyword_match():
    g = GateSpec("test-gate", "keyword", "test", keywords=["build", "buy"])
    r = evaluate_gate(g, "Should we build or buy?")
    assert r.passed and r.score == 1.0 and "build" in r.evidence


def test_gate_keyword_miss():
    g = GateSpec("test-gate", "keyword", "test", keywords=["xyz", "abc"])
    r = evaluate_gate(g, "Should we build or buy?")
    assert not r.passed and r.score == 0.0


def test_gate_length_pass():
    g = GateSpec("test-gate", "length", "test", min_length=10)
    r = evaluate_gate(g, "This is a long enough question")
    assert r.passed


def test_gate_length_fail():
    g = GateSpec("test-gate", "length", "test", min_length=100)
    r = evaluate_gate(g, "Short?")
    assert not r.passed


def test_gate_always_pass():
    g = GateSpec("test-gate", "always_pass", "test")
    r = evaluate_gate(g, "anything")
    assert r.passed and r.score == 1.0


# ── Archetype gate evaluation ──────────────────────────────────────────

def test_evaluate_gates_a2():
    results = evaluate_gates("A2", "Should we compare the cost of build vs vendor?")
    names = [g.name for g in results]
    assert "evidence-table" in names
    # "compare" and "cost" should pass some gates
    passed = [g for g in results if g.passed]
    assert len(passed) >= 1


def test_evaluate_gates_unknown_archetype():
    results = evaluate_gates("A99", "Some question")
    assert results == []


def test_evaluate_gates_a4():
    results = evaluate_gates("A4", "Who is the owner of the deploy test?")
    passed = [g for g in results if g.passed]
    assert len(passed) >= 2  # "owner" + "test" + "deploy"


# ── Confidence ─────────────────────────────────────────────────────────

def test_confidence_all_pass():
    gates = [GateResult("g1", True, 1.0, ""), GateResult("g2", True, 1.0, "")]
    assert compute_confidence(gates) == 1.0


def test_confidence_half():
    gates = [GateResult("g1", True, 1.0, ""), GateResult("g2", False, 0.0, "")]
    assert compute_confidence(gates) == 0.5


def test_confidence_empty():
    assert compute_confidence([]) == 0.0


# ── make_decision ──────────────────────────────────────────────────────

def test_make_decision_returns_record():
    rec = make_decision("Should we compare the cost of building vs buying a vendor solution?")
    assert isinstance(rec, DecisionRecord)
    assert rec.route.archetype == "A2"
    assert rec.confidence > 0.0  # "compare" + "cost" + "vendor" hit A2 gates
    assert rec.timestamp  # non-empty
    assert len(rec.gate_results) > 0


def test_make_decision_serialization():
    rec = make_decision("How do we scale growth and reduce churn to $10M ARR?")
    d = rec.to_dict()
    assert "question" in d and "route" in d and "gate_results" in d
    j = rec.to_json()
    parsed = json.loads(j)
    assert parsed["route"]["archetype"] == rec.route.archetype


# ── DecisionStore ──────────────────────────────────────────────────────

def test_store_append_and_read():
    with tempfile.TemporaryDirectory() as td:
        store = DecisionStore(Path(td) / "test.jsonl")
        rec1 = make_decision("Should we build or buy?")
        rec2 = make_decision("How do we scale?")

        store.append(rec1)
        store.append(rec2)

        assert store.count() == 2

        all_recs = store.read_all()
        assert len(all_recs) == 2
        assert all_recs[0].question == "Should we build or buy?"
        assert all_recs[1].question == "How do we scale?"
        assert all_recs[0].route.archetype == "A2"
        assert all_recs[1].route.archetype == "A10"


def test_store_empty():
    with tempfile.TemporaryDirectory() as td:
        store = DecisionStore(Path(td) / "empty.jsonl")
        assert store.count() == 0
        assert store.read_all() == []


def test_store_creates_parent_dirs():
    with tempfile.TemporaryDirectory() as td:
        deep = Path(td) / "a" / "b" / "c" / "decisions.jsonl"
        store = DecisionStore(deep)
        store.append(make_decision("Test question"))
        assert store.count() == 1
