#!/usr/bin/env python3
"""Rebuild full 326-club status manifest from files actually present on branch."""
import csv,json,hashlib,collections
from pathlib import Path
from PIL import Image
root=Path("flags/clubs/standard/outremer-2026-27")
audit=Path("audit/outremer-2026-27")
roster=list(csv.DictReader((audit/"roster_326.csv").open(encoding="utf-8")))
assert len(roster)==326 and len({r["team_id"] for r in roster})==326
sources={}
for path in ("lot8_three_public_badges.json","lot11_three_club_sources.json"):
 obj=json.loads((audit/path).read_text(encoding="utf-8"))
 for row in obj["assets"]:
  sources[row["team_id"]]={"source":row.get("img") or row.get("source"),"source_page":row.get("page") or row.get("provenance")}
for path in ("lot7_remaining66_audit.csv",):
 with (audit/path).open(encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   if row.get("status")=="published":sources.setdefault(row["team_id"],{"source":row.get("image_url"),"source_page":row.get("source")})
for path in ("lot9_rc_saint_pierre_af_possession.json",):
 for row in json.loads((audit/path).read_text(encoding="utf-8")):
  if row.get("status")=="published":sources[row["id"]]={"source":row.get("url"),"source_page":row.get("source")}
urlbase="https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-outremer-ecussons-20261023/flags/clubs/standard/outremer-2026-27/"
result=[]
for r in roster:
 tid=r["team_id"];file=root/(tid+".png");present=file.exists()
 d={"team_id":tid,"club":r["name"],"territoire":r["territory"],"statut":"PNG_120x96_GITHUB_PUBLIE" if present else "ECUSSON_A_VERIFIER","flagUrl":urlbase+tid+".png" if present else "","sha256":"","source_url":sources.get(tid,{}).get("source",""),"source_page":sources.get(tid,{}).get("source_page","")}
 if present:
  im=Image.open(file)
  assert im.format=="PNG" and im.size==(120,96), (tid,im.format,im.size)
  d["sha256"]=hashlib.sha256(file.read_bytes()).hexdigest()
 result.append(d)
assert sum(r["statut"]=="PNG_120x96_GITHUB_PUBLIE" for r in result)==302
assert sum(r["statut"]=="ECUSSON_A_VERIFIER" for r in result)==24
assert len(list(root.glob("*.png")))==302
out=audit/"published_overseas_manifest_302.csv"
with out.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
status={"total":326,"png_found":302,"missing":24,"territoires_non_resolus":dict(collections.Counter(r["territoire"] for r in result if not r["flagUrl"])),"workflow":"mmd31_outremer_final_source_audit","note":"Presence, image dimensions and format verified. Authenticity rests on club source audits; rights to logos belong to owners. Do not infer missing badges."}
(audit/"published_overseas_status_302.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("RESULT",json.dumps(status,ensure_ascii=False))
