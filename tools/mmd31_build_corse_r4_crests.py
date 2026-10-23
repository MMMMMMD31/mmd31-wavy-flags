#!/usr/bin/env python3
"""Generate real Ligue Corse R4 2026-27 standard 120x96 crest images using FFF IDs."""
from pathlib import Path
import json,hashlib,io
from PIL import Image,ImageDraw
from mmd31_build_d1d2_standard_crests import get_image,make_icon
p=Path("research-input/mmd31_corse_r4_roster_source_2026_27.json")
src=json.loads(p.read_text(encoding="utf-8"))
rows=[t for g in src["groups"] for t in g["teams"]]
assert len(rows)==9 and all(t.get("fff_affiliation") for t in rows)
out=Path("flags/clubs/standard/r4-corse-2026-27")
out.mkdir(parents=True,exist_ok=True)
manifest={}
sheet=Image.new("RGB",(3*140,3*130),"white")
draw=ImageDraw.Draw(sheet)
for i,t in enumerate(rows):
 aff=t["fff_affiliation"]
 meta,im=get_image(aff)
 item={"name":t["name"],"squad_key":t["squad_key"],"affiliation":aff,"source_url":t["club_url"]}
 if im is not None:
  data,bg,rule=make_icon(im)
  fn=out/f"bc{aff}.png"
  fn.write_bytes(data)
  item.update({"status":"published","flag_url":f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-v12-french-system-final-audit-20261023/{fn}",
               "sha256":hashlib.sha256(data).hexdigest(),"size":[120,96],"background_rgb":list(bg)})
  x=(i%3)*140+8;y=(i//3)*130+3
  sheet.paste(Image.open(io.BytesIO(data)).convert("RGB"),(x,y))
  draw.text((x,y+100),aff,fill="black")
 else:
  item.update({"status":"source_unavailable","error":meta.get("error")})
 manifest[t["squad_key"]]=item
m=Path("docs/research/mmd31-corse-r4-2026-27")
m.mkdir(parents=True,exist_ok=True)
(m/"crest_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
sheet.save(m/"contact_sheet.png",optimize=True)
print("R4 source",len(rows),"PNGs",sum(x["status"]=="published" for x in manifest.values()),flush=True)
