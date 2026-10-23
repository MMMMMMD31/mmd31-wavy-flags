#!/usr/bin/env python3
"""Lots 6: overseas Pacific + Saint-Martin + Saint-Pierre-et-Miquelon crests.
Only unambiguous real crest logos from a matching encyclopedic club article
or a matching territory-confirmed football club record. Never use page photos.
"""
import csv,re,io,hashlib,unicodedata,collections,json,colorsys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import quote,urljoin
from difflib import SequenceMatcher
import requests
from bs4 import BeautifulSoup
from PIL import Image
import imagehash
ROSTER=Path("audit/outremer-2026-27/roster_326.csv")
ROOT=Path("flags/clubs/standard/outremer-2026-27");ROOT.mkdir(parents=True,exist_ok=True)
AUDIT=Path("audit/outremer-2026-27/lot6_pacific_saintmartin_spm_audit.csv")
HEAD={"User-Agent":"MMD31OverseasBadges/1.0 (+https://github.com/MMMMMMD31/mmd31-wavy-flags; club badge research)"}
MANUAL={
"1990262000283":["Association sportive saint-pierraise"],"1990262000284":["Association sportive ilienne amateurs"],"1990262000285":["Association sportive miquelonnaise"],
"1990262000292":["Association sportive Arue"],"1990262000294":["Association sportive Vénus"],
"1990262000295":["Association sportive Olympic Mahina"],"1990262000296":["Association sportive Mataiea"],
"1990262000297":["Association sportive Manu-Ura"],"1990262000299":["Association sportive Excelsior (Tahiti)"],
"1990262000300":["AS Dragon (Tahiti)"],"1990262000302":["Association sportive Pirae"],"1990262000304":["Association sportive Central Sport"],
"1990262000306":["Association sportive Tamarii Punaruu"],"1990262000309":["Association sportive Tiare Tahiti"],
"1990262000317":["Association sportive Magenta"],"1990262000318":["Association sportive Gaïca"],
"1990262000320":["Association sportive Lössi"],"1990262000321":["Hienghène Sport"],"1990262000322":["Association sportive Kunié"],
"1990262000323":["Sporting Club Ne Drehu"],"1990262000326":["Association sportive du Mont-Dore"],
"1990262000286":["Football Club Concordia Saint Martin"],"1990262000287":["Phoenicks FC Saint Martin"],
}
TERRITORY={"Saint-Martin":("Saint-Martin","Saint Martin"),"Saint-Pierre-et-Miquelon":("Saint-Pierre","Miquelon"),
"Polynésie française":("Tahiti","Polynésie","Moorea"),"Nouvelle-Calédonie":("Nouvelle-Calédonie","New Caledonia","Calédonie")}
FFF=[]
for tid in (1990262000021,1990262000111):
 p=Path("audit/outremer-2026-27/quarantine")/(str(tid)+".png")
 if p.exists():
  with Image.open(p) as i:FFF.append(imagehash.phash(i.convert("RGB").crop((10,5,110,94))))
def norm(s):
 s=unicodedata.normalize("NFKD",s or "");s="".join(x for x in s if not unicodedata.combining(x))
 return re.sub(r"[^a-z0-9]+"," ",s.lower()).strip()
def score(a,b):return SequenceMatcher(None,norm(a),norm(b)).ratio()
def get(url):
 r=requests.get(url,headers=HEAD,timeout=16);r.raise_for_status();return r
def candidate(tid,name,terr):
 aliases=[name]+MANUAL.get(tid,[])
 choices=[]
 for alias in aliases:
  choices.append("https://fr.wikipedia.org/wiki/"+quote(alias.replace(" ","_")))
  choices.append("https://en.wikipedia.org/wiki/"+quote(alias.replace(" ","_")))
 # Prefer French Wikipedia exact article, not search result: avoids homonyms
 return list(dict.fromkeys(choices))[:8]
