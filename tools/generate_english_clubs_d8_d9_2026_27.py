#!/usr/bin/env python3
"""MMD31 D8/D9: render only verified real crest SVGs; no invented badges."""
import io,json,time
from pathlib import Path
from urllib.parse import quote
import cairosvg,requests
from PIL import Image
from collections import Counter
cat=json.loads(Path("tools/english_clubs_d8_d9_2026_27_sources.json").read_text())
out=Path("docs/english-clubs-2026-27/d8-d9");out.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({"User-Agent":"MMD31 crest migration; source JoseArroyave football-logos"})
def url(path):return "https://raw.githubusercontent.com/JoseArroyave/football-logos/main/"+"/".join(quote(x,safe="") for x in path.split("/"))
def download(u):
 for n in range(4):
  try:
   r=s.get(u,timeout=25);r.raise_for_status();assert len(r.content)>200
   return r.content
  except Exception:
   if n==3:raise
   time.sleep(1+n)
def bgcolor(im):
 im=im.copy();im.thumbnail((90,90));m=Counter()
 for r,g,b,a in im.getdata():
  if a<80 or max(r,g,b)-min(r,g,b)<35 or max(r,g,b)<55:continue
  m[(r//32,g//32,b//32)]+=a
 if m:
  r,g,b=(min(255,x*32+16) for x in m.most_common(1)[0][0])
 else:r,g,b=(50,70,100)
 return tuple(int(.76*v+.24*255) for v in (r,g,b))
found=[];missing=[]
for row in cat:
 path=row.get("source_path")
 if not path:
  missing.append({"id":row["id"],"name":row["name"],"division":row["division"]})
  continue
 svg=download(url(path))
 png=cairosvg.svg2png(bytestring=svg,output_width=480)
 im=Image.open(io.BytesIO(png)).convert("RGBA")
 box=im.getchannel("A").getbbox()
 if not box:raise ValueError("Empty crest "+row["name"])
 im=im.crop(box);bg=Image.new("RGBA",(120,96),bgcolor(im)+(255,))
 im.thumbnail((98,82),Image.Resampling.LANCZOS)
 bg.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 final=bg.convert("RGB")
 target=out/(str(row["id"])+".png");final.save(target,"PNG",optimize=True)
 assert Image.open(target).size==(120,96)
 found.append({"id":row["id"],"name":row["name"],"path":target.as_posix(),"source_url":url(path),"size":target.stat().st_size})
 print("Wrote",row["id"],row["name"],flush=True)
assert len(cat)==498 and len(found)==81 and len(missing)==417,(len(cat),len(found),len(missing))
(out/"status.json").write_text(json.dumps({"total":len(cat),"published":len(found),"not_found":len(missing),"assets":found,"unmatched":missing},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("COMPLETE",len(found),"real crests; unmatched",len(missing),flush=True)
