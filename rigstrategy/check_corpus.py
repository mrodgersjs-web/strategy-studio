"""Corpus count gate for `make verify`.

Asserts the scraped candidate counts meet the /rigstrategy targets and prints
the Jev-verified counts from corpus/MANIFEST.json. Verified counts are a
quality report, not the gate: the gate is the size of the harvested corpus.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = {"good": 1000, "bad": 300}


def main():
    ok = True
    for name, target in TARGETS.items():
        p = os.path.join(ROOT, "corpus", name, "index.jsonl")
        n = sum(1 for _ in open(p))
        status = "OK" if n >= target else "SHORT"
        if n < target:
            ok = False
        print(f"corpus/{name}: {n} candidates (target {target}) {status}")
    man = json.load(open(os.path.join(ROOT, "corpus", "MANIFEST.json")))
    for name in ("good", "bad"):
        e = man.get(name, {})
        print(f"corpus/{name}: {e.get('count', 0)} jev-verified ({e.get('status', 'unknown')})")
    r = man.get("rendered", {})
    if r:
        print(f"corpus/rendered: {r.get('count', 0)} rendered, {r.get('jev_verified', 0)} jev-verified")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
