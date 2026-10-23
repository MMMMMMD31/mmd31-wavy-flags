#!/usr/bin/env python3
"""Find false FFF filler artwork and shared PNGs before updating gameplay JSON."""
import csv,hashlib,collections,json
from pathlib import Path
from PIL import Image
import imagehash
DIR=Path("flags/clubs/standard/outremer-2026-27")
OUT=Path("audit/outremer-2026-27/crest_similarity_audit.csv")
REFERENCE=[1990262000021,1990262000064,1990262000111]
templates={}
for tid in REFERENCE:
 p=DIR/(str(tid)+".png")
 with Image.open(p) as im:templates[tid]=imagehash.phash(im.convert("RGB").crop((10,5,110,94)))
records=[]
allshas=collections.defaultdict(list)
for p in sorted(DIR.glob("*.png")):
 with Image.open(p) as im:
  image=im.convert("RGB")
  h=imagehash.phash(image.crop((10,5,110,94)))
  sample=imagehash.dhash(image.crop((10,5,110,94)))
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 allshas[sha].append(p.stem)
 distances={str(k):int(h-v) for k,v in templates.items()}
 records.append(dict(team_id=p.stem,sha256=sha,phash=str(h),dhash=str(sample),dist_fff=min(distances.values()),
  nearest_fff=min(distances,key=distances.get),suspected_fff_placeholder="YES" if min(distances.values())<=7 else "NO",sha_group=""))
for r in records:r["sha_group"]=",".join(allshas[r["sha256"]])
with OUT.open("w",newline="",encoding="utf8") as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
print(json.dumps({"total":len(records),"suspectedFFF":[(x["team_id"],x["dist_fff"]) for x in records if x["suspected_fff_placeholder"]=="YES"],
"duplicate_sha_groups":[v for v in allshas.values() if len(v)>1]},ensure_ascii=False))
