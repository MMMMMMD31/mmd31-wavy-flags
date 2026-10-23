#!/usr/bin/env python3
"""Spanish D5 2026/27 authentic crest candidate capture, v13. Never invent logos."""
import argparse,io,json,hashlib,requests,unicodedata,re,time
from pathlib import Path
from bs4 import BeautifulSoup
from rapidfuzz.fuzz import ratio
from scipy.optimize import linear_sum_assignment
from PIL import Image
from collections import Counter
ROOT=Path("docs/spanish-clubs-2026-27/v13")
ROOT.mkdir(parents=True,exist_ok=True)
ROSTER=json.loads(Path("data/spanish_d5_2026_27_roster.json").read_text(encoding="utf-8"))["groups"]
session=requests.Session()
session.headers["User-Agent"]="MMD31 Spanish football logos 2026/27 (noncommercial game data, source verification)"
SKIP={"9|Málaga Juniors","12|Laguna","14|Montijo","17|Internacional Huesca","1|Montañeros"}
ALIASES={
"1|Racing Villalbés":"Villalbés",
"4|Alavés C":"Deportivo Alavés C",
"6|Atlético Levante":"Levante B",
"6|Atlético Saguntino":"Saguntino",
"8|Atlético Bembibre":"Bembibre",
"9|Atlético Malagueño":"At. Malagueño",
"9|Atlético Marbella":"AD Atletico de Marbella",
"9|Atlético Mancha Real":"Mancha Real",
"16|Haro":"Haro Deportivo",
"2|Sporting Atlético":"Sporting Gijón B",
"3|Naval":"Naval Reinosa","3|Solares-Medio Cudeyo":"Solares",
"4|Aurrerá Vitoria":"Vitoria","4|Cultural Durango":"Durango",
"5|Vilanova":"Vilanova Geltrú",
"6|Athletic Torrellano":"Torrellano","6|Español San Vicente":"Jove Español",
"7|Moscardó":"Colonia Moscardo","7|Móstoles URJC":"Móstoles",
"7|Rayo Ciudad Alcobendas":"RC Alcobendas","7|San Sebastián de los Reyes B":"UD Sanse B",
"8|Calasanz":"Calasanz de Soria","8|Júpiter Leonés":"Cultural Leonesa B",
"8|Unionistas B":"Unionistas Salamanca B",
"9|Arenas":"Arenas Armilla","9|Churriana":"Churriana de la Vega",
"9|Recreativo Granada":"Granada B",
"10|Atlético Onubense":"Atl. Onubense","10|Cádiz Mirandilla":"Cádiz B","10|Dos Hermanas":"Dos Hermanas 1971",
"12|Añaza":"Anaza (Esp)","12|Los Llanos de Aridane":"Los Llanos",
"13|Minerva":"SFC Minerva","15|Avance":"Avance Ezcabarte",
"17|Tamarite":"CDJ Tamarite","17|Deportivo Aragón":"RZ Deportivo Aragón"
}
def norm(s):
 s=unicodedata.normalize("NFKD",s).encode("ASCII","ignore").decode().lower()
 s=re.sub(r"\b(fc|cf|cd|ud|sd|ce|ue|rc|rcd|cp|ad|sc|real|club|de|del|la|las|los|futbol|football)\b","",s)
 return re.sub(r"[^a-z0-9]+","",s)
def fetch_group(g):
 url=f"https://www.resultadosrfef.es/tercera-rfef/grupo-{g}/clasificacion"
 r=session.get(url,timeout=30);r.raise_for_status()
 soup=BeautifulSoup(r.content,"html.parser")
 for table in soup.find_all("table"):
  if not all(k in table.get_text(" ",strip=True) for k in ["Pts","PJ","GF","GC"]):continue
  out=[]
  for tr in table.find_all("tr")[1:]:
   tds=tr.find_all(["td","th"],recursive=False)
   if len(tds)<8:continue
   anchor=tds[1].find("a")
   if not anchor:continue
   name=anchor.get_text(" ",strip=True)
   img=anchor.find("img")
   src=requests.compat.urljoin(url,img.get("src")) if img and img.get("src") else None
   if name:out.append({"name":name,"url":src,"team_page":requests.compat.urljoin(url,anchor.get("href",""))})
  if 15<=len(out)<=20:return out,url
 raise RuntimeError("cannot parse real club logos for group "+str(g))
