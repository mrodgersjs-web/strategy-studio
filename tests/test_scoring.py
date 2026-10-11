import pytest

from strategy_studio.methods import load_methods
from strategy_studio.scoring import explain_losers, route

MS = load_methods()


@pytest.mark.parametrize(
    "q,expected",
    [
        ("What should our 2035 future state look like?", "future-back"),
        ("Competitors copy us; how do we differentiate?", "ten-types"),
        ("Why do customers switch away from us?", "jobs-to-be-done"),
        ("We launch Monday. What could go wrong?", "pre-mortem"),
        ("Map the value chain of our data platform.", "wardley-mapping"),
        ("What is our CAC payback?", "unit-economics"),
    ],
)
def test_routes_named_methods(q, expected):
    assert route(q, MS).method_id == expected


def test_deterministic_and_order_stable():
    q = "Should we build or buy, and is it profitable per customer?"
    a, b = route(q, MS), route(q, MS)
    assert a.to_dict() == b.to_dict()
    scores = [c.score for c in a.ranking]
    assert scores == sorted(scores, reverse=True)


def test_scored_explanation_names_matched_terms():
    d = route("Should we build or buy an eval harness?", MS)
    assert d.method_id == "build-vs-buy"
    assert d.score == 5 and "'build or buy' (+5)" in d.explanation
    assert d.confidence == "clear" and d.margin == 1.0


def test_longer_phrase_absorbs_its_parts():
    d = route("build or buy?", MS)
    top = d.ranking[0]
    assert [p for p, _ in top.matched] == ["build or buy"]


def test_plural_and_hyphen_matching():
    assert route("Is the go live plan ready?", MS).method_id == "pre-mortem"
    assert route("Which bets get funded?", MS).method_id == "real-options"


def test_fallback_when_nothing_matches():
    d = route("What matters here?", MS)
    assert d.method_id == "frame-problem" and d.confidence == "fallback" and d.score == 0
    assert all(lo["reason"] == "no keyword matched" for lo in explain_losers(d))


def test_tie_break_is_reported():
    d = route("Should we build or buy, and what could go wrong?", MS)
    assert d.confidence == "tie-break" and d.margin == 0.0
    # build-vs-buy and pre-mortem share priority 1 -> id order decides
    assert d.method_id == "build-vs-buy"
    loser = next(lo for lo in explain_losers(d) if lo["method"] == "pre-mortem")
    assert "tied at 5" in loser["reason"] and loser["matched"] == ["what could go wrong"]


def test_losers_explain_score_gap():
    d = route("What is our CAC payback, and should we launch?", MS)
    assert d.method_id == "unit-economics"
    pm = next(lo for lo in explain_losers(d) if lo["method"] == "pre-mortem")
    assert pm["reason"] == f"scored 3 vs {d.score} (gap {d.score - 3})"
    assert len(explain_losers(d)) == len(MS.methods) - 2  # all except winner and fallback


def test_empty_question_rejected():
    with pytest.raises(ValueError):
        route("   ", MS)
