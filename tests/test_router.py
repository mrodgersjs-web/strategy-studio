"""Tests for the 12-archetype strategy router."""
from strategy_studio.router import route_question, list_archetypes, to_dict


# --- A1: Org design ---
def test_org_design():
    r = route_question("Should we hire a VP of Engineering or promote internally?")
    assert r.archetype == "A1" and r.cell == "cell.org-design"


def test_team_structure():
    r = route_question("What headcount do we need for the platform team?")
    assert r.archetype == "A1"


# --- A2: Build vs buy ---
def test_build_vs_buy():
    r = route_question("Should we build or buy an eval harness?")
    assert r.archetype == "A2" and "build-vs-buy" in r.cell


def test_outsource():
    r = route_question("Should we outsource the data pipeline?")
    assert r.archetype == "A2"


def test_vendor():
    r = route_question("Which vendor should we choose for auth?")
    assert r.archetype == "A2"


# --- A3: Forecast & risk ---
def test_forecast():
    r = route_question("What's the probability we hit $10M ARR by December?")
    assert r.archetype == "A3" and "forecast" in r.cell


def test_calibration():
    r = route_question("How do we calibrate our sales forecast?")
    assert r.archetype == "A3"


# --- A4: Go-live ---
def test_go_live():
    r = route_question("How do we ship the agent workflow to production?")
    assert r.archetype == "A4"


def test_deploy():
    r = route_question("When should we deploy the new pricing engine?")
    assert r.archetype == "A4"


def test_rollout():
    r = route_question("Plan the rollout for the enterprise tier")
    assert r.archetype == "A4"


# --- A5: Competitive positioning ---
def test_competitive():
    r = route_question("How do we compete with OpenAI on agent tooling?")
    assert r.archetype == "A5" and "competitive" in r.cell


def test_moat():
    r = route_question("What's our moat against competitors?")
    assert r.archetype == "A5"


def test_differentiation():
    r = route_question("How do we differentiate from LangChain?")
    assert r.archetype == "A5"


# --- A6: Pricing ---
def test_pricing():
    r = route_question("What should we price the enterprise tier at?")
    assert r.archetype == "A6" and "pricing" in r.cell


def test_packaging():
    r = route_question("How should we package the tiers?")
    assert r.archetype == "A6"


# --- A7: Market entry ---
def test_market_entry():
    r = route_question("Should we enter the European market?")
    assert r.archetype == "A7" and "market-entry" in r.cell


def test_expand():
    r = route_question("How do we expand into healthcare vertical?")
    assert r.archetype == "A7"


# --- A8: Portfolio prioritization ---
def test_portfolio():
    r = route_question("How should we prioritize our product roadmap?")
    assert r.archetype == "A8" and "portfolio" in r.cell


def test_backlog():
    r = route_question("Help me sequence the backlog for maximum impact")
    assert r.archetype == "A8"


# --- A9: Partnerships ---
def test_partner():
    r = route_question("Should we partner with Snowflake for the data layer?")
    assert r.archetype == "A9" and "partnership" in r.cell


def test_ecosystem():
    r = route_question("How do we build an ecosystem of integrations?")
    assert r.archetype == "A9"


# --- A10: Growth ---
def test_growth():
    r = route_question("How do we scale from $1M to $10M ARR?")
    assert r.archetype == "A10" and "growth" in r.cell


def test_retention():
    r = route_question("Our churn is 8% — how do we improve retention?")
    assert r.archetype == "A10"


def test_cohort():
    r = route_question("Analyze cohort retention for Q2")
    assert r.archetype == "A10"


# --- A11: Risk & compliance ---
def test_compliance():
    r = route_question("Do we need SOC 2 compliance before enterprise sales?")
    assert r.archetype == "A11" and "risk" in r.cell


def test_gdpr():
    r = route_question("How do we handle GDPR for EU customers?")
    assert r.archetype == "A11"


# --- A12: Ops efficiency ---
def test_automation():
    r = route_question("Which processes should we automate first?")
    assert r.archetype == "A12" and "ops" in r.cell


def test_bottleneck():
    r = route_question("What's the bottleneck in our onboarding workflow?")
    assert r.archetype == "A12"


# --- Default fallback ---
def test_default():
    r = route_question("What matters here?")
    assert r.cell == "cell.frame-problem" and r.archetype == "A1"


def test_empty():
    r = route_question("")
    assert r.cell == "cell.frame-problem"


# --- Utility functions ---
def test_list_archetypes():
    archetypes = list_archetypes()
    archetype_ids = {a["archetype"] for a in archetypes}
    assert archetype_ids == {"A1", "A2", "A3", "A4", "A5", "A6",
                             "A7", "A8", "A9", "A10", "A11", "A12"}


def test_to_dict():
    r = route_question("Should we build or buy?")
    d = to_dict(r)
    assert isinstance(d, dict)
    assert "archetype" in d and "cell" in d and "gates" in d


# --- Priority: specific before general ---
def test_pricing_over_org():
    """'price the team' should match A6 (pricing) not A1 (org/team)."""
    r = route_question("How should we price the team tier?")
    assert r.archetype == "A6"


def test_compliance_over_ops():
    """'compliance workflow' should match A11 (compliance) not A12 (workflow)."""
    r = route_question("Build a compliance workflow for SOC 2")
    assert r.archetype == "A11"
