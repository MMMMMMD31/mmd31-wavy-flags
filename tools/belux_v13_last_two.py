#!/usr/bin/env python3
"""Resolve the last two Belgian D3 badges, source identity documented. No invented crests."""
import requests,re,io,json,hashlib,time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageFilter
ROOT=Path("docs/belgian-d3-clubs-2026-27/v13")
ROOT.mkdir(parents=True,exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 Club Crest Study/1.0)"})
def get_image(url):
 r=S.get(url,timeout=22,headers={"Referer":"https://www.belisiasv.be/"},allow_redirects=True)
 r.raise_for_status()
 if not r.headers.get("Content-Type","").lower().startswith("image/") and not r.content.startswith((b'\\x89PNG',b'\\xff\\xd8',b'RIFF',b'GIF')):
  raise ValueError("not an image "+str(r.headers.get("Content-Type")))
 im=Image.open(io.BytesIO(r.content)).convert("RGBA")
 if im.width<70 or im.height<65:raise ValueError("image too small")
 return im
def try_urls(club,urls):
 checks=[]
 for src in dict.fromkeys(urls):
  if src is None:continue
  try:
   im=get_image(src)
   print("ACCEPT",club,src,im.size,flush=True)
   return im,src,checks
  except Exception as exc:
   checks.append({"url":src,"error":str(exc)[:160]})
   print("REJECT",club,src,str(exc)[:130],flush=True)
 return None,None,checks
def official_urls():
 u="https://www.belisiasv.be/"
 r=S.get(u,timeout=30);r.raise_for_status()
 print("OFFICIAL_HOME",r.url,len(r.content),flush=True)
 soup=BeautifulSoup(r.text,"html.parser")
 res=[]
 for e in soup.find_all(["img","source","meta"]):
  text=" ".join(str(e.get(k,"")) for k in ("alt","src","data-src","srcset","content","title")).lower()
  if "belisia" in text and ("logo" in text or "image" in text):
   for k in ("src","data-src","content"):
    if e.get(k):res.append(urljoin(r.url,e.get(k)))
   if e.get("srcset"):
    res+= [urljoin(r.url,z.strip().split(" ")[0]) for z in str(e.get("srcset")).split(",") if z.strip()]
 print("OFFICIAL_CANDIDATES",res[:25],flush=True)
 return res
rows=[]
entries=[
 {"id":1900262702013,"name":"Belisia Bilzen SV","background":[199,235,248],"source_note":"Official Belisia website, active crest"},
 {"id":1900262702102,"name":"Union Rochefortoise","background":[191,218,241],"source_note":"Wikimedia Commons photo of first authentic Union Rochefortoise crest (2020); present-day badge version requires independent confirmation"}
]
for z in entries:
 try:
  if z["id"]==1900262702013:
   urls=[
    "https://www.belisiasv.be/media/5j5ar0n4/belisia_logo_small.png",
    "https://belisiasv.be/media/5j5ar0n4/belisia_logo_small.png"
   ]
   try:urls+=official_urls()
   except Exception as e:print("OFFICIAL_PAGE_ERROR",str(e),flush=True)
  else:
   urls=[
     "https://commons.wikimedia.org/wiki/Special:Redirect/file/Logo-Union-Rochefortoise-Avril2020.png",
     "https://upload.wikimedia.org/wikipedia/commons/8/8e/Logo-Union-Rochefortoise-Avril2020.png"
   ]
  im,url,checks=try_urls(z["name"],urls)
  z["attempts"]=checks
  if im is None:
   z["status"]="SOURCE_NOT_RETRIEVED";rows.append(z);continue
  # preserve genuinely sourced crest on flat coloured background
  # The Belisia official site uses a horizontal crest+wordmark lockup.
  # Extract the actual left-side circular emblem; avoid an illegible horizontal wordmark.
  if z["id"]==1900262702013 and im.width > im.height*1.6:
   im=im.crop((0,0,min(im.height,im.width),im.height))
   im=im.crop(im.getchannel("A").getbbox() or (0,0,im.width,im.height))
  # The documented 2020 Union Rochefortoise photo has a square matte.
  # Crop to its circular badge without changing the real logo artwork.
  if z["id"]==1900262702102:
   from PIL import ImageDraw
   m=Image.new("L",im.size,0)
   d=ImageDraw.Draw(m)
   d.ellipse((2,2,im.width-3,im.height-3),fill=255)
   im.putalpha(m)
  im.thumbnail((97,82),Image.Resampling.LANCZOS)
  if im.mode!="RGBA":im=im.convert("RGBA")
  # white outer matte only when image touches image border in large quantities
  if im.getchannel("A").getextrema()[0]==255:
   im0=im.copy()
   px=im0.load();ww,hh=im0.size
   # keep source white interior; remove only edge-connected near-white
   from collections import deque
   q=deque([(j,0) for j in range(ww)]+[(j,hh-1) for j in range(ww)]+[(0,j) for j in range(hh)]+[(ww-1,j) for j in range(hh)])
   seen=set()
   while q:
    u,v=q.popleft()
    if (u,v) in seen:continue
    seen.add((u,v))
    rr,gg,bb,aa=px[u,v]
    if min(rr,gg,bb)<247 or max(rr,gg,bb)-min(rr,gg,bb)>8:continue
    px[u,v]=(255,255,255,0)
    for a,b in ((u+1,v),(u-1,v),(u,v+1),(u,v-1)):
     if 0<=a<ww and 0<=b<hh and (a,b) not in seen:q.append((a,b))
   box=im0.getchannel("A").getbbox()
   if box:im=im0.crop(box)
  im.thumbnail((97,82),Image.Resampling.LANCZOS)
  bg=Image.new("RGBA",(120,96),tuple(z["background"])+(255,))
  bg.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  p=ROOT/f'{z["id"]}.png';bg.convert("RGB").save(p,optimize=True)
  assert Image.open(p).size==(120,96) and p.stat().st_size>1200
  z.update(status="PUBLISHED_AUTHENTIC_HISTORICAL" if z["id"]==1900262702102 else "PUBLISHED_OFFICIAL",source=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=[120,96],url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-v13-d3-assets/{p.as_posix()}")
 except Exception as e:
  z["status"]="FAILED";z["error"]=str(e)[:250]
 rows.append(z)
 print("RESULT",z["name"],z["status"],flush=True)
(ROOT/"final_two_status.json").write_text(json.dumps({"assets":rows,"count_published":sum("PUBLISHED" in x["status"] for x in rows)},indent=2,ensure_ascii=False))
