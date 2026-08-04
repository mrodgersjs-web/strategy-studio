from strategy_studio.router import route_question
def test_build_vs_buy():
    r = route_question("Should we build or buy an eval harness?")
    assert r.archetype == "A2" and "build-vs-buy" in r.cell
def test_go_live():
    assert route_question("How do we ship the agent workflow to production?").archetype == "A4"
def test_default():
    assert route_question("What matters here?").cell.startswith("cell.")