def extract(soup,url,tid,name,territory):
 h=soup.find("h1")
 if not h:raise ValueError("no_h1")
 title=h.get_text(" ",strip=True).replace(" — Wikipédia","")
 targets=[name]+MANUAL.get(tid,[])
 sim=max(score(title,t) for t in targets)
 if sim<0.69:raise ValueError("article_identity_not_confirmed")
 body=soup.get_text(" ",strip=True)
 if not any(key.lower() in body.lower() for key in TERRITORY[territory]):raise ValueError("territory_mismatch")
 infobox=soup.select_one("table.infobox") or soup.select_one(".infobox")
 if infobox is None:raise ValueError("no_infobox")
 found=[]
 for im in infobox.find_all("img"):
  src=im.get("src") or im.get("data-src") or ""
  alt=im.get("alt","")
  if not src:continue
  text=(alt+" "+src).lower()
  if not re.search(r"logo|écusson|blason|crest|emblem",text):continue
  if re.search(r"wikimedia-logo|commons-logo|fifa|fff\.png|flag_|kit_",text):continue
  if src.startswith("//"):src="https:"+src
  urlimg=urljoin(url,src)
  found.append(urlimg)
 if len(found)!=1:raise ValueError("no_unique_infobox_crest")
 return title,found[0],sim
def process(r):
 tid=r["team_id"];name=r["name"];terr=r["territory"];dst=ROOT/(tid+".png")
 if dst.exists() and dst.stat().st_size>600:
  return [tid,name,terr,"already_published","","","previously_validated"]
 errors=[]
 for url in candidate(tid,name,terr):
  try:
   resp=get(url)
   if "wiki" not in resp.url:raise ValueError("not_wikipedia")
   soup=BeautifulSoup(resp.text,"html.parser")
   title,imgurl,sim=extract(soup,resp.url,tid,name,terr)
   raw=get(imgurl).content
   with Image.open(io.BytesIO(raw)) as tmp:tmp.verify()
   logo=Image.open(io.BytesIO(raw)).convert("RGBA")
   if min(logo.size)<30:raise ValueError("small image")
   logo.thumbnail((104,86),Image.Resampling.LANCZOS)
   colors=collections.Counter()
   for red,green,blue,a in logo.getdata():
    if a<128:continue
    h,s,v=colorsys.rgb_to_hsv(red/255,green/255,blue/255)
    if s>.28 and .17<v<.95:colors[(red//40,green//40,blue//40)]+=1
   key=colors.most_common(1)[0][0] if colors else (5,5,5)
   bg=tuple(min(255,round((x*40+20)*.5+255*.5)) for x in key)
   im=Image.new("RGBA",(120,96),bg);im.alpha_composite(logo,((120-logo.width)//2,(96-logo.height)//2))
   im=im.convert("RGB")
   h=imagehash.phash(im.crop((10,5,110,94)))
   if any(h-p<=8 for p in FFF):raise ValueError("FFF_placeholder")
   buf=io.BytesIO();im.save(buf,format="PNG",optimize=True)
   if len(buf.getvalue())<650:raise ValueError("too_small_png")
   dst.write_bytes(buf.getvalue())
   return [tid,name,terr,"published",resp.url,imgurl,f"article_title={title};similarity={sim:.2f}"]
  except Exception as exc:errors.append(str(exc)[:80])
 return [tid,name,terr,"not_verified","","",";".join(dict.fromkeys(errors))[:300]]
with ROSTER.open(encoding="utf8",newline="") as f:rows=[r for r in csv.DictReader(f) if r["territory"] in TERRITORY]
assert len(rows)==44,len(rows)
results=[]
with ThreadPoolExecutor(max_workers=6) as pool:
 for fut in as_completed([pool.submit(process,r) for r in rows]):results.append(fut.result())
results.sort(key=lambda r:int(r[0]))
# Safety: images with identical file bytes for different new club IDs are not automatically accepted.
byhash=collections.defaultdict(list)
for row in results:
 if row[3] in ("published","already_published"):
  byhash[hashlib.sha256((ROOT/(row[0]+".png")).read_bytes()).hexdigest()].append(row)
for same in byhash.values():
 if len(same)>1:
  for row in same:
   if row[3]=="published":
    (ROOT/(row[0]+".png")).unlink(missing_ok=True)
    row[3]="duplicate_uncertain";row[6]="same_image_multiple_team_ids"
with AUDIT.open("w",encoding="utf8",newline="") as f:
 writer=csv.writer(f);writer.writerow(["team_id","club","territory","status","source_page","image_url","explanation"]);writer.writerows(results)
print(json.dumps({"count":len(results),"status":dict(collections.Counter(r[3] for r in results)),"failed":[r[:4] for r in results if r[3] not in ("published","already_published")]},ensure_ascii=False),flush=True)
