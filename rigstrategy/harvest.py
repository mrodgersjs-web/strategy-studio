import json,urllib.request,urllib.parse,hashlib,sys
Q=["SWOT analysis","Porter five forces","BCG matrix","Ansoff matrix","value chain diagram","business model canvas","Eisenhower matrix","issue tree","decision tree diagram","scenario planning","Wardley map","strategy map","balanced scorecard","PEST analysis","value stream mapping","fishbone diagram","flowchart business","Gantt chart","mind map","organizational chart","break-even chart","sensitivity analysis tornado","pareto chart","radar chart","stakeholder matrix","risk matrix","customer journey map","technology adoption lifecycle","product life cycle","experience curve","GE McKinsey matrix","OKR","logic model","theory of change","causal loop diagram","stock and flow diagram","Venn diagram business","waterfall chart","Sankey diagram","2x2 matrix"]
seen=set();out=open('corpus/good/index.jsonl','w');n=0
for q in Q:
  for off in (0,50):
    u="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","format":"json","generator":"search","gsrnamespace":6,"gsrsearch":q,"gsrlimit":50,"gsroffset":off,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":320})
    try: d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"rig-strategy-corpus/0.1 (mrodgersjs@gmail.com)"}),timeout=30))
    except Exception as e: print("err",q,e,file=sys.stderr); continue
    for p in d.get("query",{}).get("pages",{}).values():
      ii=(p.get("imageinfo") or [{}])[0]; url=(ii.get("url") or "").split("?")[0]
      if not url or url in seen or not url.lower().endswith((".png",".svg",".jpg",".jpeg")): continue
      seen.add(url); md=ii.get("extmetadata",{})
      out.write(json.dumps({"id":hashlib.sha256(url.encode()).hexdigest()[:16],"query":q,"title":p["title"],"url":url,"thumb":ii.get("thumburl"),"page":ii.get("descriptionurl"),"license":md.get("LicenseShortName",{}).get("value"),"label":"candidate-good"})+"\n"); n+=1
print(n)
