#!/usr/bin/env python3
"""Find authentic club crests for La Réunion and Martinique from matching SportCorico club pages.
NEVER use a site logo, placeholder, homonym, wrong territory or invent a crest.
Writes auditable statuses; auto-accepted images require a matching club title and territory.
"""
import csv, re, io, os, hashlib, unicodedata, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from PIL import Image

ROSTER=Path("audit/outremer-2026-27/roster_326.csv")
DEST=Path("flags/clubs/standard/outremer-2026-27")
DEST.mkdir(parents=True,exist_ok=True)
REPORT=Path("audit/outremer-2026-27/reunion_martinique_crest_audit.csv")
REPORT.parent.mkdir(parents=True,exist_ok=True)
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; MMD31CrestAudit/2.0; +https://github.com/MMMMMMD31/mmd31-wavy-flags)"}
# Curated exact club URL aliases when the official FFF name and name in simulator differ.
URL_SLUGS={
 "1990262000053":["la-tamponnaise"],
 "1990262000054":["as-excelsior"],
 "1990262000055":["js-st-pierroise"],
 "1990262000056":["st-denis-fc"],
 "1990262000057":["st-pauloise-fc"],
 "1990262000058":["es-dominicaine"],
 "1990262000059":["trois-bassins-fc"],
 "1990262000060":["acf-piton-st-leu"],
 "1990262000061":["ss-jeanne-d-arc"],
 "1990262000062":["js-ste-rosienne-f"],
 "1990262000063":["fc-la-ville-ste-suz"],
 "1990262000064":["us-benedictine"],
 "1990262000065":["fc-bagatelle-st-suz"],
 "1990262000066":["as-st-louisienne"],
 "1990262000027":["rc-st-joseph"],
 "1990262000028":["c-franciscain"],
 "1990262000029":["golden-lion-football"],
 "1990262000030":["as-morne-des-esses"],
 "1990262000031":["club-peleen"],
 "1990262000032":["c-colonial"],
 "1990262000033":["co-trenelle"],
 "1990262000034":["golden-star"],
 "1990262000035":["assaut"],
 "1990262000036":["samaritaine"],
 "1990262000037":["inter-de-sainte-anne"],
 "1990262000038":["rc-riviere-pilote"],
 "1990262000039":["rapid-club"],
 "1990262000040":["espoir-ste-luce"]
}
# Name equivalences are used for matching *only*, never for merging IDs.
NAME_ALIASES={
 "1990262000055":["JS Saint Pierroise","JS St Pierroise"],
 "1990262000061":["AS Jeanne d Arc","SS Jeanne d Arc"],
 "1990262000028":["Club Franciscain"],
 "1990262000032":["Club Colonial"],
 "1990262000029":["Golden Lion Football","Golden Lion FC"],
 "1990262000054":["AS Excelsior Saint Joseph"],
 "1990262000031":["Club Peleen","Club Péléen"],
}
EXCLUDE_RIGHTS_IDS={"1990262000029"} # Golden Lion: reported explicit no-republication without authorisation
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
def choose_candidate(team_id,name):
 curated=URL_SLUGS.get(team_id,[])
 orig=slugify(name)
 slugs=curated + [orig,slugify(name.replace("A.S.","AS").replace("S.C.","SC"))]
 slugs=list(dict.fromkeys(s for s in slugs if s))
 return [f"https://www.sportcorico.com/clubs/{s}" for s in slugs[:4]]
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
def process(row):
 tid,name=row["team_id"],row["name"]
 territory=row["territory"]
 target=DEST/(tid+".png")
 if target.exists() and target.stat().st_size>300:
  return dict(team_id=tid,team=name,territory=territory,status="already_published",page="",image="",confidence="previously_checked",reason="")
 if tid in EXCLUDE_RIGHTS_IDS:
  return dict(team_id=tid,team=name,territory=territory,status="permission_needed",page="",image="",confidence="",reason="explicit rights reservation; no upload")
 errors=[]
 for page in choose_candidate(tid,name):
  try:
   soup,url=get_html(page)
   h1=soup.find("h1")
   title=h1.get_text(" ",strip=True) if h1 else ""
   body=soup.get_text(" ",strip=True)
   if "Réunion" in territory and not re.search(r"District\s+La\s+R[eé]union",body,re.I): raise ValueError("territory_not_confirmed")
   if territory=="Martinique" and not re.search(r"District\s+Martinique",body,re.I): raise ValueError("territory_not_confirmed")
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
   target.write_bytes(image_bytes)
   return dict(team_id=tid,team=name,territory=territory,status="published",page=url,image=imgurl,confidence=f"identity={top_score:.3f};logo={score:.3f}",reason="")
  except Exception as exc:
   errors.append(page+": "+str(exc)[:100])
 return dict(team_id=tid,team=name,territory=territory,status="needs_manual_source",page="",image="",confidence="",reason="; ".join(errors)[:900])
with ROSTER.open(encoding="utf-8",newline="") as f:
 allrows=list(csv.DictReader(f))
rows=[r for r in allrows if r.get("territory") in ("La Réunion","Martinique")]
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
