#!/usr/bin/env python3
"""Find authentic club crests for Mayotte from matching SportCorico club pages.
NEVER use a site logo, placeholder, homonym, wrong territory or invent a crest.
Writes auditable statuses; auto-accepted images require a matching club title and territory.
Use verified 2026 Mayotte club aliases.
"""
import csv, re, io, os, hashlib, unicodedata, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from PIL import Image
import imagehash
FFF_TEMPLATES=[]
for _id in (1990262000021,1990262000111):
 _p=Path("audit/outremer-2026-27/quarantine")/(str(_id)+".png")
 if _p.exists():
  with Image.open(_p) as _im: FFF_TEMPLATES.append(imagehash.phash(_im.convert("RGB").crop((10,5,110,94))))

ROSTER=Path("audit/outremer-2026-27/roster_326.csv")
DEST=Path("flags/clubs/standard/outremer-2026-27")
DEST.mkdir(parents=True,exist_ok=True)
REPORT=Path("audit/outremer-2026-27/mayotte_crest_audit.csv")
REPORT.parent.mkdir(parents=True,exist_ok=True)
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; MMD31CrestAudit/2.0; +https://github.com/MMMMMMD31/mmd31-wavy-flags)"}
# Curated exact club URL aliases when the official FFF name and name in simulator differ.
URL_SLUGS={}
NAME_ALIASES={}
with Path("audit/outremer-2026-27/mayotte_aliases.csv").open(encoding="utf-8",newline="") as _f:
 for _r in csv.DictReader(_f):
  NAME_ALIASES.setdefault(_r["team_id"],[]).append(_r["alias"])
DIRECTORY={}
def build_index():
 for territory,url in [
  ("Mayotte","https://www.sportcorico.com/clubs-par-region/football/mayotte/mayotte")]:
  try:
   resp=requests.get(url,headers=HEADERS,timeout=20)
   resp.raise_for_status()
   html=BeautifulSoup(resp.text,"html.parser")
   choices=[]
   for a in html.select('a[href*="/clubs/"]'):
    href=a.get("href","")
    title=a.get_text(" ",strip=True)
    if not title or len(title)<3 or "clubs-par-region" in href: continue
    full=urljoin(url,href)
    if "/clubs/" in full: choices.append((title,full))
   DIRECTORY[territory]=list(dict.fromkeys(choices))
   print("DIRECTORY",territory,len(DIRECTORY[territory]),flush=True)
  except Exception as exc: print("DIRECTORY_ERROR",territory,str(exc),flush=True)
EXCLUDE_RIGHTS_IDS=set() # No explicit ban currently documented for these clubs
def normal(s):
 s=unicodedata.normalize("NFKD",s or "")
 s="".join(c for c in s if not unicodedata.combining(c))
 s=re.sub(r"\bste\b","sainte",s.lower())
 s=re.sub(r"\bst\b","saint",s)
 s=re.sub(r"[^a-z0-9]+"," ",s).strip()
 return re.sub(r"\s+"," ",s)
def slugify(s): return normal(s).replace(" ","-")
def similarity(a,b):
 x,y=normal(a),normal(b)
 return SequenceMatcher(None,x,y).ratio()
def choose_candidate(team_id,name,territory):
 curated=URL_SLUGS.get(team_id,[])
 orig=slugify(name)
 slugs=curated + [orig,slugify(name.replace("A.S.","AS").replace("S.C.","SC"))]
 slugs=list(dict.fromkeys(s for s in slugs if s))
 candidate_urls=[f"https://www.sportcorico.com/clubs/{s}" for s in slugs[:4]]
 targets=[name]+NAME_ALIASES.get(team_id,[])
 indexed=[]
 for title,url in DIRECTORY.get(territory,[]):
  score=max(similarity(title,t) for t in targets)
  if score>=0.79: indexed.append((score,url))
 indexed.sort(reverse=True)
 return list(dict.fromkeys([url for _,url in indexed[:3]]+candidate_urls))[:7]
def get_html(url):
 r=requests.get(url,timeout=14,headers=HEADERS)
 r.raise_for_status()
 return BeautifulSoup(r.text,"html.parser"),r.url
def choose_logo(soup,club):
 candidates=[]
 for im in soup.find_all("img"):
  alt=im.get("alt","").strip()
  if not re.match(r"^logo\s+",alt,re.I): continue
  label=re.sub(r"^logo\s+","",alt,flags=re.I)
  if normal(label) in ("sportcorico","site","logo","district","equipe"): continue
  score=similarity(label,club)
  if score<0.72: continue
  for attr in ("src","data-src","data-original"):
   val=im.get(attr,"")
   if val and not val.startswith("data:"):
    url=urljoin("https://www.sportcorico.com",val)
    if any(s in url.lower() for s in ("_nuxt/", "default", "placeholder","avatar","logo-long")): continue
    candidates.append((score,url,alt))
    break
 return sorted(candidates,reverse=True)