def match_names(g,names,found):
 # keep aliases explicit; for other clubs use independent global optimal matching
 scores=[]
 for name in names:
  key=str(g)+"|"+name
  explicit=ALIASES.get(key)
  srow=[]
  for item in found:
   if key in SKIP:v=-1000
   elif explicit:v=100 if norm(item["name"])==norm(explicit) else -100
   else:
    n,m=norm(name),norm(item["name"])
    v=100 if n==m else ratio(n,m)
   srow.append(v)
  scores.append(srow)
 import numpy as np
 a,b=linear_sum_assignment(-np.array(scores))
 matched={}
 for i,j in zip(a,b):
  score=scores[i][j]
  if score>=80 and found[j].get("url") and str(g)+"|"+names[i] not in SKIP:
   matched[names[i]]=(found[j],score)
 return matched
def bg_color(logo):
 counts=Counter()
 im=logo.copy();im.thumbnail((64,64))
 for r,g,b,a in im.getdata():
  if a<120 or max(r,g,b)-min(r,g,b)<40:continue
  counts[(r//32,g//32,b//32)]+=1
 if counts:
  rgb=counts.most_common(1)[0][0]
  return tuple(round((min(255,c*32+16))*.68+255*.32) for c in rgb)
 return (91,127,177)
def render(data):
 im=Image.open(io.BytesIO(data)).convert("RGBA")
 if im.width<24 or im.height<24:raise ValueError("upstream logo too small")
 # Remove only white pixels connected to the OUTSIDE edges of logo.
 w,h=im.size
 if w*h>1400000:im.thumbnail((700,700));w,h=im.size
 p=im.load();from collections import deque
 q=deque()
 for x in range(w):
  for y in (0,h-1):
   if min(p[x,y][:3])>238:q.append((x,y))
 for y in range(h):
  for x in (0,w-1):
   if min(p[x,y][:3])>238:q.append((x,y))
 seen=set()
 while q:
  x,y=q.popleft()
  if (x,y) in seen:continue
  seen.add((x,y))
  R,G,B,A=p[x,y]
  if min(R,G,B)<235:continue
  p[x,y]=(R,G,B,0)
  for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=nx<w and 0<=ny<h and (nx,ny) not in seen:q.append((nx,ny))
 box=im.getchannel("A").getbbox()
 if not box:raise ValueError("blank logo")
 im=im.crop(box)
 color=bg_color(im)
 out=Image.new("RGBA",(120,96),color+(255,))
 im.thumbnail((98,84),Image.Resampling.LANCZOS)
 out.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return out.convert("RGB"),color
def one(g):
 targets=ROSTER[str(g)];found,url=fetch_group(g)
 matched=match_names(g,targets,found)
 print("G",g,"roster",len(targets),"standings",len(found),"matches",len(matched),flush=True)
 records=[]
 for ix,name in enumerate(targets):
  id_=1884500100173+(g-1)*18+ix
  item=matched.get(name)
  rec={"id":id_,"name":name,"group":g,"status":"ÉCUSSON_RÉEL_NON_VÉRIFIÉ","source_standings":url}
  if not item:
   rec["reason"]="image missing or name not confidently matched"
  else:
   match,sim=item;rec.update(source_club=match["name"],source_image=match["url"],source_team_page=match["team_page"],match_score=sim)
   try:
    rr=session.get(match["url"],timeout=30);rr.raise_for_status()
    data=rr.content
    if len(data)<250:raise ValueError("empty or generic source")
    rendered,color=render(data)
    name_file=str(id_)+".png"
    path=ROOT/name_file;rendered.save(path,"PNG",optimize=True)
    assert Image.open(path).size==(120,96)
    rec.update(status="SOURCE_IMAGE_À_VALIDER_VISUELLEMENT",background_rgb=color,
      file_path=path.as_posix(),source_sha256=hashlib.sha256(data).hexdigest(),
      image_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
   except Exception as e:
    rec["reason"]=str(e)
  records.append(rec)
  if ix%6==5:print("G",g,"processed",ix+1,flush=True)
 out=Path(f"data/mmd31_es_v13_d5_g{g:02d}.json")
 out.parent.mkdir(exist_ok=True)
 out.write_text(json.dumps({"group":g,"count":len(records),"approved_by_human":False,"items":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("G",g,"PNGs",sum(x["status"].startswith("SOURCE_IMAGE") for x in records),flush=True)
 return records
if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--from-group",type=int,required=True);p.add_argument("--to-group",type=int,required=True);a=p.parse_args()
 for g in range(a.from_group,a.to_group+1):
  try:one(g)
  except Exception as e:print("ERROR GROUP",g,repr(e),flush=True)
