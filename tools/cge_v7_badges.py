#!/usr/bin/env python3
"""Create 120x96 PNGs from reviewed football SVG crests; report any failure."""
from pathlib import Path
from io import BytesIO
import colorsys, json, hashlib, time
import requests
import cairosvg
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/"tools/cge_v7_badges_sources.txt"
OUTPUT=ROOT/"docs/cge-v7-d3-2026-27/v1"
OUTPUT.mkdir(parents=True,exist_ok=True)
BASE="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/"
session=requests.Session()
manifest=[]
for line in SOURCES.read_text(encoding="utf-8").splitlines():
    if not line.strip() or line.startswith("#"):continue
    tid,source=line.split("|",1)
    url=BASE+source
    entry={"id":int(tid),"source":url,"status":"NOT_BUILT"}
    for attempt in range(3):
        try:
            response=session.get(url,timeout=25)
            response.raise_for_status()
            raw=response.content
            if len(raw)>3_000_000 or not raw.lstrip().startswith((b"<",b"<?xml")):
                raise ValueError("Not an SVG XML image")
            logo=Image.open(BytesIO(cairosvg.svg2png(bytestring=raw,output_width=500))).convert("RGBA")
            logo.thumbnail((106,82),Image.Resampling.LANCZOS)
            opaque=logo.getdata()
            # Derive pale background from visible saturated pixels of the authentic crest.
            colors={}
            for idx,(r,g,b,a) in enumerate(opaque):
                if idx%7 or a<150:continue
                h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
                if s>0.35 and 0.17<v<0.97:
                    q=(r//24,g//24,b//24)
                    colors[q]=colors.get(q,0)+1
            if colors:
                q=max(colors,key=colors.get)
                base=[min(255,k*24+12) for k in q]
                bgcolor=tuple(int(0.65*255+0.35*c) for c in base)
            else:bgcolor=(238,241,245)
            image=Image.new("RGBA",(120,96),bgcolor+(255,))
            image.alpha_composite(logo,((120-logo.width)//2,(96-logo.height)//2))
            path=OUTPUT/(tid+".png")
            image.convert("RGB").save(path,format="PNG",optimize=True)
            assert Image.open(path).size==(120,96)
            entry.update(status="PNG_120x96",sha256=hashlib.sha256(path.read_bytes()).hexdigest(),path=str(path.relative_to(ROOT)),bgcolor=bgcolor)
            break
        except Exception as exc:
            entry["status"]="ERROR"
            entry["error"]=str(exc)[:350]
            if attempt<2:time.sleep(attempt+1)
    manifest.append(entry)
(OUTPUT/"manifest.json").write_text(json.dumps({"count":len(manifest),"successful":sum(x["status"]=="PNG_120x96" for x in manifest),"crests":manifest},indent=2,ensure_ascii=False),encoding="utf-8")
print("CREATED",sum(x["status"]=="PNG_120x96" for x in manifest),"/",len(manifest))
for x in manifest:
    if x["status"]!="PNG_120x96":print("ERROR",x["id"],x.get("error",""))
