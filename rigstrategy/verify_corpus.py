import json,subprocess,urllib.request,os,sys
from concurrent.futures import ThreadPoolExecutor
J=os.path.expanduser("~/.rig/bin/jev-image");D="/tmp/rsimg";os.makedirs(D,exist_ok=True)
Q="Judge this image as a business chart or strategy diagram."
R="well_designed_chart_or_diagram|poorly_designed_or_misleading_chart|photo_or_not_a_chart"
out="corpus/verified.jsonl"; done={json.loads(l)["id"] for l in open(out)} if os.path.exists(out) else set()
def one(x):
  if x["id"] in done or not x.get("thumb"): return None
  p=f"{D}/{x['id']}.png"
  try:
    if not os.path.exists(p): open(p,"wb").write(urllib.request.urlopen(urllib.request.Request(x["thumb"],headers={"User-Agent":"rig-strategy-corpus/0.1"}),timeout=30).read())
    o=json.loads(subprocess.run([J,"check","--image",p,"--b64","--json","--question",Q,"--rubric",R,"--subject",f"corpus.image:{x['id']}"],capture_output=True,text=True,timeout=120).stdout)
    return {"id":x["id"],"candidate":x["label"],"jev_label":o.get("label"),"probabilities":o.get("probabilities"),"judge":o.get("judge")}
  except Exception as e: return {"id":x["id"],"candidate":x["label"],"error":str(e)[:120]}
rows=[json.loads(l) for k in("good","bad") for l in open(f"corpus/{k}/index.jsonl")]
with open(out,"a") as f, ThreadPoolExecutor(8) as ex:
  for r in ex.map(one,rows):
    if r: f.write(json.dumps(r)+"\n"); f.flush()
print("finished")
