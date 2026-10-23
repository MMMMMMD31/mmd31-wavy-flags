#!/usr/bin/env python3
"""MMD31 V12A—make verified 120x96 standard crests for 43 newly recovered affiliation IDs."""
import hashlib,io,json,collections
from pathlib import Path
from PIL import Image,ImageDraw
from mmd31_build_d1d2_standard_crests import get_image,make_icon
AFFILIATIONS="500437 501114 501115 505991 506197 507031 507168 514428 515107 515163 519689 520022 520185 522137 524576 528157 529662 530358 530360 533130 538458 538567 539814 540051 540546 545012 545563 546232 547099 548199 554424 563669 563725 564757 564892 565133 565139 565594 566021 581837 581839 581990 582387".split()
OUT=Path("flags/clubs/standard/v12a-2026-27");OUT.mkdir(parents=True,exist_ok=True)
AUD=Path("docs/research/mmd31-v12a-five-groups");AUD.mkdir(parents=True,exist_ok=True)
manifest={};canvas=Image.new("RGB",(6*140,8*128),"white");draw=ImageDraw.Draw(canvas)
for i,aff in enumerate(AFFILIATIONS):
 meta,im=get_image(aff)
 if im is None:
  manifest[aff]={"status":"source_unavailable","reason":meta.get("error"),"source":meta.get("source_url")}
  continue
 png,background,rule=make_icon(im)
 path=OUT/f"bc{aff}.png";path.write_bytes(png)
 url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-v12a-five-groups-20261023/{path}"
 manifest[aff]={"status":"published_candidate","url":url,"path":str(path),"sha256":hashlib.sha256(png).hexdigest(),"size":[120,96],"source_sha256":meta["source_sha256"],"source_url":meta["source_url"],"background_rgb":list(background)}
 x=i%6*140+8;y=i//6*128+4
 canvas.paste(Image.open(io.BytesIO(png)).convert("RGB"),(x,y))
 draw.text((x,y+100),aff,fill="black")
(AUD/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
canvas.save(AUD/"contact_sheet.png",optimize=True)
print("DID",len(manifest),"published",sum(t["status"]=="published_candidate" for t in manifest.values()),flush=True)
