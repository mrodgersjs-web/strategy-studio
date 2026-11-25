"""Integration tests — full pipeline: routing + gates + playbooks."""
import json
import tempfile
from pathlib import Path

from strategy_studio.integration import StrategyResponse, analyze_batch, analyze_question
from strategy_studio.records import DecisionStore


# ── analyze_question ───────────────────────────────────────────────────

def test_analyze_question_returns_response():
    r = analyze_question("Should we compare the cost of building vs buying?")
    assert isinstance(r, StrategyResponse)
    assert r.route.archetype == "A2"
    assert r.playbook is not None
    assert r.playbook.title == "Build vs Buy Decision"
    assert r.confidence > 0
    assert r.timestamp


def test_analyze_question_has_gates():
    r = analyze_question("Should we compare the cost of building vs buying?")
    assert len(r.gate_results) > 0
    assert any(g.passed for g in r.gate_results)


def test_analyze_question_has_playbook_steps():
    r = analyze_question("Should we compare the cost of building vs buying?")
    assert len(r.playbook.steps) >= 4
    assert r.playbook.steps[0].order == 1


def test_analyze_question_default_fallback():
    r = analyze_question("What matters here?")
    assert r.route.archetype == "A1"
    assert r.route.cell == "cell.frame-problem"
    assert r.playbook.title == "Problem Framing"


def test_analyze_question_serialization():
    r = analyze_question("How do we scale growth?")
    d = r.to_dict()
    assert "question" in d
    assert "route" in d
    assert "playbook" in d
    assert "confidence" in d
    j = r.to_json()
    parsed = json.loads(j)
    assert parsed["route"]["archetype"] == "A10"


def test_analyze_question_text_output():
    r = analyze_question("Should we build or buy?")
    text = r.format_text()
    assert "Archetype" in text
    assert "Playbook" in text
    assert "Steps" in text
    assert "Pitfalls" in text


# ── analyze_batch ──────────────────────────────────────────────────────

def test_analyze_batch_multiple():
    questions = [
        "Should we build or buy?",
        "How do we scale?",
        "Should we partner with Snowflake?",
    ]
    results = analyze_batch(questions)
    assert len(results) == 3
    assert results[0].route.archetype == "A2"
    assert results[1].route.archetype == "A10"
    assert results[2].route.archetype == "A9"


def test_analyze_batch_skips_blanks():
    results = analyze_batch(["Should we build?", "", "  ", "How do we scale?"])
    assert len(results) == 2


def test_analyze_batch_with_store():
    store = DecisionStore(Path(tempfile.mkdtemp()) / "test.jsonl")
    results = analyze_batch(["Should we build?", "How do we scale?"], store=store)
    assert len(results) == 2
    assert store.count() == 2


# ── All archetypes produce playbooks ───────────────────────────────────

def test_all_archetypes_have_playbooks():
    questions = {
        "A1": "What headcount do we need for the platform team?",
        "A2": "Should we compare the cost of building vs buying?",
        "A3": "What's the probability we hit $10M ARR?",
        "A4": "How do we ship the agent workflow to production?",
        "A5": "How do we compete with OpenAI on agent tooling?",
        "A6": "What should we price the enterprise tier at?",
        "A7": "Should we enter the European market?",
        "A8": "How should we prioritize our product roadmap?",
        "A9": "Should we partner with Snowflake?",
        "A10": "How do we scale growth and reduce churn?",
        "A11": "Do we need SOC 2 compliance?",
        "A12": "What's the bottleneck in our onboarding workflow?",
    }
    for expected_arch, question in questions.items():
        r = analyze_question(question)
        assert r.route.archetype == expected_arch, \
            f"Expected {expected_arch} for '{question}', got {r.route.archetype}"
        assert r.playbook is not None, \
            f"No playbook for {expected_arch} ({r.route.cell})"
        assert len(r.playbook.steps) >= 4


# ── E2E: all archetypes through full pipeline with metadata ────────────

def test_e2e_all_archetypes_with_metadata():
    """Every archetype produces a full response with route + gates + playbook + metadata."""
    questions = {
        "A1": "What headcount do we need for the platform team?",
        "A2": "Should we compare the cost of building vs buying?",
        "A3": "What's the probability we hit $10M ARR?",
        "A4": "How do we ship the agent workflow to production?",
        "A5": "How do we compete with OpenAI on agent tooling?",
        "A6": "What should we price the enterprise tier at?",
        "A7": "Should we enter the European market?",
        "A8": "How should we prioritize our product roadmap?",
        "A9": "Should we partner with Snowflake?",
        "A10": "How do we scale growth and reduce churn?",
        "A11": "Do we need SOC 2 compliance?",
        "A12": "What's the bottleneck in our onboarding workflow?",
    }
    for expected_arch, question in questions.items():
        r = analyze_question(question)
        assert r.route.archetype == expected_arch, f"{expected_arch}: got {r.route.archetype}"
        assert r.playbook is not None, f"{expected_arch}: no playbook"
        assert r.metadata is not None, f"{expected_arch}: no metadata"
        assert r.metadata.complexity in ("low","medium","high","critical")
        assert r.metadata.stakeholders >= 1
        assert len(r.gate_results) > 0
        d = r.to_dict()
        assert "archetype_meta" in d, f"{expected_arch}: archetype_meta missing from to_dict"
        assert d["archetype_meta"]["complexity"] == r.metadata.complexity
