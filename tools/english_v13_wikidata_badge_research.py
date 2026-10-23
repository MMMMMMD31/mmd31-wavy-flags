#!/usr/bin/env python3
"""Research only: authentic crest leads from structured Wikidata P154 statements.
Does not publish unverified assets or replace club images.
"""
import requests,concurrent.futures,json,re,unicodedata,time
from pathlib import Path
from collections import Counter
catalog=json.loads(Path("tools/english_clubs_d8_d9_2026_27_sources.json").read_text(encoding="utf8"))
todo=[x for x in catalog if not x.get("source_path")]
assert len(todo)==417
UA={"User-Agent":"MMD31-football-league-personal-study/1.0 (non-commercial; source provenance via Wikidata)"}
api="https://www.wikidata.org/w/api.php"
def norm(x):
 x=unicodedata.normalize("NFKD",x).lower()
 x=re.sub(r"[^a-z0-9]+","",x)
 return x.replace("footballclub","").replace("associationfootballclub","").replace("afc","").replace("fc","")
def seek(row):
 name=row["name"]
 try:
  q=requests.get(api,params={"action":"wbsearchentities","search":name,"language":"en","limit":8,"format":"json"},headers=UA,timeout=22)
  q.raise_for_status()
  matches=[]
  for item in q.json().get("search",[]):
   label=item.get("label","")
   desc=item.get("description","").lower()
   if norm(label)!=norm(name):continue
   if not any(a in desc for a in ("football club","football team","association football club","soccer club")):continue
   matches.append({"qid":item["id"],"label":label,"description":item.get("description")})
  if len(matches)!=1:return {"id":row["id"],"name":name,"status":"AMBIGUOUS" if matches else "NO_STRICT_IDENTITY", "candidates":matches}
  return {"id":row["id"],"name":name,"status":"IDENTITY_MATCH", "candidate":matches[0]}
 except Exception as e:return {"id":row["id"],"name":name,"status":"LOOKUP_ERROR","error":str(e)[:120]}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 raw=list(ex.map(seek,todo))
qids=[r["candidate"]["qid"] for r in raw if r["status"]=="IDENTITY_MATCH"]
byqid={}
for start in range(0,len(qids),45):
 chunk=qids[start:start+45]
 try:
  r=requests.get(api,params={"action":"wbgetentities","ids":"|".join(chunk),"props":"claims|labels|descriptions","languages":"en","format":"json"},headers=UA,timeout=35)
  r.raise_for_status()
  byqid.update(r.json().get("entities",{}))
 except Exception as e:print("Batch error",str(e)[:140],flush=True)
for row in raw:
 if row["status"]!="IDENTITY_MATCH":continue
 qid=row["candidate"]["qid"]
 entity=byqid.get(qid,{})
 props=entity.get("claims",{})
 logo_claims=props.get("P154",[])
 images=[]
 for claim in logo_claims:
  if claim.get("rank")=="deprecated":continue
  v=claim.get("mainsnak",{}).get("datavalue",{}).get("value")
  if isinstance(v,str) and re.search(r"\\.(svg|png|jpe?g|webp)$",v,re.I):images.append(v)
 row["wikidata_qid"]=qid;row["p154_files"]=list(dict.fromkeys(images))
 row["status"]="WIKIDATA_P154_CANDIDATE" if images else "NO_P154"
p=Path("docs/english-v13");p.mkdir(parents=True,exist_ok=True)
manifest={"expected":417,"count":len(raw),"candidate_crests":sum(r["status"]=="WIKIDATA_P154_CANDIDATE" for r in raw),"status_counts":dict(Counter(r["status"] for r in raw)),"method":"Exact club label + football club description + authentic logo P154; all candidates still require manual image identity inspection. No images published.","records":raw}
(p/"wikidata_badge_research.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(manifest["status_counts"],flush=True)
