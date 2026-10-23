#!/usr/bin/env python3
"""MMD31 district D3/D4/D5 standard logos. Source FFF affiliation required.
One 120x96 lighter club-color PNG per unique affiliation, reused by reserve squads.
"""
from __future__ import annotations
import collections,concurrent.futures,hashlib,io,json,os,math
from pathlib import Path
from PIL import Image,ImageDraw
from mmd31_build_d1d2_standard_crests import get_image,make_icon

lv=int(os.environ.get("MMD31_DIVISION","3"))
assert lv in [6,7,8]
INPUT=Path(f"research-input/MMD31_D{lv}_2026_2027_PARTICIPANTS_SOURCE.json")
OUT=Path(f"flags/clubs/standard/d{lv}-2026-27")
META=Path(f"docs/research/mmd31-d{lv}-2026-27")
BRANCH=f"mmd31-d{lv}-logos-20261023"
assert INPUT.is_file(),INPUT
o=json.loads(INPUT.read_text(encoding="utf8"))
groups=[g for g in o["groups"] if 6<=len(g.get("teams",[]))<=20]
allitems={}
for g in groups:
 for t in g["teams"]:
  if not t.get("source_team_key") or not t.get("fff_affiliation"):continue
  key=t["source_team_key"]
  prev=allitems.get(key)
  if prev is None or (int(t.get("played") or 0)>int(prev[1].get("played") or 0)):
   allitems[key]=(g,t)
by_aff=collections.defaultdict(list)
for key,(g,t) in allitems.items():
 by_aff[str(t["fff_affiliation"])].append({"squad_key":key,"name":t["source_name"],"district":g["district"],"group":g.get("group"),"club_url":t["club_url"]})
affiliations=sorted(by_aff)
print(f"D{lv} sourced squad keys={len(allitems)}; club affiliations={len(affiliations)}",flush=True)
OUT.mkdir(parents=True,exist_ok=True);META.mkdir(parents=True,exist_ok=True)
fetches={}
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
 futs={pool.submit(get_image,a):a for a in affiliations}
 for n,fut in enumerate(concurrent.futures.as_completed(futs)):
  aff=futs[fut]
  fetches[aff]=fut.result()
  if (n+1)%400==0:print(f"source crests {n+1}/{len(affiliations)}",flush=True)
hashes=collections.defaultdict(set)
for aff,(meta,img) in fetches.items():
 if img is not None: hashes[meta["source_sha256"]].add(aff)
entries={};errors=[];thumbs=[]
for i,aff in enumerate(affiliations):
 meta,img=fetches[aff]
 entry=dict(meta);entry["teams"]=by_aff[aff]
 if img is not None and len(hashes[meta["source_sha256"]])>1:
  entry["status"]="unresolved";entry["error"]="Source logo identical for multiple unrelated affiliations";img=None
 if img is None:
  entry["status"]="unresolved";errors.append(entry);entries[aff]=entry;continue
 png,bg,rule=make_icon(img)
 path=OUT/f"bc{aff}.png"
 path.write_bytes(png)
 entry.update({"status":"published_candidate","path":str(path),"url":f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/{BRANCH}/{path}",
   "dimensions":[120,96],"background_rgb":list(bg),"rule":rule,
   "sha256":hashlib.sha256(png).hexdigest()})
 entries[aff]=entry
 if i%max(1,len(affiliations)//100)==0 and len(thumbs)<100:
  thumbs.append((aff,Image.open(io.BytesIO(png)).convert("RGB")))
canvas=Image.new("RGB",(10*138,math.ceil(len(thumbs)/10)*124),"white")
draw=ImageDraw.Draw(canvas)
for n,(aff,img) in enumerate(thumbs):
 x=n%10*138+8;y=n//10*124+4
 canvas.paste(img,(x,y));draw.text((x,y+98),aff,fill="black")
canvas.save(META/"contact_sheet.png",optimize=True)
out={"division":lv,"season":"2026-2027","source":"TheFootData-linked FFF source crest (BC affiliation)",
     "source_squad_count":len(allitems),"unique_affiliations":len(affiliations),
     "published_affiliations":len(affiliations)-len(errors),
     "unresolved_affiliations":len(errors),"branch":BRANCH,"items":entries}
(META/"manifest.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf8")
(META/"README.md").write_text(f"# MMD31 Départementale {lv} 2026/27 standard crests\n\n"+\
 f"- Squad keys in sourced valid groups: {len(allitems)}\n- Distinct affiliations: {len(affiliations)}\n"+\
 f"- Generated 120×96 PNGs: {len(affiliations)-len(errors)}\n- Unresolved: {len(errors)}\n"+\
 "- Source identification: FFF affiliation; reserves reuse same club crest.\n"+\
 "- Background: lighter dominant crest hue; no Victory Flags.\n",encoding="utf8")
print(f"COMPLETED D{lv}: PNGS {len(affiliations)-len(errors)}, UNRESOLVED {len(errors)}",flush=True)
if len(errors)>max(10,len(affiliations)*.1):
 raise SystemExit("Insufficient source logo coverage; review before publication")
