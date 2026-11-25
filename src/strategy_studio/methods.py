"""Load and validate strategy method definitions shipped as data."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

SCHEMA = "strategy-studio.methods.v1"
ARCHETYPES = {"A1", "A2", "A3", "A4"}


class MethodsError(ValueError):
    """Raised when a methods file is malformed."""


@dataclass(frozen=True)
class WorksheetField:
    field: str
    prompt: str


@dataclass(frozen=True)
class Method:
    id: str
    name: str
    archetype: str
    priority: int
    summary: str
    keywords: tuple[tuple[str, int], ...]
    gates: tuple[str, ...]
    worksheet: tuple[WorksheetField, ...]
    calculator: str | None = None


@dataclass(frozen=True)
class MethodSet:
    methods: tuple[Method, ...]
    fallback: str
    version: str  # sha256 prefix of the canonical JSON, recorded in every audit entry

    def get(self, method_id: str) -> Method:
        for m in self.methods:
            if m.id == method_id:
                return m
        raise KeyError(f"unknown method: {method_id}")

    @property
    def ids(self) -> list[str]:
        return [m.id for m in self.methods]


def _parse(raw: dict) -> MethodSet:
    if raw.get("schema") != SCHEMA:
        raise MethodsError(f"schema must be {SCHEMA!r}, got {raw.get('schema')!r}")
    methods: list[Method] = []
    seen: set[str] = set()
    for i, m in enumerate(raw.get("methods", [])):
        for key in ("id", "name", "archetype", "priority", "summary", "keywords", "gates", "worksheet"):
            if key not in m:
                raise MethodsError(f"method #{i} missing {key!r}")
        if m["id"] in seen:
            raise MethodsError(f"duplicate method id {m['id']!r}")
        seen.add(m["id"])
        if m["archetype"] not in ARCHETYPES:
            raise MethodsError(f"{m['id']}: archetype must be one of {sorted(ARCHETYPES)}")
        kws = []
        for phrase, weight in m["keywords"].items():
            if not isinstance(weight, int) or weight <= 0:
                raise MethodsError(f"{m['id']}: weight for {phrase!r} must be a positive int")
            kws.append((phrase.lower(), weight))
        if not m["worksheet"]:
            raise MethodsError(f"{m['id']}: worksheet must have at least one field")
        methods.append(
            Method(
                id=m["id"],
                name=m["name"],
                archetype=m["archetype"],
                priority=int(m["priority"]),
                summary=m["summary"],
                keywords=tuple(sorted(kws)),
                gates=tuple(m["gates"]),
                worksheet=tuple(WorksheetField(f["field"], f["prompt"]) for f in m["worksheet"]),
                calculator=m.get("calculator"),
            )
        )
    if not methods:
        raise MethodsError("no methods defined")
    fallback = raw.get("fallback")
    if fallback not in seen:
        raise MethodsError(f"fallback {fallback!r} is not a defined method")
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    return MethodSet(tuple(methods), fallback, hashlib.sha256(canonical).hexdigest()[:12])


def load_methods(path: str | Path | None = None) -> MethodSet:
    """Load the bundled methods file, or a custom one from ``path``."""
    if path is None:
        text = resources.files("strategy_studio").joinpath("data/methods.json").read_text()
    else:
        text = Path(path).read_text()
    return _parse(json.loads(text))
