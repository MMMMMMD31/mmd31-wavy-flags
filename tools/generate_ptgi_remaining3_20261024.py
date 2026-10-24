#!/usr/bin/env python3
"""Publish verifiable club-specific 120x96 badges, leave failed sources missing."""
import requests,io,json,hashlib,time
from pathlib import Path
from PIL import Image,ImageChops
source=[
(1905100000419,"Guadalupe","https://www.ogol.com.br/img/logos/equipas/5666_imgbank_1766857712.png"),
(1905100000422,"FC Calheta","https://cdn-img.zerozero.pt/img/logos/equipas/19571_imgbank_1711622224.png"),
(1905100000423,"GD Velense","https://www.zerozero.pt/img/logos/equipas/3714_imgbank_1709047235.png"),
]
root=Path("docs/portugal-gibraltar-clubs-2026-27/v1")
out=[]
for tid,name,url in source:
 try:
  r=requests.get(url,timeout=24,headers={"User-Agent":"Mozilla/5.0"});r.raise_for_status()
  im=Image.open(io.BytesIO(r.content)).convert("RGBA")
  if im.width<80 or im.height<80:raise ValueError("Too small")
  # White-background extraction only via border-adjacent colors; preserve internal white.
  bg=Image.new("RGB",(120,96),(222,230,221))
  if tid==1905100000419:bg=Image.new("RGB",(120,96),(131,187,145))
  if tid==1905100000422:bg=Image.new("RGB",(120,96),(143,170,215))
  if tid==1905100000423:bg=Image.new("RGB",(120,96),(221,193,131))
  original=im
  if all(min(im.getpixel(c)[:3])>240 for c in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]):
   diff=ImageChops.difference(im.convert("RGB"),Image.new("RGB",im.size,"white"))
   bb=diff.point(lambda v:255 if v>24 else 0).getbbox()
   if bb:im=im.crop(bb)
   p=im.load()
   for y in range(im.height):
    for x in range(im.width):
     R,G,B,A=p[x,y];whiteness=min(R,G,B)
     if whiteness>=250:p[x,y]=(R,G,B,0)
  im.thumbnail((101,84),Image.Resampling.LANCZOS)
  canvas=Image.new("RGBA",(120,96),bg.getpixel((0,0))+(255,))
  canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  file=root/(str(tid)+".png");canvas.convert("RGB").save(file,optimize=True)
  out.append({"id":tid,"name":name,"url":url,"ok":True,"file":str(file),"sha256":hashlib.sha256(file.read_bytes()).hexdigest()})
 except Exception as e:out.append({"id":tid,"name":name,"url":url,"ok":False,"error":str(e)})
(root/"status-last3-20261024.json").write_text(json.dumps(out,indent=2,ensure_ascii=False))
print(json.dumps(out,ensure_ascii=False))
