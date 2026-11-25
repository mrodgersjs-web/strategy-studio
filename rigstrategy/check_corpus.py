"""Corpus count gate for `make verify`.

Asserts the harvested candidate counts meet the /rigstrategy targets (good>=1000,
bad>=300) and reports both v0 strict and v1 calibrated Jev-verified counts from
corpus/MANIFEST.json.
"""
import json
import os
import sys

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
        print(f"corpus/{name} (v0 strict): {e.get('count', 0)} jev-verified ({e.get('status', 'unknown')})")
    r = man.get("rendered", {})
    if r:
        print(f"corpus/rendered (v0 strict): {r.get('count', 0)} rendered, {r.get('jev_verified', 0)} jev-verified")
    v1 = man.get("v1_calibrated")
    if v1:
        g1 = v1.get("confirmed_good_total", 0)
        b1 = v1.get("confirmed_bad_total", 0)
        v1_ok = g1 >= TARGETS["good"] and b1 >= TARGETS["bad"]
        if not v1_ok:
            ok = False
        print(
            f"corpus/v1_calibrated: {g1} good (target {TARGETS['good']}), "
            f"{b1} bad (target {TARGETS['bad']}) {'OK' if v1_ok else 'SHORT'}"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
