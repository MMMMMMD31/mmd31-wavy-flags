#!/usr/bin/env python3
"""Club badges for Belgian amateur VV D4/D5 from Foot24 team identity pages.
Only match explicit 2026-27 named clubs in the SAME group. No generic replacements."""
import csv,concurrent.futures,json,io,unicodedata,re,hashlib,time,urllib.parse
from pathlib import Path
from collections import deque,defaultdict
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from PIL import Image,ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES=True
ROOT=Path("docs/belgian-d4-d5-2026-27/v17")
ROSTER=list(csv.DictReader((ROOT/"rosters.csv").open()))
PAGES={
 "D4_VV_A":"https://www.foot24.be/nl/competities/2de-afdeling-voetb-vl-a-5",
 "D4_VV_B":"https://www.foot24.be/nl/competities/2de-afdeling-voetb-vl-b-5",
 "D5_VV_A":"https://www.foot24.be/nl/competities/3de-afdeling-voetb-vl-a-5",
 "D5_VV_B":"https://www.foot24.be/nl/competities/3de-afdeling-voetb-vl-b-5",
 "D4_FFA":"https://www.foot24.be/nl/competities/2e-nationale-5",
}
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 source-based crest database 2026)"})
def norm(n):
 n=unicodedata.normalize('NFKD',n.casefold()).encode('ascii','ignore').decode()
 n=re.sub(r'[^a-z0-9]+',' ',n)
 return re.sub(r'\s+',' ',n).strip()
EXTRAS={'KFC De Kempen TL':'KFC DE KEMPEN TIELEN-LICHTAART','RC Hades Kiewit':'RC HADES KIEWIT HASSELT',
        'K Racing Mechelen':'KRC MECHELEN','KVCSV Oostkamp':'KSV OOSTKAMP',
        'KVC Lille United':'KVC LILLE UNITED','K Berg en Dal VV':'K BERG EN DAL VV',
        'Eendracht Aalst Lede':'KONINKLIJKE EENDRACHT AALST LEDE','Avanti Stekene':'AVANTI STEKENE',
        'KVC Wilrijk':'KVC WILRIJK','KV Mechelen B':'YELLOW RED KV MECHELEN'}
stop={'k','fc','kfc','r','v','vv','sv','ksv','rc','rfc','royal','koninklijke','sport','a','b'}
def tok(n):return set(norm(n).split())-stop
indexed={};page_meta={}
for group,url in PAGES.items():
 try:
  r=s.get(url,timeout=18);r.raise_for_status()
  soup=BeautifulSoup(r.content,"html.parser")
  teams=defaultdict(set)
  for a in soup.select('a[href*="/clubs/"]'):
   label=a.get_text(" ",strip=True)
   if not label or len(label)>100:continue
   span=a.parent
   img=span.find('img') if span else None
   if img:
    src=img.get("src") or img.get("data-src")
    if src and re.search(r'/logos/\d+\.(?:jpg|jpeg|png|webp)',src,re.I):
     teams[(label,urllib.parse.urljoin(url,src))].add(a.get("href"))
  indexed[group]=[{"label":lab,"src":src,"clubPages":list(links)} for (lab,src),links in teams.items()]
  page_meta[group]={"status":r.status_code,"count":len(indexed[group]),"url":url}
 except Exception as e:
  indexed[group]=[]
  page_meta[group]={"error":str(e)[:240],"url":url}
 print(group,page_meta[group],flush=True)
