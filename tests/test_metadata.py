"""Tests for archetype metadata."""
from strategy_studio.metadata import METADATA, ArchetypeMeta, get_metadata, list_metadata

def test_all_archetypes_have_metadata():
    expected = {"A1","A2","A3","A4","A5","A6","A7","A8","A9","A10","A11","A12"}
    assert set(METADATA.keys()) == expected

def test_metadata_fields_populated():
    for arch, m in METADATA.items():
        assert m.complexity in ("low","medium","high","critical"), f"{arch} bad complexity"
        assert m.stakeholders >= 1
        assert m.reversibility in ("easy","moderate","hard","irreversible")
        assert m.decision_speed in ("fast","deliberate","slow")
        assert len(m.recommended_tools) >= 2
        assert m.description

def test_get_metadata_existing():
    m = get_metadata("A2")
    assert m is not None and m.archetype == "A2"

def test_get_metadata_missing():
    assert get_metadata("A99") is None

def test_list_metadata():
    items = list_metadata()
    assert len(items) == 12

def test_metadata_serialization():
    d = get_metadata("A11").to_dict()
    assert d["complexity"] == "critical"
    assert d["reversibility"] == "irreversible"
