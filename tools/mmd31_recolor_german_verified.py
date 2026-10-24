#!/usr/bin/env python3
import io,json,hashlib,time
from collections import Counter
from pathlib import Path
import requests,cairosvg
from PIL import Image,ImageDraw
root=Path("docs/german-clubs-2026-27/missing-20261024")
catalog=json.loads((root/"manifest.json").read_text(encoding="utf8"))
session=requests.Session()
session.headers.update({"User-Agent":"MMD31-CrestPalette/1.0 (https://github.com/MMMMMMD31/mmd31-wavy-flags)"})
def get(url):
 for i in range(4):
  try:
   r=session.get(url,timeout=25)
   r.raise_for_status()
   if len(r.content)>8000000:raise ValueError("image too large")
   return r.content
  except Exception:time.sleep(i+1)
 raise RuntimeError("could not load source")
def recolor(content):
 if b"<svg" in content[:20000].lower():content=cairosvg.svg2png(bytestring=content,output_width=480)
 pic=Image.open(io.BytesIO(content)).convert("RGBA")
 bounds=pic.getchannel("A").getbbox()
 if not bounds:raise ValueError("empty logo")
 pic=pic.crop(bounds)
 small=pic.copy();small.thumbnail((120,120))
 weighted=Counter()
 for r,g,b,a in small.getdata():
  if a<75 or max(r,g,b)-min(r,g,b)<36:continue
  weighted[(r//32,g//32,b//32)]+=a
 if weighted:
  choice=weighted.most_common(1)[0][0]
  rgb=tuple(min(255,int((v*32+16)*.74+255*.26)) for v in choice)
 else:rgb=(102,119,148)
 pic.thumbnail((104,84),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",(120,96),rgb+(255,))
 canvas.alpha_composite(pic,((120-pic.width)//2,(96-pic.height)//2))
 return canvas.convert("RGB"),rgb
failed=[];complete=0
for i,club in enumerate(catalog):
 try:
  im,color=recolor(get(club["source"]))
  target=root/(str(club["teamId"])+".png")
  im.save(target,optimize=True)
  club["background_rgb"]=list(color)
  club["sha256"]=hashlib.sha256(target.read_bytes()).hexdigest()
  complete+=1
 except Exception as exc:failed.append({"id":club["teamId"],"message":str(exc)[:100]})
(root/"manifest.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
(root/"palette-status.json").write_text(json.dumps({"count":complete,"failed":failed},indent=2)+"\n",encoding="utf8")
print({"recolored":complete,"failed":len(failed)})
