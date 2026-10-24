#!/usr/bin/env python3
"""Verified Aigles d'Or de Mana (=A.O.M.) club crest: club's own Footeo site."""
from PIL import Image
from pathlib import Path
import requests,hashlib,collections,json,io
url="https://s2.static-footeo.com/100/uploads/aom-360/logo__76a9t2dll.png"
page="https://aom-360.footeo.com/"
id="1990262000093"
file=Path("flags/clubs/standard/outremer-2026-27")/(id+".png")
assert not file.exists()
r=requests.get(url,timeout=30,headers={"User-Agent":"MMD31 authentic French Guiana football club badge"});r.raise_for_status()
raw=r.content
img=Image.open(io.BytesIO(raw));img.verify()
logo=Image.open(io.BytesIO(raw)).convert("RGBA")
assert logo.width>=55 and logo.height>=55
box=logo.getchannel("A").getbbox();assert box
logo=logo.crop(box)
counts=collections.Counter()
for red,green,blue,a in logo.getdata():
 if a>120 and max(red,green,blue)-min(red,green,blue)>40:counts[(red//32,green//32,blue//32)]+=1
color=counts.most_common(1)[0][0] if counts else (6,6,6)
bg=tuple(min(255,int(.53*(q*32+16)+.47*255)) for q in color)
canvas=Image.new("RGBA",(120,96),bg+(255,))
logo.thumbnail((102,84),Image.Resampling.LANCZOS)
canvas.alpha_composite(logo,((120-logo.width)//2,(96-logo.height)//2))
out=io.BytesIO();canvas.convert("RGB").save(out,"PNG",optimize=True)
assert len(out.getvalue())>1200
file.write_bytes(out.getvalue())
record={"id":id,"name":"Aigles d'Or de Mana (A.O.M.)","source_page":page,"image":url,"image_source_sha256":hashlib.sha256(raw).hexdigest(),"png_sha256":hashlib.sha256(out.getvalue()).hexdigest(),"png_dimensions":[120,96],"notes":"Exact named club-owning page; crest visually shows A.O.M. and AIGLES D'OR DE MANA"}
Path("audit/outremer-2026-27/lot12_aom_mana.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PUBLISHED",record,flush=True)
