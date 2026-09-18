"""Offline tests for the Jev head. The provider is always mocked here.

These tests pin the contract:
- route_question() stays deterministic and untouched (conftest depends on it)
- route_question_jev() succeeds above both floors
- abstains (falls back, labelled) below either floor
- fails OPEN on provider errors -- the regex answer is used, never an exception
- choice option count stays inside the 255-option Jev cap
"""
from __future__ import annotations

import pytest

from strategy_studio import jev_head
from strategy_studio.jev_head import JevError, route_question_jev
from strategy_studio.router import route_question


def _body(choice: str, probs: dict) -> dict:
    return {"model": "jev-latest", "answers": {"archetype": {"type": "choice", "choice": choice, "probabilities": probs}}}


def test_options_inside_jev_choice_cap():
    archs = jev_head._archetypes()
    assert 0 < len(archs) <= 255
    assert all(set(a) == {"id", "desc"} for a in archs)


def test_success_above_floors(monkeypatch):
    def fake_ask(state, questions, **kw):
        return _body("A2", {"A2": 0.72, "A6": 0.18, "A1": 0.10})

    monkeypatch.setattr(jev_head, "ask_jev", fake_ask)
    monkeypatch.setattr(jev_head, "_log", lambda meta: None)
    route, meta = route_question_jev("Should we build or buy an eval harness?", log=False)
    assert meta["source"] == "jev"
    assert route.archetype == "A2"
    assert route.cell == "cell.build-vs-buy"
    assert meta["top1"] >= 0.40 and meta["margin"] >= 0.08
    assert meta["probabilities"]["A2"] == pytest.approx(0.72, abs=1e-6)


def test_abstain_below_top1_floor_falls_open(monkeypatch):
    def fake_ask(state, questions, **kw):
        return _body("A10", {"A10": 0.35, "A12": 0.30, "A1": 0.25})  # top1 0.35 < 0.40 floor

    monkeypatch.setattr(jev_head, "ask_jev", fake_ask)
    route, meta = route_question_jev("How do we scale the platform team?")
    assert meta["source"] == "jev-abstained"
    # The fallback is the deterministic router, so the conftest contract holds.
    assert route == route_question("How do we scale the platform team?")


def test_abstain_below_margin_floor_falls_open(monkeypatch):
    def fake_ask(state, questions, **kw):
        return _body("A10", {"A10": 0.60, "A12": 0.56, "A1": 0.05})  # top1 ok, margin 0.04 < 0.08

    monkeypatch.setattr(jev_head, "ask_jev", fake_ask)
    route, meta = route_question_jev("How do we scale the platform team?")
    assert meta["source"] == "jev-abstained"
    assert meta["margin"] < 0.08
    assert route == route_question("How do we scale the platform team?")


def test_provider_error_fails_open_never_raises(monkeypatch):
    def boom(state, questions, **kw):
        raise JevError("HTTP 401: bad key")

    monkeypatch.setattr(jev_head, "ask_jev", boom)
    q = "Should we partner with a reseller ecosystem?"
    route, meta = route_question_jev(q)
    assert meta["source"] == "regex-failopen"
    assert "401" in meta["error"]
    assert route == route_question(q)
    assert route.archetype == "A9"


def test_route_question_untouched_by_head(monkeypatch):
    """The deterministic contract is load-bearing; the head must not perturb it."""
    monkeypatch.setenv("STRATEGY_JEV_TOP1_FLOOR", "0.99")
    monkeypatch.setenv("STRATEGY_JEV_MARGIN_FLOOR", "0.99")
    assert route_question("Should we build or buy?").archetype == "A2"
    assert route_question("How do we scale?").archetype == "A10"
    assert route_question("Should we partner?").archetype == "A9"
    assert route_question("unrelated words nothing matches").archetype == "A1"


def test_malformed_answer_fails_open(monkeypatch):
    monkeypatch.setattr(jev_head, "ask_jev", lambda s, q, **kw: {"model": "jev-latest", "answers": {}})
    route, meta = route_question_jev("What is our pricing?", log=False)
    assert meta["source"] == "regex-failopen"
    assert route == route_question("What is our pricing?")
