#!/usr/bin/env python3
"""Deterministic orchestrator harness for /rigstrategy (rs-harness).

Pipeline:
  1. pre-route-redact.sh (fail-closed PII/secret redaction)
  2. strategy-studio deterministic router (no LLM in routing path)
  3. post-route-audit.sh (hash-chained audit log verification)
  4. Stage plan assembly (10 stages x routed method + /strategy doctrine + corpus exemplars/antipatterns)
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import pathlib
import subprocess
import sys

from strategy_studio.cli import studio

ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGES = [
    "frame", "diagnose", "options", "numbers", "stress",
    "commit", "operate", "visual-quality", "antipattern", "learn",
]
AGENTS = [
    "rs-agent-framer", "rs-agent-analyst", "rs-agent-red-teamer",
    "rs-agent-numbers-checker", "rs-agent-visual-judge", "rs-agent-goldfish-verifier",
]


def _load_methods() -> dict[str, dict]:
    data = json.loads((ROOT / "src/strategy_studio/data/methods.json").read_text(encoding="utf-8"))
    return {m["id"]: m for m in data["methods"]}


def _load_strategy_map() -> dict[str, str]:
    p = pathlib.Path.home() / ".aside/u/0/skills/user/strategy/references/method-step-map.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {row["method"]: row["step"] for row in data.get("map", [])}


def _sample_corpus(path: pathlib.Path, limit: int = 5) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            out.append({k: row.get(k) for k in ("id", "query", "title", "url", "license", "antipattern") if row.get(k)})
            if len(out) >= limit:
                break
    return out


def run_harness(question: str, audit_log: str | None = None) -> dict:
    # 1. Pre-route redaction hook
    redact = subprocess.run(
        [str(ROOT / "rigstrategy/hooks/pre-route-redact.sh"), question],
        capture_output=True, text=True, check=False,
    )
    if redact.returncode != 0:
        raise RuntimeError(f"pre-route-redact blocked: {redact.stderr.strip()}")
    redacted_q = redact.stdout.strip()

    # 2. Deterministic routing (no LLM)
    args = ["route", "--json"]
    if audit_log:
        args.extend(["--log", audit_log])
    args.append(redacted_q)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = studio(args)
    if rc != 0:
        raise RuntimeError(f"strategy-studio route failed (rc={rc})")
    routed = json.loads(buf.getvalue())

    # 3. Post-route audit verification hook
    audit_check = subprocess.run(
        [str(ROOT / "rigstrategy/hooks/post-route-audit.sh")],
        input=json.dumps(routed), capture_output=True, text=True, check=False,
    )
    if audit_check.returncode != 0:
        raise RuntimeError(f"post-route-audit blocked: {audit_check.stderr.strip()}")
    audit_verified = json.loads(audit_check.stdout)

    # 4. Assemble method + stage plan + /strategy link + corpus refs
    methods = _load_methods()
    method_id = routed["method"]
    method_def = methods.get(method_id, {})
    strat_map = _load_strategy_map()

    return {
        "schema": "rigstrategy.harness.v1",
        "question_redacted": redacted_q,
        "route": {
            "method": method_id,
            "method_name": routed.get("method_name"),
            "archetype": routed.get("archetype"),
            "score": routed.get("score"),
            "confidence": routed.get("confidence"),
            "explanation": routed.get("explanation"),
        },
        "audit_verified": audit_verified,
        "strategy_doctrine_step": strat_map.get(method_id),
        "method_gates": method_def.get("gates", []),
        "worksheet_fields": method_def.get("worksheet", []),
        "stage_pipeline": [
            {"stage": s, "metaskill": f"rs-{s}", "step_skill": f"rs-{method_id}-{s}", "workflow": f"rigstrategy/workflows/rs-{method_id}-{s}.workflow.js"}
            for s in STAGES
        ],
        "agents": AGENTS,
        "corpus_exemplars": {
            "good_verified_sample": _sample_corpus(ROOT / "corpus/good/verified.jsonl", 3),
            "bad_antipattern_sample": _sample_corpus(ROOT / "corpus/bad/verified.jsonl", 5),
        },
        "gate_d": "drafts-only; no outward send, publish, or spend without Mike approval of exact text",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run the deterministic /rigstrategy harness.")
    ap.add_argument("question", help="Business strategy question to route and plan")
    ap.add_argument("--log", dest="audit_log", default=None, help="Custom audit JSONL path")
    ap.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output")
    ns = ap.parse_args(argv)
    packet = run_harness(ns.question, audit_log=ns.audit_log)
    if ns.as_json:
        print(json.dumps(packet, indent=2))
    else:
        r = packet["route"]
        print(f"Method: {r['method']} ({r['method_name']}, score={r['score']}, confidence={r['confidence']})")
        print(f"Audit:  {packet['audit_verified']['audit_hash']} (chain ok)")
        print(f"Doctrine wrapper: {packet['strategy_doctrine_step']}")
        print("Stages: " + " -> ".join(s["step_skill"] for s in packet["stage_pipeline"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
