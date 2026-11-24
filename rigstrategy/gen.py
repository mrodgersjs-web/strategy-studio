import json,os,pathlib
R=pathlib.Path(os.path.expanduser("~/.aside/u/0/skills/user"))
methods=[m['id'] for m in json.load(open('src/strategy_studio/data/methods.json'))['methods']]
stages=["frame","diagnose","options","numbers","stress","commit","operate","visual-quality","antipattern","learn"]
def w(name,desc,body):
    d=R/name; d.mkdir(parents=True,exist_ok=True)
    (d/"SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\n{body}\n")
n=0
for s in stages:
    kids=[f"rs-{m}-{s}" for m in methods]
    w(f"rs-{s}",f"Stage metaskill '{s}' of /rigstrategy: routes to one rs-<method>-{s} step skill per strategy method. Child of rigstrategy.",
      "Pick the child whose method strategy-studio routed:\n"+"\n".join(f"- `{k}`" for k in kids)+"\n\nGate: Jev before done; drafts only.")
    for m in methods:
        w(f"rs-{m}-{s}",f"Step '{s}' for the {m} strategy method in /rigstrategy. Use when strategy-studio routed to {m} and the run is at stage {s}. Child of rs-{s}.",
f"""## Input
Routed question, worksheet from `strategy-studio route --json`, audit hash.
## Do
1. Read the {m} worksheet fields for stage {s}.
2. Produce the {s} output; every number cites a source or is marked UNVERIFIED.
3. For visuals: compare against corpus/good nearest neighbours and corpus/bad antipatterns.
## Output
Append to the run worksheet; audit append via post-route hook.
## Done when
Output present, sources cited, Jev PASS (DEFERRED if unreachable).
"""); n+=1
for a in ["framer","analyst","red-teamer","numbers-checker","visual-judge","goldfish-verifier"]:
    w(f"rs-agent-{a}",f"/rigstrategy agent persona: {a}. Load when the orchestrator dispatches the {a} role.",f"Role: {a}. Verifier never sees builder context.")
for h in ["pre-route-redact","post-route-audit","pre-done-jev","post-run-learn"]:
    w(f"rs-hook-{h}",f"/rigstrategy hook {h}.",f"Run `rigstrategy/hooks/{h}.sh`; non-zero blocks.")
for l in ["improve-loop","eval-loop","corpus-refresh-loop"]:
    w(f"rs-loop-{l}",f"/rigstrategy loop {l}.",f"Bounded loop; stops on budget or no-progress x3.")
w("rs-harness","/rigstrategy harness: question -> route -> worksheet -> stages -> gate -> audit receipt.","Pipeline: pre-route-redact, strategy-studio route --json, rs-<stage> chain, pre-done-jev, post-run-learn.")
w("rs-meta-harness","/rigstrategy meta-harness: Pareto search over step-skill prompts on a fixed eval set; model fixed.","Eval: examples/sample-questions.txt + labelled set; keep only variants that beat baseline accuracy.")
stg="\n".join(f"- `rs-{s}`" for s in stages)
w("rigstrategy","RIG strategy orchestrator (/rigstrategy): routes a business question deterministically through strategy-studio to one of 11 methods, then 10 stage metaskills x 11 methods (110 step skills), 6 agents, 4 hooks, 3 loops, harness and meta-harness, with a good/bad visual corpus gate. Wraps /strategy; drafts only.",
f"""Repo: ~/Developer/strategy-studio (mrodgersjs-web/strategy-studio).
## Run
1. `strategy-studio route --json "<question>"` -> method + score + audit hash.
2. Walk stages:\n{stg}
3. Harness `rs-harness`; verify with `rs-agent-goldfish-verifier`; Jev gate.
## Relation
Wraps `/strategy` (65 strat- steps) — strategy owns doctrine, rigstrategy owns the routed run.
## Corpus
`corpus/good/index.jsonl` (target 1000), `corpus/bad/index.jsonl` (target 300); URL+hash+tags only.
""")
print("steps",n)
