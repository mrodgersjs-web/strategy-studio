"""Accuracy check of the router against a labelled question set."""
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from .methods import MethodSet, load_methods
from .scoring import route

BUNDLED = {"labelled": "data/labelled_questions.jsonl", "holdout": "data/holdout_questions.jsonl"}


def load_labelled(path: str | Path | None = None, bundled: str = "labelled") -> list[dict]:
    """Load a question set: a JSONL path, or a bundled set ("labelled" = tuning set, "holdout")."""
    if path is None:
        text = resources.files("strategy_studio").joinpath(BUNDLED[bundled]).read_text()
    else:
        text = Path(path).read_text()
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    for r in rows:
        if "question" not in r or "expected" not in r:
            raise ValueError(f"labelled row missing question/expected: {r}")
    return rows


def evaluate(rows: list[dict], methods: MethodSet | None = None) -> dict:
    methods = methods or load_methods()
    unknown = sorted({r["expected"] for r in rows} - set(methods.ids))
    if unknown:
        raise ValueError(f"labelled set uses unknown method ids: {unknown}")
    misses = []
    per_method: dict[str, dict[str, int]] = {}
    for r in rows:
        d = route(r["question"], methods)
        stats = per_method.setdefault(r["expected"], {"total": 0, "correct": 0})
        stats["total"] += 1
        if d.method_id == r["expected"]:
            stats["correct"] += 1
        else:
            misses.append({"question": r["question"], "expected": r["expected"], "got": d.method_id})
    correct = len(rows) - len(misses)
    return {
        "total": len(rows),
        "correct": correct,
        "accuracy": round(correct / len(rows), 3) if rows else 0.0,
        "per_method": dict(sorted(per_method.items())),
        "misses": misses,
        "methods_version": methods.version,
    }
