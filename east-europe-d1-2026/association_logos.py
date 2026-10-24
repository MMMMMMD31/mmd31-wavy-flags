import io,json,requests
from pathlib import Path
import cairosvg
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/competition-logos/east-europe-d1-2026"
OUT.mkdir(parents=True,exist_ok=True)
result={}
for nation in ("BLR","UKR","MDA","GEO"):
 url=f"https://img.uefa.com/imgml/uefacom/elements/logos/ma/{nation}.svg"
 try:
  r=requests.get(url,timeout=18,headers={"User-Agent":"Mozilla/5.0"})
  r.raise_for_status()
  if b"<svg" not in r.content[:2000]:raise ValueError("not SVG")
  png=cairosvg.svg2png(bytestring=r.content,output_width=320,output_height=320)
  im=Image.open(io.BytesIO(png)).convert("RGBA")
  bounds=im.getbbox()
  if not bounds:raise ValueError("empty image")
  im=im.crop(bounds)
  im.thumbnail((256,256),Image.Resampling.LANCZOS)
  icon=Image.new("RGBA",(320,320),(0,0,0,0))
  icon.alpha_composite(im,((320-im.width)//2,(320-im.height)//2))
  path=OUT/(nation.lower()+"-association.png")
  icon.save(path,"PNG")
  with Image.open(path) as check:
   assert check.size==(320,320) and check.format=="PNG"
  result[nation]={"status":"PUBLISHED","provider":"UEFA member association emblem","source":url,"path":str(path.relative_to(ROOT)),"dimensions":[320,320]}
 except Exception as exc:
  result[nation]={"status":"MISSING","provider":"UEFA member association emblem","source":url,"error":str(exc)}
 (ROOT/"east-europe-d1-2026/associations-manifest.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
 print(nation,result[nation]["status"],flush=True)
