#!/usr/bin/env python3
import re, json, requests, concurrent.futures, time, random, threading
from pathlib import Path
from PIL import Image
from io import BytesIO
manifest=json.loads(Path("docs/english-clubs-2026-27/wiki-v13/manifest.json").read_text())
todo=[x for x in manifest["files"] if not x["status"].startswith("PUBLISHED")]
assert len(todo)==55,len(todo)
local=threading.local()
def session():
 if not hasattr(local,"http"):
  local.http=requests.Session()
  local.http.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 historical football club badge provenance)"})
 return local.http
def safeget(url):
 for k in range(3):
  try:
   r=session().get(url,timeout=25)
   if r.status_code in (429,502,503):
    time.sleep(1.2*(k+1));continue
   return r
  except requests.RequestException:
   if k==2:raise
   time.sleep(1.5*(k+1))
def canon(t):
 t=t.lower().replace("&","and").replace("’","'").replace("("," ").replace(")"," ")
 t=re.sub(r"(\\bfootball\\s*club\\b|\\bassociation\\s*football\\s*club\\b|\\bf\\.?c\\.?\\b|\\ba\\.?f\\.?c\\.?\\b)"," ",t)
 return re.sub(r"[^a-z0-9]","",t)
aliases={
 "Westfield":["Westfield FC"],
 "Windsor & Eton":["Windsor & Eton FC"],
 "South Park (Reigate)":["South Park Reigate"],
 "Boldmere St Michael's":["Boldmere St. Michaels"],
 "Sutton United (Birmingham)":["Sutton United Birmingham"],
 "Pershore Town 88":["Pershore Town"],
 "Thackley Association":["Thackley"],
 "East Cowes Victoria Athletic":["East Cowes Victoria"],
 "Torpoint Athletic":["Torpoint AFC"],
 "Bugbrooke St Michael":["Bugbrooke St Michaels"],
 "Larkfield & New Hythe":["Larkfield and New Hythe"],
}
def lookup(row):
 name=row["name"]
 tsdb=[]
 for term in [name]+aliases.get(name,[]):
  url="https://www.thesportsdb.com/api/v1/json/123/searchteams.php"
  try:
   r=safeget(url+"?t="+requests.utils.quote(term))
   if r.status_code!=200:continue
   teams=r.json().get("teams") or []
   for item in teams:
    title=item.get("strTeam") or ""
    matches=canon(title)==canon(name) or canon(title) in [canon(x) for x in aliases.get(name,[])]
    # Avoid namesakes from other sports or women's games without explicit matching of club.
    if not matches:continue
    if (item.get("strSport") or "").lower() not in ("soccer",""):continue
    badge=item.get("strBadge") or item.get("strTeamBadge")
    if not badge:continue
    tsdb.append({"name":title,"id":item.get("idTeam"),"sport":item.get("strSport"),"league":item.get("strLeague"),"gender":item.get("strGender"),"badge":badge,"source":url+"?t="+requests.utils.quote(term)})
   if tsdb:break
  except Exception:continue
 checked=[]
 for obj in tsdb[:3]:
  try:
   response=safeget(obj["badge"])
   if response.status_code==200 and response.headers.get("content-type","").startswith("image/"):
    im=Image.open(BytesIO(response.content))
    if min(im.size)>40:obj.update({"image_ok":True,"original_dimensions":list(im.size)})
   else:obj["image_ok"]=False
  except Exception as e:obj["error"]=str(e)[:90]
 return {"id":row["id"],"name":name,"tsdb":tsdb}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:
 allrows=list(p.map(lookup,todo))
result={"total":len(allrows),"with_badge":sum(any(x.get("image_ok") for x in r["tsdb"]) for r in allrows),"records":allrows}
path=Path("docs/english-v13");path.mkdir(exist_ok=True,parents=True)
(path/"tsdb_missing_55_research.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
print("COVERAGE",result["with_badge"],"/",result["total"],flush=True)
print("MISSING:",[r["name"] for r in allrows if not any(z.get("image_ok") for z in r["tsdb"])],flush=True)
