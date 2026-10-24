#!/usr/bin/env python3
"""Collect real logos of football competition governing bodies. Never invent logos."""
import requests,io,json,re,hashlib
from PIL import Image
from pathlib import Path
import cairosvg
O=Path("docs/portugal-gibraltar-clubs-2026-27/competition-logos")
O.mkdir(parents=True,exist_ok=True)
srcs=[
 ("portugal_fpf_2026","https://upload.wikimedia.org/wikipedia/commons/5/52/Federa%C3%A7%C3%A3o_Portuguesa_de_Futebol_logo_%282026%29.svg","Federação Portuguesa de Futebol — new 2026 logo, Wikimedia Commons"),
 ("gibraltar_gfa","https://upload.wikimedia.org/wikipedia/commons/d/d3/Gibraltar_Football_Association_logo.svg","Gibraltar Football Association, Wikimedia Commons"),
]
res=[]
for slug,url,provenance in srcs:
 try:
  r=requests.get(url,timeout=25,headers={"User-Agent":"MMD31ClubSimulation/1.0 (crest provenance)"})
  r.raise_for_status();assert b'<svg' in r.content[:7000],(slug,"not SVG")
  png=cairosvg.svg2png(bytestring=r.content,output_width=500)
  image=Image.open(io.BytesIO(png)).convert("RGBA")
  image.thumbnail((560,560),Image.Resampling.LANCZOS)
  canvas=Image.new("RGBA",(560,560),(0,0,0,0))
  canvas.alpha_composite(image,((560-image.width)//2,(560-image.height)//2))
  output=O/(slug+".png");canvas.save(output,format="PNG",optimize=True)
  with Image.open(output) as ck:assert ck.size==(560,560) and ck.format=="PNG"
  res.append({"slug":slug,"source":url,"source_sha256":hashlib.sha256(r.content).hexdigest(),"path":str(output),"png_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"provenance":provenance,"ok":True})
 except Exception as e:res.append({"slug":slug,"source":url,"error":str(e),"ok":False})
(O/"status.json").write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(res,ensure_ascii=False))