def style_existing_canvas(target):
 # The collection-stage neutral canvas is replaced by a color derived from
 # the actual logo, without inventing shapes or altering IDs.
 im=Image.open(target).convert("RGB")
 if im.size!=(120,96) or im.getpixel((0,0))!=(238,238,238):return
 from collections import Counter
 counts=Counter()
 for red,green,blue in im.getdata():
  if max(abs(red-238),abs(green-238),abs(blue-238))<36:continue
  import colorsys
  hue,sat,lum=colorsys.rgb_to_hsv(red/255,green/255,blue/255)
  if sat<0.28 or lum<0.20 or lum>0.97:continue
  counts[(red//40,green//40,blue//40)]+=1
 if counts:
  key=counts.most_common(1)[0][0]
  # Lightened variant of a true dominant crest color: still the club's hue
  out=tuple(min(255,int((k*40+20)*0.56+255*0.44)) for k in key)
 else:
  out=(222,222,222)
 pix=im.load()
 for y in range(96):
  for x in range(120):
   if pix[x,y]==(238,238,238):pix[x,y]=out
 im.save(target,format="PNG",optimize=True)
def process(row):
 tid,name=row["team_id"],row["name"]
 territory=row["territory"]
 target=DEST/(tid+".png")
 if target.exists() and target.stat().st_size>300:
  style_existing_canvas(target)
  previous=PRIOR.get(tid,{})
  return dict(team_id=tid,team=name,territory=territory,status="already_published",page=previous.get("page",""),image=previous.get("image",""),confidence=previous.get("confidence","previously_checked"),reason="previously published")
 if tid in EXCLUDE_RIGHTS_IDS:
  return dict(team_id=tid,team=name,territory=territory,status="permission_needed",page="",image="",confidence="",reason="explicit rights reservation; no upload")
 errors=[]
 for page in choose_candidate(tid,name,territory):
  try:
   soup,url=get_html(page)
   h1=soup.find("h1")
   title=h1.get_text(" ",strip=True) if h1 else ""
   body=soup.get_text(" ",strip=True)
   if territory=="Guadeloupe" and not re.search(r"(?:District|Ligue)\s+(?:de\s+|d\x27)?Guadeloupe",body,re.I): raise ValueError("territory_not_confirmed")
   if territory=="Guyane" and not re.search(r"(?:District|Ligue)\s+(?:de\s+|d\x27)?Guyane",body,re.I): raise ValueError("territory_not_confirmed")
   scores=[(similarity(title,n),n) for n in [name]+NAME_ALIASES.get(tid,[])]
   top_score,matched=max(scores)
   if top_score < 0.77: raise ValueError("club_identity_mismatch:"+str(round(top_score,2))+"/"+title)
   logos=choose_logo(soup,title)
   if not logos: raise ValueError("no_unambiguous_club_crest_img")
   score,imgurl,alt=logos[0]
   if score < 0.80: raise ValueError("logo_alt_mismatch:"+alt)
   r=requests.get(imgurl,timeout=14,headers=HEADERS)
   r.raise_for_status()
   if len(r.content)<600: raise ValueError("too_small")
   raw=Image.open(io.BytesIO(r.content))
   raw.verify()
   logo=Image.open(io.BytesIO(r.content)).convert("RGBA")
   if logo.width<30 or logo.height<30: raise ValueError("undersize_source")
   if logo.width/logo.height>3.5 or logo.height/logo.width>3.5: raise ValueError("wrong_ratio")
   logo.thumbnail((102,86),Image.Resampling.LANCZOS)
   bg=Image.new("RGBA",(120,96), "#eeeeee")
   bg.alpha_composite(logo,((120-logo.width)//2,(96-logo.height)//2))
   buf=io.BytesIO();bg.convert("RGB").save(buf,format="PNG",optimize=True)
   image_bytes=buf.getvalue()
   if len(image_bytes)<750: raise ValueError("flattened_image_too_small")
   # Reject visually detected FFF generic placeholders.
   with Image.open(io.BytesIO(image_bytes)) as _check:
    _hash=imagehash.phash(_check.convert("RGB").crop((10,5,110,94)))
   if any(_hash-_x<=7 for _x in FFF_TEMPLATES):
    raise ValueError("FFF_GENERIC_NOT_CLUB_CREST")
   target.write_bytes(image_bytes)
   return dict(team_id=tid,team=name,territory=territory,status="published",page=url,image=imgurl,confidence=f"identity={top_score:.3f};logo={score:.3f}",reason="")
  except Exception as exc:
   errors.append(page+": "+str(exc)[:100])
 return dict(team_id=tid,team=name,territory=territory,status="needs_manual_source",page="",image="",confidence="",reason="; ".join(errors)[:900])
PRIOR={}
if REPORT.exists():
 with REPORT.open(encoding="utf-8",newline="") as f:
  PRIOR={r["team_id"]:r for r in csv.DictReader(f)}
with ROSTER.open(encoding="utf-8",newline="") as f:
 allrows=list(csv.DictReader(f))
rows=[r for r in allrows if r.get("territory") in ("Mayotte",)]
build_index()
print("SCANNING",len(rows),"clubs",flush=True)
results=[]
with ThreadPoolExecutor(max_workers=6) as ex:
 jobs={ex.submit(process,r):r for r in rows}
 for job in as_completed(jobs):
  try: results.append(job.result())
  except Exception as exc:
   r=jobs[job]
   results.append(dict(team_id=r["team_id"],team=r["name"],territory=r["territory"],status="error",page="",image="",confidence="",reason=str(exc)[:500]))
 results.sort(key=lambda x:(x["territory"],int(x["team_id"])))
with REPORT.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["team_id","team","territory","status","page","image","confidence","reason"])
 w.writeheader();w.writerows(results)
from collections import Counter
print("RESULTS",dict(Counter(r["status"] for r in results)),flush=True)
