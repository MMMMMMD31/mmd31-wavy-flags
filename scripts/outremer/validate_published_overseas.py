#!/usr/bin/env python3
"""Strict integrity check for all published PNGs. Never creates imagery.
Run after false FFF logo quarantine; preserve missing teams with no invented crest.
"""
import csv, json,hashlib,collections
from pathlib import Path
from PIL import Image
import imagehash
FFF_HASHES=[]
for _tid in (1990262000021,1990262000111):
 _p=Path('audit/outremer-2026-27/quarantine')/(str(_tid)+'.png')
 if _p.exists():
  with Image.open(_p) as _im:
   FFF_HASHES.append(imagehash.phash(_im.convert('RGB').crop((10,5,110,94))))
ROOT=Path("flags/clubs/standard/outremer-2026-27")
ROSTER=Path("audit/outremer-2026-27/roster_326.csv")
AUDIT_DIR=Path("audit/outremer-2026-27")
BRANCH="mmd31-outremer-ecussons-20261023"
URL="https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/"+BRANCH+"/flags/clubs/standard/outremer-2026-27/"
references={}
for filename in ("reunion_martinique_crest_audit.csv","guadeloupe_guyane_crest_audit.csv","mayotte_crest_audit.csv","saintmartin_crest_audit.csv"):
 p=AUDIT_DIR/filename
 if p.exists():
  for row in csv.DictReader(p.open(encoding="utf8")):
   references[row["team_id"]]={"source_page":row.get("page",""),"source_image":row.get("image",""),"status":row.get("status","")}
p=AUDIT_DIR/"martinique_last3_audit.csv"
if p.exists():
 for row in csv.DictReader(p.open(encoding="utf8")):
  references[row["team_id"]]={"source_page":row.get("source_page",""),"source_image":row.get("image_url",""),"status":row.get("status","")}
for filename in ("lot6_pacific_saintmartin_spm_audit.csv",):
 p=AUDIT_DIR/filename
 if p.exists():
  for row in csv.DictReader(p.open(encoding="utf8")):
   references[row["team_id"]]={"source_page":row.get("source_page",""),"source_image":row.get("image_url",""),"status":row.get("status","")}
p=AUDIT_DIR/"duplicate_club_resolution.csv"
if p.exists():
 for row in csv.DictReader(p.open(encoding="utf8")):
  if row["status"] in ("restored_original_verified_logo","new_unique_club_logo"):
   references[row["team_id"]]={"source_page":row.get("check_page",""),"source_image":row.get("source",""),"status":row.get("status","")}
rows=list(csv.DictReader(ROSTER.open(encoding="utf8")))
assert len(rows)==326,len(rows)
assert len(set(row["team_id"] for row in rows))==326
checks=[]
for row in rows:
 cid=row["team_id"]; p=ROOT/(cid+".png")
 status="missing";sha="";bytesize=0;reason=""
 if p.is_file():
  try:
   with Image.open(p) as im:
    im.verify()
   with Image.open(p) as im:
    if im.format!="PNG" or im.size!=(120,96):raise ValueError(f"format={im.format} dimensions={im.size}")
   data=p.read_bytes()
   if len(data)<400:raise ValueError("unusually small")
   sha=hashlib.sha256(data).hexdigest()
   bytesize=len(data);status="ok"
   if FFF_HASHES:
    with Image.open(p) as _im:
     _hash=imagehash.phash(_im.convert("RGB").crop((10,5,110,94)))
    if any(_hash-h<=7 for h in FFF_HASHES):
     status="generic_not_club_crest";reason="FFF placeholder, not a team crest"
  except Exception as err:
   status="invalid";reason=str(err)
 ref=references.get(cid,{})
 checks.append(dict(team_id=cid,club=row["name"],territory=row["territory"],status=status,sha256=sha,size_bytes=bytesize,
     flagUrl=URL+cid+".png" if status=="ok" else "",source_page=ref.get("source_page",""),source_image=ref.get("source_image",""),
     source_status=ref.get("status",""),reason=reason))
group=collections.defaultdict(list)
for r in checks:
 if r["status"]=="ok":group[r["sha256"]].append(r["team_id"])
duplicates={key:ids for key,ids in group.items() if len(ids)>1}
if duplicates:
 for r in checks:
  if r["sha256"] in duplicates:r["reason"]="Possible identical logo for IDs: "+",".join(duplicates[r["sha256"]])
if duplicates:
 for entry in checks:
  if entry["sha256"] in duplicates:
   entry["status"]="unverified_duplicate"
   entry["flagUrl"]=""
   entry["reason"]="same PNG for several team IDs; no documented parent affiliation"
for r in rows:
 check=next(c for c in checks if c["team_id"]==r["team_id"])
 if check["status"]=="ok":
  r["flagUrl"]=check["flagUrl"]
  r["crest_status"]="GITHUB_PUBLIE_PNG_120x96"
 elif r["team_id"]=="1990262000029":
  r["flagUrl"]="";r["crest_status"]="AUTORISATION_REPUBLICATION_A_VERIFIER"
 elif r["team_id"]=="1990262000121":
  r["flagUrl"]="";r["crest_status"]="ENTENTE_SANS_ECUSSON_COMMUN_VERIFIE"
 else:r["flagUrl"]="";r["crest_status"]="ECUSSON_MANQUANT"
with ROSTER.open("w",encoding="utf8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
out=AUDIT_DIR/"published_overseas_manifest.csv"
with out.open("w",encoding="utf8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
counts={k:collections.Counter(c["territory"] for c in checks if c["status"]==k) for k in ["ok","invalid","missing"]}
report={"total":len(checks),"published":sum(c["status"]=="ok" for c in checks),"invalid":sum(c["status"]=="invalid" for c in checks),"missing":sum(c["status"]=="missing" for c in checks),"by_territory":dict(counts["ok"]),"duplicate_sha256":duplicates,"placeholder_count":sum(c["status"]=="generic_not_club_crest" for c in checks),"unresolved":[{k:v for k,v in c.items() if k in ("team_id","club","territory","status","reason")} for c in checks if c["status"]!="ok"]}
(AUDIT_DIR/"published_overseas_validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps({k:v for k,v in report.items() if k!="unresolved"},ensure_ascii=False,indent=2))
if report["invalid"]:raise SystemExit("Invalid PNG artwork detected, inspect report")
if duplicates:print("WARNING: duplicate PNG bytes detected; manual identity verification needed")
