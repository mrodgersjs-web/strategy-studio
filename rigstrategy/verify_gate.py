"""Gate verifier: Jev-image confirmation for scraped corpus candidates.

Skips ids already CONFIRMED (correct rubric label for their candidate class) in the
verification files passed as argv[3:]. 2 workers, exponential backoff on HTTP 429.
Append-only output, resumable: rerun the same command to continue.

Usage:
  python3 rigstrategy/verify_gate.py PENDING.jsonl OUT.jsonl VERIFIED1.jsonl [VERIFIED2 ...]
"""
import json, subprocess, urllib.request, os, sys, time
from concurrent.futures import ThreadPoolExecutor

J = os.path.expanduser("~/.rig/bin/jev-image")
D = "/tmp/rsimg"; os.makedirs(D, exist_ok=True)
Q = "Judge this image as a business chart or strategy diagram."
R = "well_designed_chart_or_diagram|poorly_designed_or_misleading_chart|photo_or_not_a_chart"
CONFIRMED = {
    "candidate-good": "well_designed_chart_or_diagram",
    "candidate-bad": "poorly_designed_or_misleading_chart",
}

inp, out = sys.argv[1], sys.argv[2]

def confirmed_ids(files):
    s = set()
    for f in files:
        if not os.path.exists(f):
            continue
        for l in open(f):
            try:
                r = json.loads(l)
            except Exception:
                continue
            j, c = r.get("jev_label"), r.get("candidate")
            if j and c in CONFIRMED and j == CONFIRMED[c]:
                s.add(r["id"])
    return s

confirmed = confirmed_ids(sys.argv[3:] + [out])

def one(x):
    r = None
    for t in range(6):
        r = _one(x)
        if not (r and r.get("error") and "429" in r["error"]):
            return r
        time.sleep(10 * 2 ** t)
    return r

def _one(x):
    if not x.get("thumb"):
        return None
    p = f"{D}/{x['id']}.png"
    try:
        if os.path.exists(p) and os.path.getsize(p) == 0:
            os.remove(p)  # yesterday's 429s cached empty files
        if not os.path.exists(p):
            pass
            open(p, "wb").write(urllib.request.urlopen(
                urllib.request.Request(x["thumb"],
                                       headers={"User-Agent": "rig-strategy-corpus/0.1"}),
                timeout=30).read())
        o = json.loads(subprocess.run(
            [J, "check", "--image", p, "--b64", "--json",
             "--question", Q, "--rubric", R,
             "--subject", f"corpus.image:{x['id']}"],
            capture_output=True, text=True, timeout=120).stdout)
        return {"id": x["id"], "candidate": x["label"], "jev_label": o.get("label"),
                "probabilities": o.get("probabilities"), "judge": o.get("judge")}
    except Exception as e:
        return {"id": x["id"], "candidate": x["label"], "error": str(e)[:120]}

rows = [r for r in (json.loads(l) for l in open(inp)) if r["id"] not in confirmed]
n = 0
with open(out, "a") as f, ThreadPoolExecutor(4) as ex:
    for r in ex.map(one, rows):
        if r:
            f.write(json.dumps(r) + "\n"); f.flush(); n += 1
            if n % 50 == 0:
                print(f"{n}/{len(rows)}", flush=True)
print(f"finished {n} of {len(rows)}", flush=True)
