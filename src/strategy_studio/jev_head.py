"""Jev (TypeSafe System One) head over the deterministic archetype router.

Design contract (the reason this file exists beside router.py, not inside it):
- ``router.route_question()`` stays 100% deterministic and offline. The
  conftest anti-fake gate depends on that and is not negotiable.
- ``route_question_jev()`` adds calibrated-choice routing: one Jev call over
  the 12 archetypes returns a probability per archetype plus a locally
  computed top-2 margin. It FAILS OPEN -- provider error, abstention below
  the floors, or a malformed answer all fall back to the regex router and
  are labelled as such in the returned meta.
- Thresholds are UNCALIBRATED until labelled decision rows exist (the same
  discipline as rig-capabilities s1gate). They are env-overridable:
  STRATEGY_JEV_TOP1_FLOOR / STRATEGY_JEV_MARGIN_FLOOR.
- The API key comes from $TYPESAFE_API_KEY or the macOS keychain item
  ``com.rig.env.TYPESAFE_API_KEY``. The value is never returned to a caller,
  never logged, never written.

Every Jev-backed decision is appended to
``~/.rig/1000x/strategy-records/jev_routes.jsonl`` (sha256 of the question,
not the question text) so a later ``calibrate`` can earn real thresholds.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .router import Route, _ROUTES

JEV_BASE_URL = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai").rstrip("/")
JEV_MODEL = os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest")
KEYCHAIN_ITEM = os.environ.get("S1GATE_KEYCHAIN_ITEM", "com.rig.env.TYPESAFE_API_KEY")
ROUTES_JSONL = (
    Path(os.environ.get("STRATEGY_RECORDS_DIR", Path.home() / ".rig" / "1000x" / "strategy-records"))
    / "jev_routes.jsonl"
)

DEFAULT_TOP1_FLOOR = 0.40
DEFAULT_MARGIN_FLOOR = 0.08


class JevError(RuntimeError):
    """The System One provider could not be reached or returned garbage."""


def _floor(env_name: str, default: float) -> float:
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_ITEM, "-w"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise JevError("keychain lookup failed: %s" % type(exc).__name__) from exc
    key = (out.stdout or "").strip()
    if not key:
        raise JevError("no System One API key: set TYPESAFE_API_KEY or store keychain item %s" % KEYCHAIN_ITEM)
    return key


def ask_jev(state: str, questions: Dict[str, Any], *, timeout: float = 20.0, retries: int = 2) -> Dict[str, Any]:
    """POST one System One request. Raises JevError on any failure."""
    payload = json.dumps({"state": state, "model": JEV_MODEL, "questions": questions}).encode("utf-8")
    key = _api_key()
    last: Optional[Exception] = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            JEV_BASE_URL + "/v1/systemone",
            data=payload,
            method="POST",
            headers={
                "Authorization": "Bearer %s" % key,
                "Content-Type": "application/json",
                "User-Agent": "strategy-studio-jev-head/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            if "answers" not in body:
                raise JevError("response missing 'answers'")
            return body
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8")[:300]
            except Exception:
                pass
            last = JevError("HTTP %s: %s" % (exc.code, detail))
            if exc.code != 429 and 400 <= exc.code < 500:
                break
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            last = JevError("%s: %s" % (type(exc).__name__, exc))
        if attempt < retries:
            time.sleep(0.4 * (2 ** attempt))
    raise last if last else JevError("unknown provider failure")


def _archetypes() -> List[Dict[str, str]]:
    """Deduped archetype list in router priority order."""
    seen: Dict[str, Dict[str, str]] = {}
    for _pat, arch, cell, _gates, rat in _ROUTES:
        if arch not in seen:
            seen[arch] = {"id": arch, "desc": "%s (%s)" % (rat, cell)}
    return list(seen.values())


def _route_for(archetype: str) -> Route:
    """Build the canonical Route for a Jev-chosen archetype."""
    for _pat, arch, cell, gates, rat in _ROUTES:
        if arch == archetype:
            return Route(arch, cell, list(gates), rat)
    return Route("A1", "cell.frame-problem", ["define-outcome", "non-goals"], "Default framing cell")


def _margin(probabilities: Dict[str, float]) -> Tuple[str, float, float]:
    ranked = sorted(probabilities.items(), key=lambda kv: kv[1], reverse=True)
    top_id, top_p = ranked[0]
    second_p = ranked[1][1] if len(ranked) > 1 else 0.0
    return top_id, float(top_p), round(float(top_p - second_p), 4)


def _log(meta: Dict[str, Any]) -> None:
    try:
        ROUTES_JSONL.parent.mkdir(parents=True, exist_ok=True)
        with ROUTES_JSONL.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(meta, sort_keys=True) + "\n")
    except OSError:
        pass  # the decision still returns; the log is best-effort


def route_question_jev(
    q: str,
    *,
    top1_floor: Optional[float] = None,
    margin_floor: Optional[float] = None,
    log: bool = True,
) -> Tuple[Route, Dict[str, Any]]:
    """Route via Jev with fail-open to the deterministic regex router.

    Returns (Route, meta). meta["source"] is one of:
      "jev"            -- Jev picked it above both floors
      "jev-abstained"  -- Jev answered but below a floor (or said none-of-the-above)
      "regex-failopen" -- provider unreachable; regex answer used
    """
    if not q or not q.strip():
        raise ValueError("question must be a non-empty string")
    if top1_floor is None:
        top1_floor = _floor("STRATEGY_JEV_TOP1_FLOOR", DEFAULT_TOP1_FLOOR)
    if margin_floor is None:
        margin_floor = _floor("STRATEGY_JEV_MARGIN_FLOOR", DEFAULT_MARGIN_FLOOR)

    archs = _archetypes()
    meta: Dict[str, Any] = {
        "ts": time.time(),
        "question_sha256": hashlib.sha256(q.encode("utf-8")).hexdigest(),
        "source": "regex-failopen",
        "probabilities": None,
        "top1": None,
        "margin": None,
        "model": None,
        "latency_ms": None,
        "error": None,
        "top1_floor": top1_floor,
        "margin_floor": margin_floor,
    }
    started = time.time()
    questions = {
        "archetype": {
            "type": "choice",
            "instructions": "Which strategy archetype does this question belong to?",
            "criteria": {a["id"]: a["desc"] for a in archs},
        }
    }
    try:
        body = ask_jev(q.strip(), questions)
        ans = body.get("answers", {}).get("archetype", {})
        probs = ans.get("probabilities") or {}
        if not probs:
            raise JevError("answer missing probabilities")
        top_id, top_p, margin = _margin(probs)
        meta["model"] = body.get("model")
        meta["latency_ms"] = int((time.time() - started) * 1000)
        meta["probabilities"] = {k: round(float(v), 4) for k, v in probs.items()}
        meta["top1"] = round(top_p, 4)
        meta["margin"] = margin
        if top_p >= top1_floor and margin >= margin_floor and top_id in {a["id"] for a in archs}:
            meta["source"] = "jev"
            route = _route_for(top_id)
        else:
            meta["source"] = "jev-abstained"
            route = route_question_fallback(q)
    except (JevError, ValueError, KeyError) as exc:
        meta["error"] = str(exc)[:300]
        meta["latency_ms"] = int((time.time() - started) * 1000)
        route = route_question_fallback(q)

    if log:
        _log(meta)
    return route, meta


def route_question_fallback(q: str) -> Route:
    """The deterministic path, imported lazily so tests can patch around it."""
    from .router import route_question

    return route_question(q)
