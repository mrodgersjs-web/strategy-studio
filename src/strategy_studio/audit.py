"""Append-only, hash-chained JSONL audit log of routing decisions."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .scoring import Decision

GENESIS = "0" * 64


def _entry_hash(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_log(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def build_entry(decision: Decision, prev: str, seq: int, ts: str | None = None) -> dict:
    runner = next((c for c in decision.ranking if c.method_id != decision.method_id), None)
    entry = {
        "seq": seq,
        "ts": ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": decision.question,
        "question_sha256": hashlib.sha256(decision.question.encode()).hexdigest(),
        "method": decision.method_id,
        "archetype": decision.archetype,
        "score": decision.score,
        "confidence": decision.confidence,
        "margin": decision.margin,
        "runner_up": runner.method_id if runner else None,
        "runner_up_score": runner.score if runner else None,
        "scores": {c.method_id: c.score for c in decision.ranking},
        "methods_version": decision.methods_version,
        "prev": prev,
    }
    entry["hash"] = _entry_hash(entry)
    return entry


def append(path: str | Path, decision: Decision, ts: str | None = None) -> dict:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    entries = read_log(p)
    prev = entries[-1]["hash"] if entries else GENESIS
    entry = build_entry(decision, prev, len(entries) + 1, ts)
    with p.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def verify(path: str | Path) -> tuple[bool, list[str]]:
    """Check every entry's hash and its link to the previous entry."""
    problems: list[str] = []
    prev = GENESIS
    for i, entry in enumerate(read_log(path), start=1):
        if entry.get("seq") != i:
            problems.append(f"entry {i}: seq is {entry.get('seq')}, expected {i}")
        if entry.get("prev") != prev:
            problems.append(f"entry {i}: prev hash does not match entry {i - 1}")
        if _entry_hash(entry) != entry.get("hash"):
            problems.append(f"entry {i}: hash mismatch (entry was edited)")
        prev = entry.get("hash", "")
    return (not problems, problems)
