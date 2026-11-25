"""Tests for /rigstrategy hooks, harness, corpus gate, and skill generator."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_hooks_exist_and_are_executable():
    for name in ("pre-route-redact", "post-route-audit", "pre-done-jev", "post-run-learn"):
        p = ROOT / "rigstrategy" / "hooks" / f"{name}.sh"
        assert p.exists(), f"missing hook {p}"
        assert p.stat().st_mode & 0o111, f"hook not executable: {p}"


def test_pre_route_redact_strips_sensitive_data_and_blocks_empty():
    hook = str(ROOT / "rigstrategy/hooks/pre-route-redact.sh")
    raw = "Email alice@example.com with key sk-1234567890abcdefghijklmno from /Users/alice/doc.md"
    proc = subprocess.run([hook, raw], capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    out = proc.stdout.strip()
    assert "alice@example.com" not in out
    assert "sk-1234567890abcdefghijklmno" not in out
    assert "/Users/alice/" not in out
    assert "[REDACTED_EMAIL]" in out
    assert "[REDACTED_SECRET]" in out
    assert "[REDACTED_HOME]/" in out

    empty = subprocess.run([hook, "   "], capture_output=True, text=True, check=False)
    assert empty.returncode != 0


def test_harness_end_to_end_and_post_run_learn(tmp_path):
    audit_log = tmp_path / "audit.jsonl"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "rigstrategy/harness.py"),
            "Should we build our own CRM or buy HubSpot? Contact bob@example.com",
            "--log",
            str(audit_log),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    packet = json.loads(proc.stdout)
    assert packet["schema"] == "rigstrategy.harness.v1"
    assert "bob@example.com" not in packet["question_redacted"]
    assert packet["route"]["method"] == "build-vs-buy"
    assert packet["audit_verified"]["ok"] is True
    assert len(packet["stage_pipeline"]) == 10
    assert len(packet["agents"]) == 6
    assert len(packet["worksheet_fields"]) > 0

    ledger = tmp_path / "run-ledger.jsonl"
    learn = subprocess.run(
        [
            str(ROOT / "rigstrategy/hooks/post-run-learn.sh"),
            packet["route"]["method"],
            "frame",
            packet["audit_verified"]["audit_hash"],
            "PASS",
            "smoke test",
        ],
        env={**dict(__import__("os").environ), "RIGSTRATEGY_LEDGER": str(ledger)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert learn.returncode == 0, learn.stderr
    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["method"] == "build-vs-buy"


def test_corpus_manifest_has_calibrated_and_strict_counts():
    man = json.loads((ROOT / "corpus/MANIFEST.json").read_text(encoding="utf-8"))
    assert man["good"]["count"] >= 300
    assert man["bad"]["count"] >= 300
    v1 = man["v1_calibrated"]
    assert v1["confirmed_good_total"] >= 1000
    assert v1["confirmed_bad_total"] >= 300
