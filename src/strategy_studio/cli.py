from __future__ import annotations
import argparse, json
from .router import route_question, to_dict

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="strategy-route")
    p.add_argument("question")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    d = to_dict(route_question(args.question))
    print(json.dumps(d, indent=2) if args.json else f"{d['archetype']} -> {d['cell']}\ngates: {', '.join(d['gates'])}\n{d['rationale']}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
