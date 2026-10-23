#!/usr/bin/env python3
import json,io,re,time,random,hashlib,threading,concurrent.futures
from pathlib import Path
from urllib.parse import quote,urlsplit
from collections import Counter
import requests
from bs4 import BeautifulSoup
from PIL import Image
rows=json.loads(Path("tools/english_clubs_d8_d9_2026_27_sources.json").read_text(encoding="utf8"))
todo=[r for r in rows if not r.get("source_path")]
assert len(todo)==417
dest=Path("docs/english-clubs-2026-27/wiki-v13")
dest.mkdir(parents=True,exist_ok=True)
local=threading.local()
def client():
 if not hasattr(local,"s"):
  local.s=requests.Session()
  local.s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 2026 English football historical badge research)"})
 return local.s
def fetch(url):
 for k in range(4):
  try:
   r=client().get(url,timeout=21)
   if r.status_code in (429,500,502,503,504) and k<3:
    time.sleep((k+1)*1.7+random.random());continue
   return r
  except requests.RequestException:
   if k==3:raise
   time.sleep((k+1)*1.1)
def key(x):
 x=x.lower().replace("’","'").replace("&","and").replace("community","")
 x=re.sub(r"(?i)association football club|football club|a\.?f\.?c\.?|f\.?c\.?","",x)
 return re.sub(r"[^a-z0-9]","",x)
def candidates(name):
 t=[name+" F.C.",name+" A.F.C."]
 if name.startswith("AFC "):t+=["A.F.C. "+name[4:],name]
 elif name.startswith("FC "):t+=["F.C. "+name[3:],name]
 else:t+=[name]
 if name.endswith(" Community"):t+=[name.replace(" Community","")+" F.C."]
 return list(dict.fromkeys(t))
def retrieve(row):
 name=row["name"];errors=[]
 for candidate in candidates(name):
  url="https://en.wikipedia.org/wiki/"+quote(candidate.replace(" ","_"),safe="()_.")
  try:
   h=fetch(url)
   if h.status_code!=200:continue
   soup=BeautifulSoup(h.content,"html.parser")
   title=(soup.title.get_text(" ",strip=True) if soup.title else "").replace(" - Wikipedia","")
   if key(title)!=key(name):continue
   imgs=[]
   for tag in soup.select("table.infobox img")[:7]:
    src=tag.get("src") or ""
    if src.startswith("//"):src="https:"+src
    src=src.split("?")[0]
    if not src.startswith("https://") or "wikimedia.org" not in urlsplit(src).netloc:continue
    if not re.search(r"\.(png|jpg|jpeg|webp)$",src,re.I):continue
    imgfile=src.split("/")[-1].lower()
    if any(word in imgfile for word in ("kit","shirt","stadium","ground","away","home-colour")):continue
    tokens=[k.lower() for k in re.findall("[a-zA-Z]{4,}",name) if k.lower() not in ("town","city","united","football","sporting","community")]
    if not any(x in imgfile for x in ("badge","logo","crest","emblem")) and not any(x in imgfile.replace("_","") for x in tokens):continue
    imgs.append(src)
   if not imgs:continue
   img=fetch(imgs[0])
   if img.status_code!=200 or not img.headers.get("content-type","").startswith("image/"):continue
   original=Image.open(io.BytesIO(img.content)).convert("RGBA")
   if original.width<20 or original.height<20:continue
   original.thumbnail((99,82),Image.Resampling.LANCZOS)
   small=original.copy();small.thumbnail((55,55))
   colors=Counter()
   for red,green,blue,a in small.getdata():
    if a>120 and max(red,green,blue)-min(red,green,blue)>=32:
     colors[(red//32,green//32,blue//32)]+=1
   if colors:
    rgb=tuple(min(255,v*32+16) for v in colors.most_common(1)[0][0])
   else:rgb=(50,70,95)
   bgcolor=tuple(round(.7*x+.3*255) for x in rgb)
   canvas=Image.new("RGBA",(120,96),bgcolor+(255,))
   canvas.alpha_composite(original,((120-original.width)//2,(96-original.height)//2))
   destfile=dest/(str(row["id"])+".png")
   canvas.convert("RGB").save(destfile,"PNG",optimize=True)
   return {"id":row["id"],"name":name,"status":"PUBLISHED_REAL_WIKIPEDIA_INFOBOX","wikipedia_article":url,"verified_page_title":title,"source_logo":imgs[0],"github_path":str(destfile),"bytes":destfile.stat().st_size,"rgb":bgcolor}
  except Exception as e:errors.append(str(e)[:100])
 return {"id":row["id"],"name":name,"status":"NO_VERIFIED_REAL_IMAGE","errors":errors[:3]}
found=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 fs=[pool.submit(retrieve,row) for row in todo]
 for n,f in enumerate(concurrent.futures.as_completed(fs),1):
  found.append(f.result())
  if n%30==0:print("Done",n,"/",len(todo),"images",sum(z["status"].startswith("PUBLISHED") for z in found),flush=True)
found.sort(key=lambda z:z["id"])
status={"expected":417,"published":sum(z["status"].startswith("PUBLISHED") for z in found),"unverified":sum(not z["status"].startswith("PUBLISHED") for z in found),"files":found,"source":"English Wikipedia infobox image (authentic existing club crest); individual visual review still recommended"}
(dest/"manifest.json").write_text(json.dumps(status,indent=2,ensure_ascii=False),encoding="utf8")
print("Finished",status["published"],"of",status["expected"],flush=True)
