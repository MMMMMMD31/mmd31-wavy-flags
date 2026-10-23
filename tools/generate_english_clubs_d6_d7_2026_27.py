#!/usr/bin/env python3
"""Build official MMD31 English club flag PNGs from traceable upstream SVG badges."""
import io, json, time
from collections import Counter
from pathlib import Path
from urllib.parse import quote
import cairosvg
import requests
from PIL import Image, ImageDraw

ROOT = Path("docs/english-clubs-2026-27/d6-d7")
ROOT.mkdir(parents=True, exist_ok=True)
CATALOG = json.loads(Path("tools/english_clubs_d6_d7_2026_27_sources.json").read_text(encoding="utf-8"))
session = requests.Session()
session.headers.update({"User-Agent": "MMD31EnglishClubAssets/1.0 (GitHub Actions; club badge source attribution)"})

def srcurl(path):
    return "https://raw.githubusercontent.com/JoseArroyave/football-logos/main/" + "/".join(quote(bit, safe="") for bit in path.split("/"))

def fetch(url):
    error = None
    for attempt in range(4):
        try:
            r=session.get(url,timeout=27)
            r.raise_for_status()
            if len(r.content) < 200:
                raise ValueError("SVG suspiciously small")
            return r.content
        except Exception as exc:
            error=exc
            time.sleep(1.5*(attempt+1))
    raise RuntimeError(f"Cannot read SVG source {url}: {error}")

def dominant(im):
    pix=im.copy()
    pix.thumbnail((90,90))
    weighted=Counter()
    for r,g,b,a in pix.getdata():
        if a < 80: continue
        mx,mn=max(r,g,b),min(r,g,b)
        if mx-mn < 35 or mx<55: continue
        key=(r//32,g//32,b//32)
        weighted[key] += a
    if weighted:
        r,g,b=[min(255,x*32+16) for x in weighted.most_common(1)[0][0]]
    else:
        r,g,b=(50,70,100)
    # Retain club hue but soften dark colors to protect legibility.
    return (int(.76*r+.24*255),int(.76*g+.24*255),int(.76*b+.24*255))

def build_badge(svg):
    png=cairosvg.svg2png(bytestring=svg,output_width=480)
    image=Image.open(io.BytesIO(png)).convert("RGBA")
    bbox=image.getchannel("A").getbbox()
    if not bbox: raise ValueError("SVG rendered transparent")
    image=image.crop(bbox)
    fill=dominant(image)
    bg=Image.new("RGBA",(120,96),fill+(255,))
    image.thumbnail((98,82),Image.Resampling.LANCZOS)
    x,y=(120-image.width)//2,(96-image.height)//2
    # Contrast plate only when crest is predominantly white/low contrast.
    px=list(image.getdata())
    white=sum(1 for r,g,b,a in px if a>90 and min(r,g,b)>225)
    solid=sum(1 for *_,a in px if a>90)
    if solid and white/solid>.55:
        plate=Image.new("RGBA",(image.width+8,image.height+6),(248,248,248,215))
        bg.alpha_composite(plate,(max(0,x-4),max(0,y-3)))
    bg.alpha_composite(image,(x,y))
    return bg.convert("RGB"),fill

assets=[]
for row in CATALOG:
    u=srcurl(row["source_path"])
    print("Rendering",row["id"],row["name"],u,flush=True)
    image,color=build_badge(fetch(u))
    output=ROOT/(str(row["id"])+".png")
    image.save(output,format="PNG",optimize=True)
    assert Image.open(output).size==(120,96)
    assets.append({"id":row["id"],"name":row["name"],"source":u,
                   "github_path":output.as_posix(),"background_rgb":list(color),
                   "bytes":output.stat().st_size})
status={"count":len(assets),"expected":136,"size":[120,96],
        "source_repository":"JoseArroyave/football-logos",
        "victory_flags_created":0,"assets":assets}
assert len(assets)==136, f"Only {len(assets)} generated"
(ROOT/"status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SUCCESS 136/136 PNG images; status.json created",flush=True)
