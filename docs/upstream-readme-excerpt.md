# RIG Strategy Studio

**A 147-cell deterministic routing engine that maps any strategic question to the cheapest execution mode that can answer it — from a $0.001 rules-only pass to a full agent crew — with evidence-weighted synthesis at every step.**

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg) ![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg) ![Tests](https://img.shields.io/badge/tests-371%20collected-brightgreen.svg) ![Status](https://img.shields.io/badge/status-beta-orange.svg)

## The problem

Most "AI strategy" tooling sends every question to the most expensive model available. A question that a deterministic rule could answer for a fraction of a cent gets routed to an Opus crew — slow, costly, and unauditable. And when the answer comes back, you can't tell which claims were grounded in evidence and which the model invented.

RIG Strategy Studio fixes the routing problem first. Every strategic intent is classified onto a **147-cell lattice** (7 altitudes × 3 domains × 7 process steps), and each cell is bound to one of **four cost-capped build modes** — A1 (rules only) through A4 (agent crew). The system picks the cheapest mode that can actually answer the question and only escalates on failure. Synthesis is evidence-weighted: claims without cited sources are flagged `UNKNOWN`, not guessed.

```bash
strategy-studio lattice summary                                      # see the four cost bands
strategy-studio lattice pipeline --altitude 2 --diamond D1 --query "..."
```

## Who it's for

- **Strategy & corp-dev teams** who want repeatable, citeable decisions instead of one-off model chats.
- **Operators wiring LLMs into a pipeline** who need a hard cost cap per decision and a deterministic floor.
- **Anyone tired of "the model said so"** — every output here is mode-tagged, cost-bounded, and evidence-scored.

## What you get

- **147-cell decision lattice** — `L{altitude}-D{diamond}-{IQRSQPI step}`, every cell resolvable and inspectable as a Build Card.
- **4 cost-capped build modes (A1–A4)** — binding `<=$0.001 / <=$0.05 / <=$1 / <=$50` ceilings, not suggestions, with automatic A1→A2→A3→A4 escalation on failure.
- **BMS auto-selection** — Build-Mode Score picks the mode per cell from altitude + complexity; explicit override supported.
- **Evidence-weighted synthesis** — minimum-2-cited-sources rule; uncited claims return `UNKNOWN` with an indexing request instead of a hallucination.
- **Strategy engines** — synthesis, market wargame, forecasting, falsification, competitor/client intelligence, decision room (MCDA + sensitivity + value-of-information).
- **FastAPI service** — `/synthesize`, `/wargame`, `/forecast`, `/falsify`, and `/lattice/*` endpoints backed by Pydantic models.
- **Click CLI** — the `strategy-studio` binary with a `lattice` command group (`summary`, `bms`, `cards`, `cell`, `map`, `pipeline`, `traverse`) plus engine commands (`synthesize`, `wargame`, `forecast`, `falsify`, `full`, ...).
- **ProofPacket + FalsificationPacket** on external-facing deliverables — every send carries an audit trail.
- **371 tests** across the lattice, BMS routing, engines, teaser pipeline, and tool registry.

## RIG Lattice — core architecture

The lattice is a **147-cell decision matrix** routing every strategy question to the right execution mode.

```
147 cells = 7 Altitudes × 3 Diamonds × 7 IQRSQPI steps
L{A}-{D[123]}-{I1|Q1|R|S|Q2|P|I2}
```

| Axis | Values | Doctrine |
|------|--------|----------|
| Altitude | L1–L7 | Deterministic → novel frame. Sets cost band + BMS threshold. |
| Diamond | D1 (Strategy), D2 (Intelligence), D3 (Operations) | Domain classification |
| IQRSQPI | I1→Q1→R→S→Q2→P→I2 | Intent → Question → Research → Solution → Quality → Proof → Integrate |

Four build modes — not recommendations, **binding cost constraints**:

| Mode | Cap | Executor | Cells |
|------|-----|----------|-------|
| A1 PYTHON_ONLY | <=$0.001 | Pydantic + Jinja2 + regex, no model in path | 42 |
| A2 HYBRID | <=$0.05 | A1 + Haiku/Sonnet shims | 42 |
| A3 AGENT_BOUNDED | <=$1 | LangGraph + CrewAI + guardrails | 42 |
| A4 LLM_AGENT_FREE | <=$50 / 4h | Opus crews + falsification | 21 |

BMS auto-selects the mode per cell. Escalation on failure: A1→A2→A3→A4.

Full reference: [`docs/rig-lattice-architecture.md`](docs/rig-lattice-architecture.md).

## Quick start

```bash
# Clone (point at your own fork)
git clone https://github.com/your-org/strategy-studio.git
cd strategy-studio

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package (CLI + engines + FastAPI service)
pip install -e .

# Install dev dependencies (to run the test suite)
pip install -e ".[dev]"

# Smoke test — show the lattice + the four build modes
strategy-studio lattice summary
```

One real command, copy-pasteable, that runs with no external services:

```bash
strategy-studio lattice summary
```

You should see the 147-cell lattice summary including the A1–A4 build-mode breakdown with cell counts.

## CLI usage

The `strategy-studio` command exposes the lattice and execution surfaces:

```bash
# Lattice operations
strategy-studio lattice summary                 # 147 cells + A1-A4 cost bands
strategy-studio lattice cell L2-D1-I1           # inspect a single cell's Build Card
