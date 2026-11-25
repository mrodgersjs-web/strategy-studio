"""Tests for cell-level strategy playbooks."""
from strategy_studio.playbooks import (
    PLAYBOOKS,
    Playbook,
    PlaybookStep,
    get_playbook,
    list_playbooks,
)


# ── Registry completeness ──────────────────────────────────────────────

def test_all_cells_have_playbooks():
    expected_cells = {
        "cell.org-design", "cell.build-vs-buy", "cell.forecast-risk",
        "cell.go-live", "cell.competitive-position", "cell.pricing-packaging",
        "cell.market-entry", "cell.portfolio-priority", "cell.partnership",
        "cell.growth-scale", "cell.risk-compliance", "cell.ops-efficiency",
        "cell.frame-problem",
    }
    assert expected_cells == set(PLAYBOOKS.keys())


def test_playbook_count():
    assert len(PLAYBOOKS) == 13  # 12 archetypes + default frame-problem


# ── Playbook structure ─────────────────────────────────────────────────

def test_playbook_has_steps():
    for cell, pb in PLAYBOOKS.items():
        assert len(pb.steps) >= 4, f"{cell} has only {len(pb.steps)} steps"
        for step in pb.steps:
            assert step.order > 0
            assert step.name
            assert step.instruction
            assert step.output_field


def test_playbook_has_key_questions():
    for cell, pb in PLAYBOOKS.items():
        assert len(pb.key_questions) >= 3, f"{cell} has only {len(pb.key_questions)} questions"


def test_playbook_has_template():
    for cell, pb in PLAYBOOKS.items():
        assert len(pb.template) >= 3, f"{cell} template has only {len(pb.template)} fields"


def test_playbook_has_pitfalls():
    for cell, pb in PLAYBOOKS.items():
        assert len(pb.pitfalls) >= 2, f"{cell} has only {len(pb.pitfalls)} pitfalls"


def test_step_output_fields_match_template():
    """Every step's output_field should exist in the template."""
    for cell, pb in PLAYBOOKS.items():
        template_fields = set(pb.template.keys())
        for step in pb.steps:
            assert step.output_field in template_fields, \
                f"{cell}: step '{step.name}' output_field '{step.output_field}' not in template"


# ── Lookup ─────────────────────────────────────────────────────────────

def test_get_playbook_existing():
    pb = get_playbook("cell.build-vs-buy")
    assert pb is not None
    assert pb.archetype == "A2"
    assert pb.title == "Build vs Buy Decision"


def test_get_playbook_missing():
    assert get_playbook("cell.nonexistent") is None


def test_list_playbooks():
    pbs = list_playbooks()
    assert len(pbs) == 13
    cells = {p["cell"] for p in pbs}
    assert "cell.build-vs-buy" in cells
    assert "cell.go-live" in cells


# ── Serialization ──────────────────────────────────────────────────────

def test_playbook_to_dict():
    pb = get_playbook("cell.forecast-risk")
    d = pb.to_dict()
    assert "cell" in d
    assert "steps" in d
    assert "template" in d
    assert isinstance(d["steps"], list)


def test_playbook_to_json():
    import json
    pb = get_playbook("cell.pricing-packaging")
    j = pb.to_json()
    parsed = json.loads(j)
    assert parsed["cell"] == "cell.pricing-packaging"
    assert len(parsed["steps"]) >= 4


# ── Specific playbook content ──────────────────────────────────────────

def test_build_vs_buy_has_tco():
    pb = get_playbook("cell.build-vs-buy")
    assert any("tco" in s.output_field for s in pb.steps)


def test_go_live_has_rollback():
    pb = get_playbook("cell.go-live")
    assert any("rollback" in s.name.lower() for s in pb.steps)


def test_growth_has_unit_economics():
    pb = get_playbook("cell.growth-scale")
    assert any("econ" in s.output_field for s in pb.steps)


def test_compliance_has_audit():
    pb = get_playbook("cell.risk-compliance")
    assert any("audit" in s.output_field for s in pb.steps)
