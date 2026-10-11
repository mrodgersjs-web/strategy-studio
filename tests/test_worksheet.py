import pytest

from strategy_studio.methods import load_methods
from strategy_studio.scoring import route
from strategy_studio.worksheet import build_worksheet, expected_value, render_markdown, unit_economics

MS = load_methods()


def test_worksheet_matches_method_fields():
    d = route("Why do customers switch away from us?", MS)
    ws = build_worksheet(d, MS.get(d.method_id), {"job_statement": "When I close the month, I want..."})
    assert ws["method"] == "jobs-to-be-done"
    assert [f["field"] for f in ws["fields"]] == [f.field for f in MS.get("jobs-to-be-done").worksheet]
    assert ws["completion"] == "1/6"
    assert ws["gates"][0] == {"gate": "job-statement", "passed": False}
    md = render_markdown(ws)
    assert "# Jobs to be done worksheet" in md and "When I close the month" in md


def test_unknown_field_rejected():
    d = route("Map our value chain", MS)
    with pytest.raises(KeyError, match="nope"):
        build_worksheet(d, MS.get(d.method_id), {"nope": "x"})


def test_unit_economics_math():
    r = unit_economics({"revenue_per_unit": "40", "variable_cost_per_unit": "25", "cac": "$120", "retention": "18"})
    assert r["contribution_margin"] == 15.0 and r["ltv"] == 270.0
    assert r["payback_periods"] == 8.0 and r["ltv_to_cac"] == 2.25 and r["flags"] == []


def test_unit_economics_flags():
    neg = unit_economics({"revenue_per_unit": "10", "variable_cost_per_unit": "12", "cac": "50", "retention": "12"})
    assert neg["payback_periods"] is None and "negative contribution margin" in neg["flags"][0]
    slow = unit_economics({"revenue_per_unit": "10", "variable_cost_per_unit": "8", "cac": "50", "retention": "12"})
    assert slow["payback_periods"] == 25.0 and "never paid back" in slow["flags"][0]
    assert unit_economics({"cac": "5"})["status"] == "incomplete"


def test_expected_value_percent_and_fraction():
    a = expected_value({"probability": "30%", "upside": "1000", "downside": "200"})
    b = expected_value({"probability": "0.3", "upside": "1000", "downside": "200"})
    assert a["expected_value"] == b["expected_value"] == 160.0 and a["positive"]


def test_calculator_attached_to_worksheet():
    d = route("Which bets should we fund?", MS)
    ws = build_worksheet(d, MS.get("real-options"), {"probability": "0.1", "upside": "100", "downside": "50"})
    assert ws["calculator"]["expected_value"] == -35.0 and ws["calculator"]["positive"] is False
