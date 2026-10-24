#!/usr/bin/env python3
"""Publish league-organizer logo instead of national federation badge."""
from pathlib import Path
import requests,io,json,hashlib
from PIL import Image
out=Path("docs/portugal-gibraltar-clubs-2026-27/competition-logos")
out.mkdir(parents=True,exist_ok=True)
url="https://commons.wikimedia.org/wiki/Special:FilePath/S%C3%ADmbolo_da_Liga_Portuguesa_de_Futebol_Profissional.png"
r=requests.get(url,headers={"User-Agent":"MMD31 Football League Edition (Commons historic attribution)","Accept":"image/png,*/*"},timeout=30)
r.raise_for_status()
logo=Image.open(io.BytesIO(r.content)).convert("RGBA")
assert logo.width>=200 and logo.height>=200,(logo.size)
logo.thumbnail((470,485),Image.Resampling.LANCZOS)
canvas=Image.new("RGBA",(512,512),(255,255,255,255))
canvas.alpha_composite(logo,((512-logo.width)//2,(512-logo.height)//2))
target=out/"liga_portugal_d1_logo.png"
canvas.save(target,format="PNG",optimize=True)
with Image.open(target) as im: assert im.size==(512,512) and im.format=="PNG"
meta={"logo":"Liga Portugal (Liga Portuguesa de Futebol Profissional)","source":url,"source_attribution":"Liga Portugal via Wikimedia Commons, CC BY-SA 4.0","source_sha256":hashlib.sha256(r.content).hexdigest(),"size":[512,512],"path":str(target),"sha256":hashlib.sha256(target.read_bytes()).hexdigest()}
(out/"liga_portugal_d1_logo_manifest.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(meta,ensure_ascii=False))
