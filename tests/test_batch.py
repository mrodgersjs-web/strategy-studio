"""Tests for batch routing and archetype analytics."""
import tempfile
from pathlib import Path

from strategy_studio.batch import (
    ArchetypeStats,
    StoreSummary,
    route_batch,
    route_from_file,
    summarize_store,
)
from strategy_studio.records import DecisionStore, make_decision


# ── Batch routing ──────────────────────────────────────────────────────

def test_route_batch_basic():
    questions = [
        "Should we build or buy?",
        "How do we scale to $10M?",
        "Should we partner with Snowflake?",
    ]
    records = route_batch(questions)
    assert len(records) == 3
    assert records[0].route.archetype == "A2"
    assert records[1].route.archetype == "A10"
    assert records[2].route.archetype == "A9"


def test_route_batch_skips_blanks():
    questions = ["Should we build?", "", "  ", "How do we scale?"]
    records = route_batch(questions)
    assert len(records) == 2


def test_route_batch_empty():
    assert route_batch([]) == []


def test_route_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Should we build or buy?\n")
        f.write("How do we scale?\n")
        f.write("\n")  # blank line
        f.write("Should we partner?\n")
        f.flush()
        records = route_from_file(f.name)
    assert len(records) == 3


# ── Store summary ──────────────────────────────────────────────────────

def _populate_store(n: int = 10) -> DecisionStore:
    """Create a temp store with N diverse decisions."""
    store = DecisionStore(Path(tempfile.mkdtemp()) / "test.jsonl")
    questions = [
        "Should we compare the cost of building vs buying?",
        "How do we scale growth and reduce churn?",
        "Should we partner with Snowflake?",
        "How do we compete with OpenAI?",
        "Should we enter the European market?",
        "What should we price the enterprise tier at?",
        "How should we prioritize our product roadmap?",
        "Do we need SOC 2 compliance?",
        "What's the bottleneck in our onboarding workflow?",
        "Should we hire a VP of Engineering?",
    ]
    for i in range(n):
        store.append(make_decision(questions[i % len(questions)]))
    return store


def test_summarize_store_counts():
    store = _populate_store(10)
    summary = summarize_store(store)
    assert summary.total_records == 10
    assert sum(summary.archetype_distribution.values()) == 10


def test_summarize_store_avg_confidence():
    store = _populate_store(10)
    summary = summarize_store(store)
    assert 0.0 <= summary.avg_confidence <= 1.0


def test_summarize_store_histogram():
    store = _populate_store(10)
    summary = summarize_store(store)
    # All buckets should exist
    assert set(summary.confidence_histogram.keys()) == {
        "0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"
    }
    # Total across buckets should equal total records
    assert sum(summary.confidence_histogram.values()) == 10


def test_summarize_store_per_archetype():
    store = _populate_store(10)
    summary = summarize_store(store)
    archetypes = {a.archetype for a in summary.per_archetype}
    # Should have multiple archetypes from our diverse questions
    assert len(archetypes) >= 3


def test_summarize_store_gate_pass_rates():
    store = _populate_store(10)
    summary = summarize_store(store)
    for name, rate in summary.gate_pass_rates.items():
        assert 0.0 <= rate <= 1.0


def test_summarize_store_empty():
    store = DecisionStore(Path(tempfile.mkdtemp()) / "empty.jsonl")
    summary = summarize_store(store)
    assert summary.total_records == 0
    assert summary.avg_confidence == 0.0
    assert summary.per_archetype == []


def test_summarize_store_serialization():
    store = _populate_store(5)
    summary = summarize_store(store)
    d = summary.to_dict()
    assert "total_records" in d
    assert "archetype_distribution" in d
    assert "confidence_histogram" in d
    assert "per_archetype" in d
    assert "gate_pass_rates" in d
    j = summary.to_json()
    import json
    parsed = json.loads(j)
    assert parsed["total_records"] == 5


def test_archetype_stats_cells():
    store = _populate_store(10)
    summary = summarize_store(store)
    for a in summary.per_archetype:
        assert isinstance(a.cells, dict)
        assert all(isinstance(v, int) for v in a.cells.values())


def test_archetype_stats_top_questions():
    store = _populate_store(10)
    summary = summarize_store(store)
    for a in summary.per_archetype:
        assert isinstance(a.top_questions, list)
        assert len(a.top_questions) <= 5
