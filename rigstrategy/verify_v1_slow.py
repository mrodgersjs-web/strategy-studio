import json,subprocess,urllib.request,os,sys
from concurrent.futures import ThreadPoolExecutor
J=os.path.expanduser("~/.rig/bin/jev-image");D="/tmp/rsimg";os.makedirs(D,exist_ok=True)
Q="Is this chart clean and readable, with labelled axes or parts and a clear title?"
R="yes_clean_readable|no_cluttered_or_unlabelled"
out=sys.argv[2]; done={json.loads(l)["id"] for l in open(out)} if os.path.exists(out) else set()
def one(x):
  if x["id"] in done or not (x.get("thumb") or x.get("path")): return None
  p=f"{D}/{x['id']}.png"
  try:
    if x.get("path"): p=x["path"]
    elif not os.path.exists(p): open(p,"wb").write(urllib.request.urlopen(urllib.request.Request(x["thumb"],headers={"User-Agent":"rig-strategy-corpus/0.1"}),timeout=30).read())
    o=json.loads(subprocess.run([J,"check","--image",p,"--b64","--json","--question",Q,"--rubric",R,"--subject",f"corpus.image:{x['id']}"],capture_output=True,text=True,timeout=120).stdout)
    return {"id":x["id"],"candidate":x["label"],"jev_label":o.get("label"),"probabilities":o.get("probabilities"),"judge":o.get("judge")}
  except Exception as e: return {"id":x["id"],"candidate":x["label"],"error":str(e)[:120]}
rows=[json.loads(l) for l in open(sys.argv[1])]
with open(out,"a") as f, ThreadPoolExecutor(2) as ex:
  for r in ex.map(one,rows):
    if r: f.write(json.dumps(r)+"\n"); f.flush()
print("finished")
