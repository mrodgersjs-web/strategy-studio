import json

import pytest

from strategy_studio.methods import MethodsError, load_methods

REQUIRED = {"future-back", "ten-types", "jobs-to-be-done", "pre-mortem", "wardley-mapping", "unit-economics"}


def test_bundled_methods_cover_required_set():
    ms = load_methods()
    assert REQUIRED <= set(ms.ids)
    assert ms.fallback == "frame-problem"
    assert len(ms.version) == 12


def test_every_method_has_worksheet_and_gates():
    for m in load_methods().methods:
        assert m.worksheet and m.gates and m.summary
        assert len({f.field for f in m.worksheet}) == len(m.worksheet)


def _write(tmp_path, data):
    p = tmp_path / "m.json"
    p.write_text(json.dumps(data))
    return p


def test_rejects_duplicate_ids(tmp_path):
    m = {"id": "x", "name": "X", "archetype": "A1", "priority": 1, "summary": "s", "keywords": {"a": 1}, "gates": ["g"],
         "worksheet": [{"field": "f", "prompt": "p"}]}
    with pytest.raises(MethodsError, match="duplicate"):
        load_methods(_write(tmp_path, {"schema": "strategy-studio.methods.v1", "fallback": "x", "methods": [m, m]}))


def test_rejects_bad_weight_and_fallback(tmp_path):
    m = {"id": "x", "name": "X", "archetype": "A1", "priority": 1, "summary": "s", "keywords": {"a": 0}, "gates": ["g"],
         "worksheet": [{"field": "f", "prompt": "p"}]}
    with pytest.raises(MethodsError, match="positive int"):
        load_methods(_write(tmp_path, {"schema": "strategy-studio.methods.v1", "fallback": "x", "methods": [m]}))
    m["keywords"] = {"a": 1}
    with pytest.raises(MethodsError, match="fallback"):
        load_methods(_write(tmp_path, {"schema": "strategy-studio.methods.v1", "fallback": "nope", "methods": [m]}))


def test_version_changes_when_data_changes(tmp_path):
    m = {"id": "x", "name": "X", "archetype": "A1", "priority": 1, "summary": "s", "keywords": {"a": 1}, "gates": ["g"],
         "worksheet": [{"field": "f", "prompt": "p"}]}
    base = {"schema": "strategy-studio.methods.v1", "fallback": "x", "methods": [m]}
    v1 = load_methods(_write(tmp_path, base)).version
    m["keywords"] = {"a": 2}
    v2 = load_methods(_write(tmp_path, base)).version
    assert v1 != v2
