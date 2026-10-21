#!/usr/bin/env python3
"""Generate MMD31 120×96 crested flags from actual club crests; log source status."""
import io, json, math, os, re, time
from pathlib import Path
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
BASE=Path(__file__).resolve().parent
TEAMS=json.loads((BASE/"roster.json").read_text(encoding="utf8"))["teams"]
S=requests.Session(); S.headers.update({"User-Agent":"MMD31ClubFlagResearch/1.0 (public educational simulator; GitHub workflow)"})
def download(url):
 try:
  r=S.get(url,timeout=7,headers={"User-Agent":"Mozilla/5.0 (MMD31 sports graphics)"});r.raise_for_status()
  if len(r.content)>5_000_000:return None
  if "<svg" in r.text[:250].lower() or url.lower().split("?")[0].endswith(".svg"):
   import cairosvg
   return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=r.content,output_width=480,output_height=480))).convert("RGBA")
  return Image.open(io.BytesIO(r.content)).convert("RGBA")
 except Exception: return None

def wiki_crest(team):
 # Prefer club badge from Wikipedia infobox; reject article hero image not in infobox.
 titles=[team["wiki"]]
 for lang in ("fr","en"):
  for title in titles:
   url=f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ','_'))}"
   try:
    r=S.get(url,timeout=6);r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    selectors=["table.infobox_v2 img","table.infobox img","aside.portable-infobox img","table.infobox_v3 img"]
    for selector in selectors:
     imgs=soup.select(selector)
     for im in imgs[:3]:
      alt=(im.get("alt") or "").lower()
      if any(x in alt for x in ("drapeau","map","localisation","carte","stade")):continue
      loc=im.get("srcset", "").split(",")[0].split(" ")[0] or im.get("src")
      if not loc: continue
      loc=("https:"+loc) if loc.startswith("//") else urljoin(url,loc)
      img=download(loc)
      if img and img.width>25 and img.height>25:
       return img,loc
   except Exception:continue
 return None,None

def build(t):
 slug=t["slug"]; div=t["division"]
 crest,source=wiki_crest(t)
 if crest is None:
  return {"club":t["name"],"division":div,"status":"NO_AUTHENTIC_CRESPONSE","source":None}
 crest.thumbnail((73,73),Image.Resampling.LANCZOS)
 W,H=120,96
 base=Image.new("RGBA",(W,H),t["color"])
 overlay=Image.new("RGBA",(W,H),(0,0,0,0))
 ImageDraw.Draw(overlay).rounded_rectangle((19,7,101,89),radius=15,fill=(255,255,255,60))
 base=Image.alpha_composite(base,overlay)
 base.alpha_composite(crest,((W-crest.width)//2,(H-crest.height)//2))
 dest=BASE/div/"standard";dest.mkdir(parents=True,exist_ok=True)
 base.save(dest/(slug+".png"),"PNG",optimize=True)
 dst=Image.new("RGBA",(W,H),(0,0,0,0))
 o=dst.load();b=base.load()
 for y in range(H):
  dx=3*math.sin(y*2*math.pi/72+.4)
  for x in range(W):
   ripple=2.2*math.sin(x*2*math.pi/84+y*2*math.pi/125)
   if not(3+dx <= x < 117+dx and 4+ripple <= y < 92+ripple):continue
   ix=int(round(x-dx));iy=int(round(y-ripple))
   if 0<=ix<W and 0<=iy<H:
    R,G,B,A=b[ix,iy]
    f=1+0.06*math.sin(x*2*math.pi/70+y/20)
    o[x,y]=(min(255,int(R*f)),min(255,int(G*f)),min(255,int(B*f)),A)
 v=BASE/div/"victory";v.mkdir(parents=True,exist_ok=True)
 dst.save(v/(slug+".png"),"PNG",optimize=True)
 assert Image.open(v/(slug+".png")).size==(120,96)
 return {"club":t["name"],"division":div,"status":"AUTHENTIC_WIKI_INFOBOX_CREST","source":source}
results=[]
with ThreadPoolExecutor(max_workers=6) as pool:
 for f in as_completed([pool.submit(build,t) for t in TEAMS]):
  try:results.append(f.result())
  except Exception as e:results.append({"status":"ERROR","error":str(e)})
report={"generated":sum(x["status"]=="AUTHENTIC_WIKI_INFOBOX_CREST" for x in results),"requested":len(TEAMS),"results":sorted(results,key=lambda x:x.get("club",""))}
(BASE/"crest-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps({"generated":report["generated"],"missing":[x for x in results if x["status"]!="AUTHENTIC_WIKI_INFOBOX_CREST"]},ensure_ascii=False))
