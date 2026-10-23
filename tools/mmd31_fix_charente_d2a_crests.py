#!/usr/bin/env python3
"""Produce 12 confirmed Charente D2 Group A crests, with unchanged 120x96 style."""
from pathlib import Path
import json,hashlib,io
from PIL import Image,ImageDraw
from mmd31_build_d1d2_standard_crests import get_image,make_icon

FFA=["500089","563725","526779","541490","547100","527934","547099","512943","506967","506939","528905","517984"]
OUT=Path("flags/clubs/standard/d1d2-2026-27")
META=Path("docs/research/mmd31-v9-charente-2026-27")
OUT.mkdir(parents=True,exist_ok=True);META.mkdir(parents=True,exist_ok=True)
data={}
sheet=Image.new("RGB",(4*140,3*128),"white")
draw=ImageDraw.Draw(sheet)
for n,aff in enumerate(FFA):
    src,icon=get_image(aff)
    if icon is None:
        raise SystemExit(f"Unverifiable crest for FFF {aff}: {src.get('error')}")
    png,color,rule=make_icon(icon)
    im=Image.open(io.BytesIO(png))
    assert im.size==(120,96)
    p=OUT/f"bc{aff}.png"
    if p.exists():raise SystemExit(f"already exists: {p}")
    p.write_bytes(png)
    x=(n%4)*140+10;y=(n//4)*128+5
    sheet.paste(im,(x,y))
    draw.text((x,y+98),aff,fill="black")
    data[aff]={"status":"published_candidate","source":src,"png_path":p.as_posix(),
       "url":f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-v9-charente-fix-20261023/{p.as_posix()}",
       "background_rgb":color,"tone_rule":rule,
       "png_sha256":hashlib.sha256(png).hexdigest(),
       "dimensions":[120,96]}
sheet.save(META/"contact_sheet.png")
(META/"manifest.json").write_text(json.dumps({"2026-27_charente_d2_group_A":data,"clubs":12},ensure_ascii=False,indent=2),encoding="utf-8")
print("PUBLISHED",len(data),flush=True)
