"""Structured worksheets for a chosen method, plus small calculators."""
from __future__ import annotations

import math

from .methods import Method
from .scoring import Decision


def build_worksheet(decision: Decision, method: Method, answers: dict[str, str] | None = None) -> dict:
    answers = answers or {}
    unknown = sorted(set(answers) - {f.field for f in method.worksheet})
    if unknown:
        raise KeyError(f"unknown worksheet field(s) for {method.id}: {', '.join(unknown)}")
    ws = {
        "method": method.id,
        "method_name": method.name,
        "question": decision.question,
        "summary": method.summary,
        "gates": [{"gate": g, "passed": False} for g in method.gates],
        "fields": [
            {"field": f.field, "prompt": f.prompt, "answer": answers.get(f.field, "")}
            for f in method.worksheet
        ],
    }
    if method.calculator:
        ws["calculator"] = run_calculator(method.calculator, answers)
    filled = sum(1 for f in ws["fields"] if f["answer"])
    ws["completion"] = f"{filled}/{len(ws['fields'])}"
    return ws


def _num(answers: dict[str, str], key: str) -> float | None:
    v = answers.get(key, "").strip().replace(",", "").replace("$", "").replace("%", "")
    try:
        return float(v)
    except ValueError:
        return None


def _missing_nonfinite(values: dict[str, float | None]) -> list[str]:
    return [k for k, v in values.items() if v is None or not math.isfinite(v)]


def _invalid_nonfinite_result() -> dict:
    return {"status": "invalid", "error": "calculator result must be finite"}


def _has_nonfinite_number(values) -> bool:
    return any(isinstance(v, float) and not math.isfinite(v) for v in values)


def unit_economics(answers: dict[str, str]) -> dict:
    """Contribution margin, CAC payback and LTV:CAC from worksheet answers.

    ``retention`` is the expected lifetime in periods.
    """
    rev = _num(answers, "revenue_per_unit")
    cost = _num(answers, "variable_cost_per_unit")
    cac = _num(answers, "cac")
    life = _num(answers, "retention")
    missing = _missing_nonfinite({"revenue_per_unit": rev, "variable_cost_per_unit": cost, "cac": cac, "retention": life})
    if missing:
        return {"status": "incomplete", "missing": missing}
    margin = rev - cost
    out = {
        "status": "ok",
        "contribution_margin": round(margin, 2),
        "contribution_margin_pct": round(margin / rev * 100, 1) if rev else None,
        "ltv": round(margin * life, 2),
    }
    out["payback_periods"] = round(cac / margin, 2) if margin > 0 else None
    out["ltv_to_cac"] = round(out["ltv"] / cac, 2) if cac > 0 else None
    if _has_nonfinite_number(out.values()):
        return _invalid_nonfinite_result()
    flags = []
    if margin <= 0:
        flags.append("negative contribution margin: each unit loses money before acquisition cost")
    elif out["payback_periods"] is not None and out["payback_periods"] > life:
        flags.append("CAC is never paid back within the expected lifetime")
    out["flags"] = flags
    return out


def expected_value(answers: dict[str, str]) -> dict:
    """EV = p x upside - (1 - p) x downside. ``probability`` may be 0-1 or a percent."""
    p = _num(answers, "probability")
    up = _num(answers, "upside")
    down = _num(answers, "downside")
    missing = [k for k, v in {"probability": p, "upside": up, "downside": down}.items() if v is None]
    missing += _missing_nonfinite({"upside": up, "downside": down})
    missing = sorted(set(missing))
    if missing:
        return {"status": "incomplete", "missing": missing}
    if p > 1:
        p = p / 100
    if not 0 <= p <= 1:
        return {"status": "invalid", "error": "probability must be between 0 and 1 (or 0-100%)"}
    ev = p * up - (1 - p) * down
    if not math.isfinite(ev):
        return _invalid_nonfinite_result()
    return {"status": "ok", "probability": p, "expected_value": round(ev, 2), "positive": ev > 0}


CALCULATORS = {"unit-economics": unit_economics, "expected-value": expected_value}


def run_calculator(name: str, answers: dict[str, str]) -> dict:
    if name not in CALCULATORS:
        raise KeyError(f"unknown calculator {name!r}")
    return CALCULATORS[name](answers)


def render_markdown(ws: dict) -> str:
    lines = [f"# {ws['method_name']} worksheet", "", f"**Question:** {ws['question']}", "", ws["summary"], ""]
    lines += ["## Gates", ""] + [f"- [{'x' if g['passed'] else ' '}] {g['gate']}" for g in ws["gates"]] + [""]
    for f in ws["fields"]:
        lines += [f"## {f['field']}", "", f"_{f['prompt']}_", "", f["answer"] or "[ ]", ""]
    if "calculator" in ws:
        lines += ["## Calculator", ""] + [f"- {k}: {v}" for k, v in ws["calculator"].items()] + [""]
    return "\n".join(lines)
