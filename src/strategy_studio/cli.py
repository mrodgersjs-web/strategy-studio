"""CLI for the strategy-studio deterministic router.

``strategy-route``  legacy archetype router (A1-A4 cells), unchanged.
``strategy-studio`` method router: route, explain, worksheet, methods, eval, audit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from . import audit as audit_mod
from .evaluate import evaluate, load_labelled
from .methods import load_methods
from .scoring import explain_losers, route
from .worksheet import build_worksheet, render_markdown

DEFAULT_LOG = ".strategy-studio/audit.jsonl"

from .batch import route_batch, route_from_file, summarize_store
from .integration import analyze_question
from .jev_head import route_question_jev
from .playbooks import get_playbook, list_playbooks
from .records import DecisionStore, make_decision
from .router import list_archetypes, route_question, to_dict


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="strategy-route",
        description="Deterministic strategy routing — question → archetype → cell → gates.",
    )
    p.add_argument("question", nargs="?", default=None,
                   help="Strategy question to route (omit with --list-archetypes or --stats)")
    p.add_argument("--json", action="store_true",
                   help="Output as JSON")
    p.add_argument("--list-archetypes", action="store_true",
                   help="List all registered archetypes and exit")
    p.add_argument("--record", action="store_true",
                   help="Persist decision record to JSONL store")
    p.add_argument("--store-path", type=str, default=None,
                   help="Custom path for the decision store")
    p.add_argument("--with-gates", action="store_true",
                   help="Include gate evaluation results in output")
    p.add_argument("--batch", type=str, metavar="FILE",
                   help="Route questions from file (one per line)")
    p.add_argument("--summary", action="store_true",
                   help="Compact one-line-per-question output for batch mode")
    p.add_argument("--export", type=str, metavar="FILE",
                   help="Export batch results as markdown report to FILE")
    p.add_argument("--validate", action="store_true",
                   help="Validate question quality before routing")
    p.add_argument("--stats", action="store_true",
                   help="Show aggregate statistics from the decision store")
    p.add_argument("--playbook", type=str, metavar="CELL",
                   help="Show playbook for a cell (e.g. cell.build-vs-buy)")
    p.add_argument("--list-playbooks", action="store_true",
                   help="List all available playbooks")
    p.add_argument("--jev", action="store_true",
                   help="Route via the Jev (System One) head with fail-open to the regex router")
    p.add_argument("--full", action="store_true",
                   help="Full analysis: route + gates + playbook (implies --record)")
    args = p.parse_args(argv)

    # ── List archetypes ────────────────────────────────────────────────
    if args.list_archetypes:
        archetypes = list_archetypes()
        if args.json:
            print(json.dumps(archetypes, indent=2))
        else:
            for a in archetypes:
                print(f"  {a['archetype']:>4}  {a['cell']:<30}  {a['rationale']}")
        return 0

    # ── List playbooks ─────────────────────────────────────────────────
    if args.list_playbooks:
        pbs = list_playbooks()
        if args.json:
            print(json.dumps(pbs, indent=2))
        else:
            for pb in pbs:
                print(f"  {pb['archetype']:>4}  {pb['cell']:<30}  {pb['title']}")
        return 0

    # ── Show playbook ──────────────────────────────────────────────────
    if args.playbook:
        pb = get_playbook(args.playbook)
        if not pb:
            print(f"  No playbook for: {args.playbook}", file=sys.stderr)
            return 1
        if args.json:
            print(pb.to_json())
        else:
            print(f"  {pb.title} ({pb.archetype})")
            print(f"  {pb.description}\n")
            print(f"  Steps:")
            for s in pb.steps:
                print(f"    {s.order}. {s.name}: {s.instruction}")
            print(f"\n  Key questions:")
            for q in pb.key_questions:
                print(f"    • {q}")
            print(f"\n  Template:")
            for field_name, placeholder in pb.template.items():
                print(f"    {field_name}: {placeholder}")
            print(f"\n  Pitfalls:")
            for pit in pb.pitfalls:
                print(f"    ⚠ {pit}")
        return 0

    # ── Store statistics ───────────────────────────────────────────────
    if args.stats:
        store = DecisionStore(args.store_path)
        summary = summarize_store(store)
        if args.json:
            print(summary.to_json())
        else:
            print(f"  Total records : {summary.total_records}")
            print(f"  Avg confidence: {summary.avg_confidence:.0%}")
            print(f"  Archetypes:")
            for arch, count in sorted(summary.archetype_distribution.items()):
                print(f"    {arch:>4}: {count}")
            print(f"  Confidence histogram:")
            for bucket, count in summary.confidence_histogram.items():
                bar = "█" * count
                print(f"    {bucket}: {bar} ({count})")
        return 0

    # ── Batch routing ──────────────────────────────────────────────────
    if args.batch:
        records = route_from_file(args.batch)
        if args.record:
            store = DecisionStore(args.store_path)
            for rec in records:
                store.append(rec)
        if args.json:
            print(json.dumps([r.to_dict() for r in records], indent=2))
        elif args.summary:
            for rec in records:
                gp = sum(1 for g in rec.gate_results if g.passed)
                gt = len(rec.gate_results)
                print(f"{rec.route.archetype:>4} | {rec.route.cell:<28} | gates {gp}/{gt} | conf {rec.confidence:.0%} | {rec.question[:50]}")
            print(f"\n  {len(records)} questions routed")
        else:
            for rec in records:
                print(f"  {rec.route.archetype:>4}  {rec.route.cell:<30}  conf={rec.confidence:.0%}  {rec.question[:60]}")
            print(f"\n  {len(records)} questions routed")
        return 0

    # ── Export markdown ────────────────────────────────────────────────
    if args.export:
        records = route_from_file(args.question) if args.question else []
        if not records:
            p.error("question arg used as input file with --export")
        lines = ["# Strategy Analysis Report\n"]
        lines.append(f"**Questions analyzed:** {len(records)}\n")
        lines.append("| Archetype | Cell | Gates | Confidence | Question |")
        lines.append("|---|---|---|---|---|")
        for rec in records:
            gp = sum(1 for g in rec.gate_results if g.passed)
            gt = len(rec.gate_results)
            lines.append(f"| {rec.route.archetype} | {rec.route.cell} | {gp}/{gt} | {rec.confidence:.0%} | {rec.question[:60]} |")
        lines.append("\n## Detailed Results\n")
        for rec in records:
            lines.append(f"### {rec.route.archetype}: {rec.question}\n")
            lines.append(f"- **Cell:** {rec.route.cell}")
            lines.append(f"- **Rationale:** {rec.route.rationale}")
            lines.append(f"- **Confidence:** {rec.confidence:.0%}")
            lines.append(f"- **Gates:** {', '.join(rec.route.gates)}")
            if rec.gate_results:
                lines.append(f"- **Gate results:**")
                for g in rec.gate_results:
                    mark = '✓' if g.passed else '✗'
                    lines.append(f"  - {mark} {g.name}: {g.evidence}")
            lines.append("")
        Path(args.export).write_text("\n".join(lines))
        print(f"  Exported {len(records)} results to {args.export}")
        return 0

    # ── Full analysis ──────────────────────────────────────────────────
    if args.full:
        if not args.question:
            p.error("question is required with --full")
        store = DecisionStore(args.store_path) if args.record else None
        resp = analyze_question(args.question, store=store)
        if args.json:
            print(resp.to_json())
        else:
            print(resp.format_text())
        return 0

    # ── Validate question ──────────────────────────────────────────────
    if args.validate:
        if not args.question:
            p.error("question is required with --validate")
        q = args.question
        words = len(q.split())
        issues = []
        if words < 5:
            issues.append(f"Too short ({words} words) — aim for 8+ words")
        if words > 50:
            issues.append(f"Very long ({words} words) — consider splitting")
        sw = {"should","how","what","build","buy","scale","grow","compete","price","enter","partner","hire","ship","launch","deploy","risk"}
        found = [w for w in sw if w in q.lower()]
        if not found:
            issues.append("No strategy keywords — may route to default cell")
        if issues:
            print(f"  Words: {words} | Issues: {'; '.join(issues)}")
        else:
            print(f"  Words: {words} | Keywords: {found} | Good for routing")
        return 0

    # ── Single question ────────────────────────────────────────────────
    if not args.question:
        p.error("question is required (or use --list-archetypes / --stats / --batch)")

    if args.jev:
        r, meta = route_question_jev(args.question)
        d = to_dict(r)
        d["jev"] = {k: meta.get(k) for k in ("source", "top1", "margin", "model", "latency_ms", "error")}
        if args.json:
            print(json.dumps(d, indent=2))
        else:
            print(f"  archetype : {d['archetype']}  (source={meta['source']}, top1={meta['top1']}, margin={meta['margin']})")
            print(f"  cell      : {d['cell']}")
            print(f"  gates     : {', '.join(d['gates'])}")
            print(f"  rationale : {d['rationale']}")
            if meta.get("error"):
                print(f"  jev error : {meta['error']}")
        return 0

    if args.record or args.with_gates:
        rec = make_decision(args.question)
        if args.record:
            store = DecisionStore(args.store_path)
            store.append(rec)
        if args.json:
            out = rec.to_dict()
            if not args.with_gates:
                out.pop("gate_results", None)
                out.pop("metadata", None)
            print(json.dumps(out, indent=2))
        else:
            print(f"  archetype  : {rec.route.archetype}")
            print(f"  cell       : {rec.route.cell}")
            print(f"  gates      : {', '.join(rec.route.gates)}")
            print(f"  rationale  : {rec.route.rationale}")
            print(f"  confidence : {rec.confidence:.0%}")
            if args.with_gates:
                print(f"  gate results:")
                for g in rec.gate_results:
                    mark = "✓" if g.passed else "✗"
                    print(f"    {mark} {g.name}: {g.evidence}")
    else:
        r = route_question(args.question)
        d = to_dict(r)
        if args.json:
            print(json.dumps(d, indent=2))
        else:
            print(f"  archetype : {d['archetype']}")
            print(f"  cell      : {d['cell']}")
            print(f"  gates     : {', '.join(d['gates'])}")
            print(f"  rationale : {d['rationale']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


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
