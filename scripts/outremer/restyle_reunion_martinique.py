#!/usr/bin/env python3
"""Convert the neutral temporary canvas of found logos into a team-color backing.
Does not alter authentic logo artwork. Only updates images with exact original #eeeeee canvas corners.
"""
from pathlib import Path
from PIL import Image
from collections import defaultdict
import colorsys, csv, io, collections
root=Path("flags/clubs/standard/outremer-2026-27")
audit=Path("audit/outremer-2026-27/reunion_martinique_crest_audit.csv")
files=[r for r in csv.DictReader(audit.open(encoding="utf-8")) if r["status"] in ("already_published","published")]
seen=set()
for rec in files:
 p=root/(rec["team_id"]+".png")
 if p in seen:continue
 seen.add(p)
 if not p.is_file():continue
 img=Image.open(p).convert("RGB")
 if img.size!=(120,96):continue
 # Existing custom colored backgrounds are kept untouched.
 if img.getpixel((0,0))!=(238,238,238):continue
 pixels=list(img.getdata())
 colorful=collections.defaultdict(lambda:[0.,0.,0.,0.])
 for r,g,b in pixels:
  if max(abs(r-238),abs(g-238),abs(b-238)) < 36:continue
  h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
  if s<0.23 or v<0.19 or v>0.97:continue
  binno=int(h*18)
  weight=(0.3+s)*min(v+0.35,1.2)
  a=colorful[binno]
  a[0]+=weight;a[1]+=r*weight;a[2]+=g*weight;a[3]+=b*weight
 if colorful:
  bucket=max(colorful.values(),key=lambda x:x[0])
  rgb=tuple(int(bucket[i]/bucket[0]*0.52+255*0.48) for i in (1,2,3))
 else:
  rgb=(221,221,221) # light white/grey for monochrome club logos
 src=img.load()
 for y in range(96):
  for x in range(120):
   r,g,b=src[x,y]
   if (r,g,b)==(238,238,238):
    src[x,y]=rgb
 img.save(p,format="PNG",optimize=True)
 print("RESTYLED",rec["team_id"],rec["team"],rgb)
print("RESTYLE COMPLETE",len(seen))
