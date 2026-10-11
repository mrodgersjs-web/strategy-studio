import json
import os
import subprocess
import sys

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


@pytest.mark.parametrize("field", ["revenue_per_unit", "variable_cost_per_unit", "cac", "retention"])
@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_unit_economics_nonfinite_inputs_are_incomplete(field, value):
    answers = {"revenue_per_unit": "40", "variable_cost_per_unit": "25", "cac": "120", "retention": "18"}
    answers[field] = value
    r = unit_economics(answers)
    assert r == {"status": "incomplete", "missing": [field]}


@pytest.mark.parametrize(
    "answers",
    [
        {"revenue_per_unit": "1e308", "variable_cost_per_unit": "0", "cac": "1", "retention": "2"},  # multiplication
        {"revenue_per_unit": "1e308", "variable_cost_per_unit": "-1e308", "cac": "1", "retention": "1"},  # subtraction
        {"revenue_per_unit": "1e308", "variable_cost_per_unit": "0", "cac": "1e-308", "retention": "1"},  # division
    ],
)
def test_unit_economics_finite_overflow_is_invalid(answers):
    r = unit_economics(answers)
    assert r == {"status": "invalid", "error": "calculator result must be finite"}


@pytest.mark.parametrize("field", ["upside", "downside"])
@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_expected_value_nonfinite_amount_inputs_are_incomplete(field, value):
    answers = {"probability": "0.5", "upside": "1000", "downside": "200"}
    answers[field] = value
    r = expected_value(answers)
    assert r == {"status": "incomplete", "missing": [field]}


@pytest.mark.parametrize("probability", ["nan", "inf", "-inf"])
def test_expected_value_nonfinite_probability_stays_invalid(probability):
    r = expected_value({"probability": probability, "upside": "1000", "downside": "200"})
    assert r == {"status": "invalid", "error": "probability must be between 0 and 1 (or 0-100%)"}


def test_expected_value_finite_extreme_can_remain_finite():
    r = expected_value({"probability": "0.5", "upside": "1e308", "downside": "1e308"})
    assert r == {"status": "ok", "probability": 0.5, "expected_value": 0.0, "positive": False}


def test_cli_json_is_strict_for_invalid_calculator_results(tmp_path):
    env = {**os.environ, "PYTHONPATH": "src", "HOME": str(tmp_path)}
    cmd = [
        sys.executable,
        "-m",
        "strategy_studio.cli",
        "worksheet",
        "synthetic unit economics question",
        "--method",
        "unit-economics",
        "--set",
        "revenue_per_unit=1e308",
        "--set",
        "variable_cost_per_unit=0",
        "--set",
        "cac=1",
        "--set",
        "retention=2",
        "--json",
    ]
    out = subprocess.check_output(cmd, text=True, env=env)
    parsed = json.loads(out)
    assert parsed["calculator"] == {"status": "invalid", "error": "calculator result must be finite"}


def test_cli_json_is_strict_for_nonfinite_inputs(tmp_path):
    env = {**os.environ, "PYTHONPATH": "src", "HOME": str(tmp_path)}
    cmd = [
        sys.executable,
        "-m",
        "strategy_studio.cli",
        "worksheet",
        "synthetic unit economics question",
        "--method",
        "unit-economics",
        "--set",
        "revenue_per_unit=nan",
        "--set",
        "variable_cost_per_unit=25",
        "--set",
        "cac=120",
        "--set",
        "retention=18",
        "--json",
    ]
    out = subprocess.check_output(cmd, text=True, env=env)
    parsed = json.loads(out)
    assert parsed["calculator"] == {"status": "incomplete", "missing": ["revenue_per_unit"]}
