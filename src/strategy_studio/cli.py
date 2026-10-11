"""Command line entrypoints.

``strategy-route``  legacy archetype router (A1-A4 cells), unchanged.
``strategy-studio`` method router: route, explain, worksheet, methods, eval, audit.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import audit as audit_mod
from .evaluate import evaluate, load_labelled
from .methods import load_methods
from .router import route_question, to_dict
from .scoring import explain_losers, route
from .worksheet import build_worksheet, render_markdown

DEFAULT_LOG = ".strategy-studio/audit.jsonl"


def main(argv=None) -> int:
    """Legacy ``strategy-route`` entrypoint (archetype router)."""
    p = argparse.ArgumentParser(prog="strategy-route")
    p.add_argument("question")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    d = to_dict(route_question(args.question))
    print(json.dumps(d, indent=2) if args.json else f"{d['archetype']} -> {d['cell']}\ngates: {', '.join(d['gates'])}\n{d['rationale']}")
    return 0


def _parse_answers(pairs: list[str]) -> dict[str, str]:
    out = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit(f"--set expects field=value, got {pair!r}")
        k, v = pair.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _add_common(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--methods", help="path to a custom methods.json (default: bundled)")
    sp.add_argument("--json", action="store_true", help="print JSON")


def studio(argv=None) -> int:
    p = argparse.ArgumentParser(prog="strategy-studio", description="Deterministic strategy method router")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("route", help="route a question to a method and append to the audit log")
    r.add_argument("question")
    r.add_argument("--log", default=DEFAULT_LOG, help=f"audit log path (default {DEFAULT_LOG})")
    r.add_argument("--no-log", action="store_true", help="do not write an audit entry")
    r.add_argument("--ts", help="fixed timestamp for the audit entry (for reproducible runs)")
    _add_common(r)

    e = sub.add_parser("explain", help="scoring/audit mode: why the winner won and every other method lost")
    e.add_argument("question")
    _add_common(e)

    w = sub.add_parser("worksheet", help="route and emit the worksheet for the chosen method")
    w.add_argument("question")
    w.add_argument("--method", help="force a method id instead of routing")
    w.add_argument("--set", action="append", metavar="FIELD=VALUE", help="fill a worksheet field (repeatable)")
    w.add_argument("--markdown", action="store_true", help="print markdown instead of text summary")
    _add_common(w)

    m = sub.add_parser("methods", help="list method definitions")
    _add_common(m)

    ev = sub.add_parser("eval", help="accuracy on a labelled question set")
    ev.add_argument("--labelled", help="JSONL with question/expected (default: bundled set)")
    ev.add_argument("--holdout", action="store_true", help="use the bundled held-out set instead of the tuning set")
    ev.add_argument("--min-accuracy", type=float, default=0.0, help="exit 1 if accuracy is below this")
    _add_common(ev)

    a = sub.add_parser("audit", help="audit log tools")
    a.add_argument("action", choices=["verify", "show"])
    a.add_argument("--log", default=DEFAULT_LOG)
    a.add_argument("--json", action="store_true")

    args = p.parse_args(argv)

    if args.cmd == "audit":
        if args.action == "verify":
            ok, problems = audit_mod.verify(args.log)
            n = len(audit_mod.read_log(args.log))
            if args.json:
                print(json.dumps({"ok": ok, "entries": n, "problems": problems}, indent=2))
            else:
                print(f"audit log {args.log}: {n} entries, {'OK' if ok else 'BROKEN'}")
                for pr in problems:
                    print(f"  - {pr}")
            return 0 if ok and n > 0 else 1
        entries = audit_mod.read_log(args.log)
        if args.json:
            print(json.dumps(entries, indent=2))
        else:
            for en in entries:
                print(f"#{en['seq']} {en['ts']} {en['method']} ({en['score']}, {en['confidence']}) {en['question']}")
        return 0

    methods = load_methods(args.methods)

    if args.cmd == "methods":
        if args.json:
            rows = [{"id": x.id, "name": x.name, "archetype": x.archetype, "summary": x.summary} for x in methods.methods]
            print(json.dumps(rows, indent=2))
        else:
            for x in methods.methods:
                print(f"{x.id:26} {x.archetype}  {x.name}")
            print(f"methods_version {methods.version}")
        return 0

    if args.cmd == "eval":
        rep = evaluate(load_labelled(args.labelled, "holdout" if args.holdout else "labelled"), methods)
        if args.json:
            print(json.dumps(rep, indent=2))
        else:
            print(f"accuracy {rep['correct']}/{rep['total']} = {rep['accuracy']:.3f} (methods {rep['methods_version']})")
            for mid, s in rep["per_method"].items():
                print(f"  {mid:26} {s['correct']}/{s['total']}")
            for miss in rep["misses"]:
                print(f"  MISS expected={miss['expected']} got={miss['got']}: {miss['question']}")
        return 0 if rep["accuracy"] >= args.min_accuracy else 1

    try:
        decision = route(args.question, methods)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.cmd == "route":
        out = decision.to_dict()
        if not args.no_log:
            entry = audit_mod.append(args.log, decision, ts=args.ts)
            out["audit"] = {"log": args.log, "seq": entry["seq"], "hash": entry["hash"]}
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(f"{decision.method_name} [{decision.method_id}] score={decision.score} confidence={decision.confidence}")
            print(decision.explanation)
            if "audit" in out:
                print(f"audit: {args.log} #{out['audit']['seq']}")
        return 0

    if args.cmd == "explain":
        losers = explain_losers(decision)
        if args.json:
            print(json.dumps({**decision.to_dict(), "losers": losers}, indent=2))
        else:
            print(f"WINNER {decision.method_id} score={decision.score} margin={decision.margin} confidence={decision.confidence}")
            print(f"  {decision.explanation}")
            for lo in losers:
                hits = f" matched: {', '.join(lo['matched'])}" if lo["matched"] else ""
                print(f"  lost  {lo['method']:26} {lo['reason']}{hits}")
        return 0

    if args.cmd == "worksheet":
        method = methods.get(args.method) if args.method else methods.get(decision.method_id)
        try:
            ws = build_worksheet(decision, method, _parse_answers(args.set))
        except KeyError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(ws, indent=2))
        elif args.markdown:
            print(render_markdown(ws))
        else:
            print(f"{ws['method_name']} worksheet ({ws['completion']} filled)")
            for f in ws["fields"]:
                print(f"- {f['field']}: {f['prompt']}" + (f"\n    -> {f['answer']}" if f["answer"] else ""))
            if "calculator" in ws:
                print(f"calculator: {json.dumps(ws['calculator'])}")
        return 0
    return 1  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(studio())