matched=[];missed=[];ambiguous=[]
for row in ROSTER:
 id_,name,group=int(row["id"]),row["name"],row["group"]
 if row["crestStatus"]=="PARENT_REUSED":
  matched.append({"id":id_,"name":name,"group":group,"status":"PARENT_REUSED_IN_JSON"})
  continue
 candidates=[]
 for p in indexed.get(group,[]):
  stem=EXTRAS.get(name,name)
  # Fuzzy lexical matching uses same real-season group, minimizing same-name cross-club cases.
  a,b=norm(stem),norm(p["label"])
  overlap=len(tok(stem)&tok(p["label"]))
  score=max(fuzz.ratio(a,b),fuzz.token_set_ratio(a,b)*0.90)
  if a==b:score=100
  candidates.append((score,overlap,p))
 candidates.sort(key=lambda z:(z[0],z[1]),reverse=True)
 if not candidates or candidates[0][0]<72 or candidates[0][1]<1:
  missed.append({"id":id_,"name":name,"group":group,"status":"UNMATCHED_FOOT24","candidates":[{"name":p["label"],"score":round(sc,1)} for sc,ol,p in candidates[:3]]})
  continue
 best=candidates[0]
 if len(candidates)>1 and candidates[1][0]>(best[0]-7) and candidates[1][0]>=72:
  ambiguous.append({"id":id_,"name":name,"group":group,"status":"AMBIGUOUS","top":[{"label":p["label"],"score":round(sc,1)} for sc,_,p in candidates[:4]]})
  continue
 matched.append({"id":id_,"name":name,"group":group,"status":"CANDIDATE","sourceTeam":best[2]["label"],"matchConfidence":round(best[0],1),"source":best[2]["src"],"sourcePage":PAGES[group],"sourceClubPages":best[2]["clubPages"]})
def alpha_on_white(img):
 im=img.convert('RGBA')
 im.thumbnail((460,460),Image.Resampling.LANCZOS)
 w,h=im.size;px=im.load();q=deque()
 def white(x,y):
  r,g,b,a=px[x,y];return a>0 and min(r,g,b)>=242 and max(r,g,b)-min(r,g,b)<13
 for x in range(w):
  if white(x,0):q.append((x,0))
  if white(x,h-1):q.append((x,h-1))
 for y in range(h):
  if white(0,y):q.append((0,y))
  if white(w-1,y):q.append((w-1,y))
 seen=set()
 while q:
  x,y=q.popleft()
  if (x,y) in seen or not white(x,y):continue
  seen.add((x,y));px[x,y]=(255,255,255,0)
  for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=nx<w and 0<=ny<h and (nx,ny) not in seen:q.append((nx,ny))
 b=im.getchannel("A").getbbox()
 return im.crop(b) if b else im
def fetch(row):
 if row["status"]!="CANDIDATE":return row
 try:
  r=s.get(row["source"],timeout=20);r.raise_for_status()
  original=Image.open(io.BytesIO(r.content)).convert("RGBA")
  if min(original.size)<48:raise ValueError("resolution source trop faible")
  crest=alpha_on_white(original)
  if min(crest.size)<24:raise ValueError("emblem too small")
  crest.thumbnail((98,81),Image.Resampling.LANCZOS)
  pix=[px for px in crest.resize((55,55)).getdata() if px[3]>170 and max(px[:3])-min(px[:3])>42]
  if pix:
   # color from sampled crest, pale background for emblem legibility
   cr,cg,cb=max(pix,key=lambda p:max(p[:3])-min(p[:3]))[:3]
   bg=tuple(int(v*.25+235*.75) for v in (cr,cg,cb))
  else:bg=(221,226,233)
  canvas=Image.new("RGBA",(120,96),(*bg,255))
  canvas.alpha_composite(crest,((120-crest.width)//2,(96-crest.height)//2))
  dst=ROOT/(str(row["id"])+".png")
  canvas.convert("RGB").save(dst,optimize=True)
  if dst.stat().st_size<1000:raise ValueError("suspected near-empty crest")
  row.update(status="SOURCE_LINKED_PUBLISHED",sourceDimensions=list(original.size),background=bg,sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
             url="https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-d4-d5-v17-crests-fast/"+dst.as_posix())
 except Exception as e:row.update(status="SOURCE_FETCH_FAILED",error=str(e)[:200])
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 results=list(pool.map(fetch,matched))
assets=results+missed+ambiguous
result={"page_meta":page_meta,"assets":assets,"published":sum(z["status"]=="SOURCE_LINKED_PUBLISHED" for z in assets),"parent":sum(z["status"]=="PARENT_REUSED_IN_JSON" for z in assets),
"unmatched":len(missed),"ambiguous":len(ambiguous)}
(ROOT/"foot24_crest_status.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print("SOURCED",result["published"],"PARENT",result["parent"],"UNMATCHED",len(missed),"AMBIGUOUS",len(ambiguous),flush=True)
for m in (missed+ambiguous):print("MISSING",m["group"],m["name"],m["status"],str(m.get("candidates",m.get("top")))[:110],flush=True)
