"""Deterministic archetype router — no LLM required.

12 archetypes (A1–A12) covering the full strategy surface.
Each maps a question to an archetype, cell, gate set, and rationale.
Pattern priority: specific before general; first match wins.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import re

@dataclass(frozen=True)
class Route:
    archetype: str
    cell: str
    gates: list[str]
    rationale: str

# Ordered (pattern, archetype, cell, gates, rationale) — first match wins.
# Patterns use \b prefix only (no trailing \b) so stems match inflections.
_ROUTES: list[tuple[str, str, str, list[str], str]] = [
    # A4: Execution / go-live — high priority (action verbs)
    (r"\b(ship|launch|go[\s-]*live|deploy|rollout|release)",
     "A4", "cell.go-live",
     ["eval-green", "rollback", "owner-named"],
     "Execution / go-live"),
    # A5: Competitive positioning
    (r"\b(compet|rival|moat|differentiat|categor)",
     "A5", "cell.competitive-position",
     ["competitor-map", "moat-audit", "differentiation-proof"],
     "Competitive positioning"),
    # A7: Market entry & expansion
    (r"\b(enter\s+the|enter\s+a|market\s*enter|expand\s+(in|into)|geograph|international)",
     "A7", "cell.market-entry",
     ["tam-sam-som", "entry-barrier", "go-to-market-seq"],
     "Market entry & expansion"),
    # A11: Risk, compliance & governance
    (r"\b(complian|audit|governan|regulat|soc\s*2|gdpr|hipaa)",
     "A11", "cell.risk-compliance",
     ["requirement-map", "control-gap", "residual-risk"],
     "Risk & compliance"),
    # A9: Partnerships & alliances
    (r"\b(partner|alliance|ecosystem|reseller)",
     "A9", "cell.partnership",
     ["value-exchange", "exclusivity-check", "exit-clause"],
     "Partnership & alliances"),
    # A6: Pricing & packaging
    (r"\b(pric|package\s+the|discount|willingness.to.pay|monetiz)",
     "A6", "cell.pricing-packaging",
     ["value-metric", "tier-fence", "price-test"],
     "Pricing & packaging"),
    # A8: Portfolio & roadmap prioritization
    (r"\b(portfolio|prioriti[sz]|roadmap|sequenc|backlog|initiative)",
     "A8", "cell.portfolio-priority",
     ["impact-effort", "dependency-map", "kill-criteria"],
     "Portfolio prioritization"),
    # A10: Growth & scaling
    (r"\b(scale|growth|acqui[sr]|retention|churn|viral|cohort)",
     "A10", "cell.growth-scale",
     ["unit-economics", "growth-loop", "capacity-limit"],
     "Growth & scaling"),
    # A3: Forecasting & risk quantification
    (r"\b(forecast|predict|probability|calibrat|brier|base\s*rate)",
     "A3", "cell.forecast-risk",
     ["base-rate", "calibration", "disconfirm"],
     "Uncertainty quantification"),
    # A12: Operational efficiency & automation
    (r"\b(efficien|optimi[sz]|automat|process|workflow|toil|bottleneck)",
     "A12", "cell.ops-efficiency",
     ["current-state", "automation-candidate", "roi-threshold"],
     "Operational efficiency"),
    # A2: Build vs buy / vendor decisions
    (r"\b(buy|build\s+or\s+buy|make\s*vs|vendor|outsource|insource)",
     "A2", "cell.build-vs-buy",
     ["evidence-table", "tco-bound", "kill-criteria"],
     "Choice under alternatives"),
    # A1: Org design & hiring
    (r"\b(hire|org\s+design|team\s+structure|role|staff|headcount|reporting)",
     "A1", "cell.org-design",
     ["role-boundary", "span-check"],
     "Organization design"),
]

_COMPILED = [(re.compile(pat), arch, cell, gates, rat)
             for pat, arch, cell, gates, rat in _ROUTES]


def route_question(q: str) -> Route:
    """Route a question string to its strategy archetype.

    Patterns are evaluated in priority order; first match wins.
    Falls back to A1 frame-problem when nothing matches.
    """
    t = q.lower()
    for pattern, archetype, cell, gates, rationale in _COMPILED:
        if pattern.search(t):
            return Route(archetype, cell, list(gates), rationale)
    return Route("A1", "cell.frame-problem",
                 ["define-outcome", "non-goals"],
                 "Default framing cell")


def list_archetypes() -> list[dict[str, str]]:
    """Return all registered archetypes with their cells and rationale."""
    seen: dict[str, dict[str, str]] = {}
    for _, arch, cell, _, rat in _ROUTES:
        if arch not in seen:
            seen[arch] = {"archetype": arch, "cell": cell, "rationale": rat}
    # Add default
    seen.setdefault("A1-default", {
        "archetype": "A1", "cell": "cell.frame-problem",
        "rationale": "Default framing cell",
    })
    return list(seen.values())


def to_dict(r: Route) -> dict:
    return asdict(r)
