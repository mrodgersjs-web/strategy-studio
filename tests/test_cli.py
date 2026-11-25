import json

from strategy_studio.cli import main, studio


def test_route_writes_audit(tmp_path, capsys):
    log = tmp_path / "audit.jsonl"
    assert studio(["route", "What is our CAC payback?", "--log", str(log), "--json", "--ts", "2026-01-01T00:00:00Z"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["method"] == "unit-economics" and out["audit"]["seq"] == 1
    assert studio(["audit", "verify", "--log", str(log)]) == 0


def test_audit_verify_fails_on_missing_log(tmp_path):
    assert studio(["audit", "verify", "--log", str(tmp_path / "none.jsonl")]) == 1


def test_explain_lists_losers(capsys):
    studio(["explain", "Map our value chain", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["method"] == "wardley-mapping" and len(out["losers"]) == 9


def test_worksheet_forced_method(capsys):
    studio(["worksheet", "anything", "--method", "pre-mortem", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["method"] == "pre-mortem" and out["fields"][0]["field"] == "plan"


def test_worksheet_bad_field_exit_code():
    assert studio(["worksheet", "Map our value chain", "--set", "nope=1"]) == 2


def test_eval_threshold_exit_code(capsys):
    assert studio(["eval", "--min-accuracy", "0.95"]) == 0
    assert "accuracy" in capsys.readouterr().out


def test_legacy_entrypoint_still_works(capsys):
    assert main(["Should we build or buy an eval harness?", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["archetype"] == "A2"
