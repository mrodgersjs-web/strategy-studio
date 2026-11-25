from strategy_studio.evaluate import evaluate, load_labelled

# The bundled labelled set is hand-written and the keyword weights were tuned against it,
# so this is a regression check, not a generalisation benchmark.
MIN_ACCURACY = 0.95


def test_labelled_set_covers_every_method():
    from strategy_studio.methods import load_methods

    rows = load_labelled()
    assert len(rows) >= 40
    assert {r["expected"] for r in rows} == set(load_methods().ids)


def test_accuracy_on_labelled_set():
    rep = evaluate(load_labelled())
    assert rep["accuracy"] >= MIN_ACCURACY, rep["misses"]
    assert rep["total"] == rep["correct"] + len(rep["misses"])


def test_eval_detects_wrong_labels(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text('{"question": "What is our CAC payback?", "expected": "future-back"}\n')
    rep = evaluate(load_labelled(p))
    assert rep["accuracy"] == 0.0 and rep["misses"][0]["got"] == "unit-economics"


# The held-out set was written after the keyword weights were last changed and was not
# used for tuning. First measurement: 20/22. The floor leaves room for one more miss.
HOLDOUT_MIN = 0.85


def test_accuracy_on_holdout_set():
    rep = evaluate(load_labelled(bundled="holdout"))
    assert rep["total"] >= 20
    assert rep["accuracy"] >= HOLDOUT_MIN, rep["misses"]
