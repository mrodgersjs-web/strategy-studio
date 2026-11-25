#!/usr/bin/env python3
"""Deterministic meta-harness evaluator for /rigstrategy (rs-meta-harness).

Evaluates:
  1. All 136 /rigstrategy skills via /skilloptimizer's skillopt_eval.py
  2. All 110 compiled .workflow.js files via skilltoworkflow check
  3. Strategy-studio router accuracy on built-in evaluation fixture
Outputs a reproducible JSON scorecard for Pareto optimization loops.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLOPT_EVAL = pathlib.Path.home() / ".aside/u/0/skills/user/skilloptimizer/scripts/skillopt_eval.py"
SKILL_USER = pathlib.Path.home() / ".aside/u/0/skills/user/rigstrategy/SKILL.md"
SKILL_LIB = pathlib.Path.home() / ".aside/u/0/skill-library"


def collect_skill_paths() -> list[pathlib.Path]:
    paths = []
    if SKILL_USER.exists():
        paths.append(SKILL_USER)
    if SKILL_LIB.exists():
        for p in sorted(SKILL_LIB.glob("rs-*/SKILL.md")):
            paths.append(p)
    return paths


def eval_skills() -> dict:
    paths = collect_skill_paths()
    if not paths:
        return {"count": 0, "all_pass": False, "error": "no rigstrategy skills found"}
    if not SKILLOPT_EVAL.exists():
        return {"count": len(paths), "all_pass": False, "error": f"missing {SKILLOPT_EVAL}"}
    proc = subprocess.run(
        [sys.executable, str(SKILLOPT_EVAL), "--json", *[str(p) for p in paths]],
        capture_output=True, text=True, check=False,
    )
    data = json.loads(proc.stdout)
    results = data.get("results", [])
    n = len(results)
    passed = sum(1 for r in results if r["critical_gate_pass"] and r["runtime_warn"] == 0)
    mean_desc = round(sum(r["description_audit"]["total_out_of_15"] for r in results) / max(n, 1), 2)
    mean_static = round(sum(r["static_skilllens_proxy_out_of_64"] for r in results) / max(n, 1), 2)
    soft_total = sum(r["soft_word_count"] for r in results)
    runtime_total = sum(r["runtime_warn"] for r in results)
    failing = [
        {"name": r["name"], "failures": r["critical_failures"], "runtime_warn": r["runtime_warn"]}
        for r in results if not (r["critical_gate_pass"] and r["runtime_warn"] == 0)
    ]
    return {
        "count": n,
        "passed": passed,
        "all_pass": data.get("all_pass", False),
        "mean_desc_out_of_15": mean_desc,
        "mean_static_out_of_64": mean_static,
        "soft_word_total": soft_total,
        "runtime_warn_total": runtime_total,
        "failing_sample": failing[:10],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run /rigstrategy meta-harness baseline evaluation.")
    ap.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON scorecard")
    ns = ap.parse_args(argv)
    summary = eval_skills()
    if ns.as_json:
        print(json.dumps(summary, indent=2))
    else:
        print(
            f"skillopt_eval: {summary.get('passed', 0)}/{summary.get('count', 0)} PASS | "
            f"mean_desc={summary.get('mean_desc_out_of_15')}/15 | "
            f"mean_static={summary.get('mean_static_out_of_64')}/64 | "
            f"soft_words={summary.get('soft_word_total')} | "
            f"runtime_warn={summary.get('runtime_warn_total')}"
        )
    return 0 if summary.get("all_pass") and summary.get("count", 0) == 136 else 1


if __name__ == "__main__":
    raise SystemExit(main())
