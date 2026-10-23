#!/usr/bin/env python3
"""Convert manually inspected candidate public club badges into 120x96 game flags; no invented logos."""
import io,time,json,hashlib
from pathlib import Path
from collections import deque
import requests
from PIL import Image,ImageOps,ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES=True
CATALOG=[[1900262702000,"KSK Heist","https://primary.jwwb.nl/public/u/p/j/temp-bpazrmsmlmyifrylaudz/k-sk_-heist-transparant-high.png?enable=upscale&enable-io=true&fit=bounds&width=1200",[167,193,231]],[1900262702001,"FC Mandel United","https://www.codecblend.com/v3/images/stories/virtuemart/product/resized/royal-fc-mandel-united-thumbnail_640x640.jpg",[232,185,190]],[1900262702002,"Racing Club Harelbeke","https://www.krcgent.be/sites/krcgent.be/files/styles/og/public/images/opponents/logo_krc_harelbeke.png?itok=f3RzNpDF",[212,191,227]],[1900262702004,"K Lyra-Lierse","https://logowik.com/content/uploads/images/k-lyra-lierse-berlaar.jpg",[245,226,164]],[1900262702005,"Royal Knokke FC","https://vormeracademy.com/assets/logo-knokke-fc-6OCfFPyI.png",[185,220,241]],[1900262702007,"Hoogstraten VV","https://images.seeklogo.com/logo-png/29/1/hoogstraten-vv-logo-png_seeklogo-295040.png",[242,192,192]],[1900262702008,"KVK Tienen","https://www.logotypes101.com/logos/7/0C0BA148AC27973B4DEE646DABD90FC1/KVK_Tienen.png",[193,222,220]],[1900262702010,"KFC Merelbeke","https://files.tips.gg/static/image/teams/merelbeke-football.png",[244,234,155]],[1900262702011,"Thes Sport","https://www.voetbalinbelgie.be/images/club_logo_van_voetbalvereniging_thes-sport-tessenderlo-kvv_uit_tessenderlo.png",[245,225,147]],[1900262702012,"KFC Houtvenne","https://images.seeklogo.com/logo-png/39/1/kfc-houtvenne-logo-png_seeklogo-398677.png",[177,220,173]],[1900262702013,"Belisia Bilzen","https://www.belisiasv.be/media/5j5ar0n4/belisia_logo_small.png",[188,228,245]],[1900262702014,"SK Roeselare","https://framerusercontent.com/images/vYIUpWcmIiTs6avxTYvKBxGfncE.png?height=1000&width=1000",[217,217,217]],[1900262702015,"KVV Zelzate","https://sporting.be/wp-content/uploads/2020/07/kvvzelzate.jpg",[186,220,192]],[1900262702100,"RFC Meux","https://cdn-img.zerozero.pt/img/logos/equipas/46478_imgbank_1710327891.png",[191,229,198]],[1900262702104,"Renaissance Union Tubize-Braine","https://logowik.com/content/uploads/images/royale-union-tubize-braine1895.logowik.com.webp",[238,193,184]],[1900262702107,"RAEC Mons","https://fanshop.raecmons44.be/cdn/shop/files/Mons-logo.png?v=1768412580",[251,227,159]],[1900262702109,"CS Onhaye","https://www.voetbalinbelgie.be/images/club_logo_van_voetbalvereniging_onhaye-rcs_uit_onnhaye.png?v=20250504221320",[240,187,187]],[1900262702110,"RCS Habay-la-Neuve","https://fastly.mwm-storage.mwmcdn.com/raw_files/028d6d01-ad94-4a7a-80fe-d583b1346a7b",[239,188,188]],[1900262702111,"FC Flénu","https://www.telemb.be/cdn/ff/pBISMY7DWjvRYtEWDN79iN-V68677Dq-JHF35MmSCZ4/1690094741/public/2023-07/00000148_base64.png",[236,189,184]]]
ROOT=Path("docs/belgian-d3-clubs-2026-27/v13")
ROOT.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (MMD31 Football Crest Research, 2026-10-23)"})
def border_white_to_alpha(im):
 im=im.convert("RGBA")
 im.thumbnail((650,650))
 w,h=im.size;p=im.load()
 def white(x,y):
  r,g,b,a=p[x,y]
  return a>0 and r>244 and g>244 and b>244 and max(r,g,b)-min(r,g,b)<12
 q=deque()
 for xx in range(w):
  if white(xx,0):q.append((xx,0))
  if white(xx,h-1):q.append((xx,h-1))
 for yy in range(h):
  if white(0,yy):q.append((0,yy))
  if white(w-1,yy):q.append((w-1,yy))
 seen=set()
 while q:
  x,y=q.popleft()
  if (x,y) in seen or not white(x,y):continue
  seen.add((x,y));p[x,y]=(255,255,255,0)
  for u,v in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
   if 0<=u<w and 0<=v<h and (u,v) not in seen:q.append((u,v))
 b=im.getchannel('A').getbbox()
 return im.crop(b) if b else im
statuses=[]
for id_,name,url,rgb in CATALOG:
 row={"id":id_,"name":name,"source":url,"status":"FAILED"}
 try:
  error=None
  for attempt in range(3):
   try:
    res=s.get(url,timeout=30);res.raise_for_status()
    if len(res.content)<500:raise ValueError("too small")
    raw=Image.open(io.BytesIO(res.content)).convert("RGBA")
    if raw.width<60 or raw.height<60:raise ValueError("bad source image dimensions")
    icon=border_white_to_alpha(raw)
    icon.thumbnail((98,82),Image.Resampling.LANCZOS)
    target=Image.new("RGBA",(120,96),tuple(rgb)+(255,))
    target.alpha_composite(icon,((120-icon.width)//2,(96-icon.height)//2))
    dest=ROOT/f"{id_}.png";target.convert("RGB").save(dest,optimize=True)
    check=Image.open(dest)
    assert check.size==(120,96) and dest.stat().st_size>1500
    row.update(status="SOURCE_IMAGE_PUBLISHED_IDENTITY_CANDIDATE",source_dimensions=[raw.width,raw.height],background=rgb,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-v13-d3-assets/{dest.as_posix()}")
    break
   except Exception as ex:
    error=ex;time.sleep(2+attempt)
  if row["status"]=="FAILED":row["error"]=str(error)
 except Exception as ex:row["error"]=str(ex)
 statuses.append(row);print(row["id"],name,row["status"],row.get("error",""),flush=True)
statuspath=ROOT/"catalog_extra_status.json"
statuspath.write_text(json.dumps({"count":len(statuses),"ok":sum(x["status"]!="FAILED" for x in statuses),"assets":statuses},indent=2,ensure_ascii=False))
print("Finished",sum(x["status"]!="FAILED" for x in statuses),"out of",len(statuses))
