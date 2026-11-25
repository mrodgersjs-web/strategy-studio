import json,random,hashlib,os,matplotlib
matplotlib.use("Agg");import matplotlib.pyplot as plt
D="corpus/rendered";os.makedirs(D,exist_ok=True);rnd=random.Random(7)
W=["Market growth","Share","Cost","Value","Risk","Impact","Certainty","Effort","Evolution","Visibility"]
def save(fig,kind,label,law=None):
  p=f"{D}/{kind}-{label}-{rnd.getrandbits(40):x}.png";fig.savefig(p,dpi=80);plt.close(fig)
  return {"id":hashlib.sha256(p.encode()).hexdigest()[:16],"query":kind,"title":p,"thumb":None,"path":p,"license":"owned (RIG-rendered)","label":"candidate-"+label,**({"antipattern":law} if law else {})}
def quad(good):
  f,a=plt.subplots(figsize=(5,4));x,y=rnd.sample(W,2)
  if good:
    a.axhline(.5,c="#888",lw=1);a.axvline(.5,c="#888",lw=1)
    for i,t in enumerate(["Invest","Grow","Harvest","Exit"]):a.text(.25+.5*(i%2),.75-.5*(i//2),t,ha="center",fontsize=11,color="#333")
    for _ in range(rnd.randint(3,6)):a.scatter(rnd.random(),rnd.random(),s=rnd.randint(60,300),alpha=.6,c="#2a6f97")
    a.set(xlim=(0,1),ylim=(0,1),xlabel=x,ylabel=y,title=f"{y} vs {x}: where to invest");a.set_xticks([]);a.set_yticks([])
  else:
    f.patch.set_facecolor(rnd.choice(["#ff00ff","#00ff00","#ffff00"]))
    for _ in range(25):a.scatter(rnd.random(),rnd.random(),s=rnd.randint(50,900),c=[[rnd.random() for _ in range(3)]])
    a.text(.1,.5,"SYNERGY!!! LEVERAGE!!!",fontsize=20,rotation=rnd.randint(-30,30))
  return f
def bars(good):
  f,a=plt.subplots(figsize=(5,4));v=[rnd.randint(20,100) for _ in range(5)];l=["A","B","C","D","E"]
  if good:
    o=sorted(zip(v,l));a.barh([x[1] for x in o],[x[0] for x in o],color=["#bbb"]*4+["#2a6f97"]);a.set_title(f"Segment {o[-1][1]} drives most revenue");a.set_xlabel("Revenue ($k)");[a.spines[s].set_visible(False) for s in("top","right")]
  else:
    a.bar(l,v,color=[[rnd.random() for _ in range(3)] for _ in v],hatch="//",edgecolor="k");a.set_ylim(min(v)-5,max(v)+1);a.grid(lw=2)
  return f
def waterfall(good):
  f,a=plt.subplots(figsize=(5,4));s=["Price","COGS","CAC","Support","Margin"];v=[100,-rnd.randint(20,40),-rnd.randint(10,25),-rnd.randint(5,10)];c=0
  for i,x in enumerate(v):
    a.bar(s[i],x,bottom=c if x<0 else 0,color=("#2a6f97" if x>0 else "#c44") if good else [[rnd.random() for _ in range(3)]]);c+=x
  a.bar(s[4],c,color="#2a6f97" if good else "yellow")
  if good:a.set_title(f"Unit economics: ${c} contribution per unit");a.set_ylabel("$ per unit")
  else:a.set_xticks([]);a.set_yticks([])
  return f
def tree(good):
  f,a=plt.subplots(figsize=(5,4));a.axis("off")
  if good:
    a.text(.05,.5,"Decision",bbox=dict(fc="#eef"),fontsize=10)
    for i,(o,p) in enumerate([("Build",rnd.randint(30,60)),("Buy",rnd.randint(20,50)),("Wait",rnd.randint(5,20))]):
      y=.85-.35*i;a.annotate("",(.45,y),(.22,.5),arrowprops=dict(arrowstyle="->"));a.text(.47,y,f"{o}: EV ${p}k",bbox=dict(fc="#efe"),fontsize=10)
    a.set_title("Option tree: Build has highest expected value")
  else:
    for _ in range(30):a.plot([rnd.random(),rnd.random()],[rnd.random(),rnd.random()],lw=rnd.randint(1,4))
    for _ in range(12):a.text(rnd.random(),rnd.random(),"option?",fontsize=rnd.randint(6,16))
  return f
def pie(good):
  f,a=plt.subplots(figsize=(5,4))
  if good:
    v=[rnd.randint(30,60),rnd.randint(10,30),rnd.randint(5,15)];a.barh(["Core","Adjacent","Transformational"],v,color="#2a6f97");a.set_title("Innovation portfolio mix (%)");a.set_xlabel("% of budget")
  else:
    v=[rnd.randint(1,10) for _ in range(14)];a.pie(v,explode=[.1]*14,shadow=True,startangle=rnd.randint(0,360))
  return f
law={"quad":"chartjunk, neon background, buzzwords, no axes","bars":"truncated axis, rainbow colors, heavy grid, no title","waterfall":"no labels or scale, random colors","tree":"spaghetti, no structure or values","pie":"14-slice exploded 3D-style pie"}
G={"quad":quad,"bars":bars,"waterfall":waterfall,"tree":tree,"pie":pie}
rows=[]
for k,fn in G.items():
  for _ in range(280):rows.append(save(fn(True),k,"good"))
  for _ in range(80):rows.append(save(fn(False),k,"bad",law[k]))
open("corpus/rendered/index.jsonl","w").writelines(json.dumps(r)+"\n" for r in rows);print(len(rows))
