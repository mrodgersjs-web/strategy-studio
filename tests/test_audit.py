import json

from strategy_studio import audit
from strategy_studio.scoring import route


def test_append_chains_and_verifies(tmp_path):
    log = tmp_path / "a" / "audit.jsonl"
    e1 = audit.append(log, route("What is our CAC payback?"), ts="2026-01-01T00:00:00Z")
    e2 = audit.append(log, route("What could go wrong at launch?"), ts="2026-01-01T00:00:01Z")
    assert e1["seq"] == 1 and e1["prev"] == audit.GENESIS
    assert e2["prev"] == e1["hash"]
    assert e1["method"] == "unit-economics" and e2["method"] == "pre-mortem"
    assert e1["scores"]["unit-economics"] == e1["score"]
    assert e1["runner_up"] and e1["methods_version"]
    assert audit.verify(log) == (True, [])


def test_tamper_is_detected(tmp_path):
    log = tmp_path / "audit.jsonl"
    for q in ["Build or buy a CRM?", "Forecast Q3 deals", "Who owns pricing after the reorg?"]:
        audit.append(log, route(q), ts="2026-01-01T00:00:00Z")
    lines = log.read_text().splitlines()
    row = json.loads(lines[1])
    row["method"] = "future-back"
    lines[1] = json.dumps(row, sort_keys=True)
    log.write_text("\n".join(lines) + "\n")
    ok, problems = audit.verify(log)
    assert not ok and any("entry 2: hash mismatch" in p for p in problems)


def test_deleted_entry_breaks_chain(tmp_path):
    log = tmp_path / "audit.jsonl"
    for q in ["Build or buy a CRM?", "Forecast Q3 deals", "Map our value chain"]:
        audit.append(log, route(q), ts="2026-01-01T00:00:00Z")
    lines = log.read_text().splitlines()
    log.write_text("\n".join([lines[0], lines[2]]) + "\n")
    ok, problems = audit.verify(log)
    assert not ok and any("prev hash" in p for p in problems)


def test_same_input_same_hash(tmp_path):
    a = audit.append(tmp_path / "x.jsonl", route("Map our value chain"), ts="2026-01-01T00:00:00Z")
    b = audit.append(tmp_path / "y.jsonl", route("Map our value chain"), ts="2026-01-01T00:00:00Z")
    assert a["hash"] == b["hash"]
