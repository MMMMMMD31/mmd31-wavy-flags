#!/usr/bin/env python3
import io,json,hashlib
from pathlib import Path
import requests,cairosvg
from PIL import Image,ImageFilter
ROOT=Path("docs/belgian-d3-clubs-2026-27/v13");ROOT.mkdir(parents=True,exist_ok=True)
SOURCE="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/belgium/"
catalog=[
(1900262702006,"KFC Dessel Sport","KFC_Dessel_Sport.svg",(245,222,85)),
(1900262702101,"RWDM Brussels","RWDM_Brussels.svg",(226,204,218)),
(1900262702106,"Olympic Charleroi","Olympic_Charleroi.svg",(245,209,212)),
]
result=[]
for id_,name,filename,color in catalog:
 url=SOURCE+filename
 r=requests.get(url,timeout=30,headers={"User-Agent":"MMD31-BELUX-V13/1.0"});r.raise_for_status()
 assert b"<svg" in r.content[:2000]
 crest=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=r.content,output_width=500))).convert('RGBA')
 box=crest.getchannel('A').getbbox();assert box
 crest=crest.crop(box);crest.thumbnail((96,81),Image.Resampling.LANCZOS)
 image=Image.new('RGBA',(120,96),(*color,255));x=(120-crest.width)//2;y=(96-crest.height)//2
 image.alpha_composite(crest,(x,y));p=ROOT/f'{id_}.png';image.convert('RGB').save(p,optimize=True)
 assert Image.open(p).size==(120,96)
 result.append({"id":id_,"name":name,"source":url,"status":"SOURCE_CANDIDATE_TO_VERIFY_CURRENT_IDENTITY","size":[120,96],"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"url":f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-v13-d3-assets/{p.as_posix()}"})
(ROOT/"status.json").write_text(json.dumps({"count":len(result),"crests":result},ensure_ascii=False,indent=2))
print("success",len(result))
