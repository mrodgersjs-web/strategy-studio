"""Deterministic keyword scoring of a question against every method.

Same question + same methods file -> same scores, same winner, same order.
Ties break on the method's ``priority`` (lower wins), then on its id.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .methods import Method, MethodSet, load_methods


@dataclass(frozen=True)
class Candidate:
    method_id: str
    name: str
    score: int
    matched: tuple[tuple[str, int], ...]  # (phrase, weight)
    priority: int


@dataclass(frozen=True)
class Decision:
    question: str
    method_id: str
    method_name: str
    archetype: str
    score: int
    margin: float  # (winner - runner_up) / winner, 0..1; 0 when fallback
    confidence: str  # clear | narrow | tie-break | fallback
    explanation: str
    ranking: tuple[Candidate, ...] = field(repr=False)
    methods_version: str = ""

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "method": self.method_id,
            "method_name": self.method_name,
            "archetype": self.archetype,
            "score": self.score,
            "margin": self.margin,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "methods_version": self.methods_version,
            "ranking": [
                {"method": c.method_id, "score": c.score, "matched": [list(m) for m in c.matched]}
                for c in self.ranking
            ],
        }


_PATTERN_CACHE: dict[str, re.Pattern[str]] = {}


def _pattern(phrase: str) -> re.Pattern[str]:
    pat = _PATTERN_CACHE.get(phrase)
    if pat is None:
        parts = [re.escape(p) for p in re.split(r"[\s\-]+", phrase.strip()) if p]
        body = r"[\s\-]+".join(parts)
        # Allow a simple plural on the last word; word boundaries on both sides.
        pat = re.compile(rf"(?<![\w]){body}(?:s|es)?(?![\w])")
        _PATTERN_CACHE[phrase] = pat
    return pat


def _canon(phrase: str) -> str:
    return re.sub(r"[\s\-]+", " ", phrase.strip())


def normalize(question: str) -> str:
    return re.sub(r"\s+", " ", question.lower().replace("\u2019", "'")).strip()


def score_method(text: str, method: Method) -> Candidate:
    matched = []
    for phrase, weight in method.keywords:
        if _pattern(phrase).search(text):
            matched.append((phrase, weight))
    # A matched phrase that is contained in a longer matched phrase does not count twice
    # ("build" inside "build or buy").
    # Spelling variants ("go live" / "go-live") count once, at the highest weight.
    best: dict[str, tuple[str, int]] = {}
    for p, w in matched:
        key = _canon(p)
        if key not in best or w > best[key][1]:
            best[key] = (p, w)
    kept = [
        (p, w)
        for key, (p, w) in best.items()
        if not any(other != key and len(other) > len(key) and _pattern(p).search(other) for other in best)
    ]
    kept.sort(key=lambda pw: (-pw[1], pw[0]))
    return Candidate(method.id, method.name, sum(w for _, w in kept), tuple(kept), method.priority)


def rank(question: str, methods: MethodSet) -> list[Candidate]:
    text = normalize(question)
    cands = [score_method(text, m) for m in methods.methods if m.id != methods.fallback]
    cands.sort(key=lambda c: (-c.score, c.priority, c.method_id))
    return cands


def route(question: str, methods: MethodSet | None = None) -> Decision:
    if not question or not question.strip():
        raise ValueError("question must be a non-empty string")
    methods = methods or load_methods()
    ranking = rank(question, methods)
    top = ranking[0]
    runner = ranking[1] if len(ranking) > 1 else None
    if top.score == 0:
        fb = methods.get(methods.fallback)
        return Decision(
            question=question,
            method_id=fb.id,
            method_name=fb.name,
            archetype=fb.archetype,
            score=0,
            margin=0.0,
            confidence="fallback",
            explanation=f"No method keyword matched; routed to {fb.name} to define the decision first.",
            ranking=tuple(ranking),
            methods_version=methods.version,
        )
    second = runner.score if runner else 0
    margin = round((top.score - second) / top.score, 3)
    if top.score == second:
        confidence = "tie-break"
    elif margin >= 0.4:
        confidence = "clear"
    else:
        confidence = "narrow"
    terms = ", ".join(f"'{p}' (+{w})" for p, w in top.matched)
    expl = f"{top.name} scored {top.score} from {terms}."
    if runner and runner.score == 0:
        expl += " No other method matched any keyword."
    elif runner:
        expl += f" Runner-up {runner.name} scored {runner.score}"
        expl += " and lost the tie-break (priority, then id)." if confidence == "tie-break" else "."
    m = methods.get(top.method_id)
    return Decision(
        question=question,
        method_id=m.id,
        method_name=m.name,
        archetype=m.archetype,
        score=top.score,
        margin=margin,
        confidence=confidence,
        explanation=expl,
        ranking=tuple(ranking),
        methods_version=methods.version,
    )


def explain_losers(decision: Decision) -> list[dict]:
    """Why every other method lost to the winner, in ranking order."""
    out = []
    winner = next((c for c in decision.ranking if c.method_id == decision.method_id), None)
    for c in decision.ranking:
        if c.method_id == decision.method_id:
            continue
        if c.score == 0:
            reason = "no keyword matched"
        elif winner is None:
            reason = "fallback chosen"  # unreachable when any candidate scored > 0
        elif c.score == winner.score:
            reason = (
                f"tied at {c.score}; lost on priority ({c.priority} vs {winner.priority})"
                if c.priority != winner.priority
                else f"tied at {c.score} and priority; lost on id order"
            )
        else:
            reason = f"scored {c.score} vs {winner.score} (gap {winner.score - c.score})"
        out.append(
            {
                "method": c.method_id,
                "score": c.score,
                "matched": [p for p, _ in c.matched],
                "reason": reason,
            }
        )
    return out
