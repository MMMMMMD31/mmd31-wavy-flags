#!/usr/bin/env python3
"""MMD31: create 120x96 Spanish club badge flags from traceable real SVG crests."""
from pathlib import Path
from collections import Counter
from io import BytesIO
from urllib.parse import quote
import hashlib
import json
import math
import time
import requests
import cairosvg
from PIL import Image, ImageDraw, ImageFilter

OUT = Path("docs/spanish-clubs-2026-27/v1")
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = [x.strip() for x in Path("tools/spanish_clubs_2026_27_sources.txt").read_text(encoding="utf-8").splitlines() if x.strip()]
assert len(SOURCES) == 172
ROOT_URL = "https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/spain/"
session = requests.Session()
session.headers["User-Agent"] = "MMD31SpanishCrests/1.0 (noncommercial football simulator)"
cache = {}

def get_crest(name):
    if name not in cache:
        url = ROOT_URL + quote(name, safe="") + ".svg"
        error = None
        for retry in range(5):
            try:
                response = session.get(url, timeout=32)
                response.raise_for_status()
                body = response.content
                if b"<svg" not in body[:4000] or len(body) < 150:
                    raise ValueError("Not a valid SVG source")
                rendered = cairosvg.svg2png(bytestring=body, output_width=500, output_height=500)
                im = Image.open(BytesIO(rendered)).convert("RGBA")
                bbox = im.getchannel("A").getbbox()
                if bbox is None:
                    raise ValueError("Transparent SVG")
                cache[name] = (im.crop(bbox), url, hashlib.sha256(body).hexdigest())
                break
            except Exception as exc:
                error = repr(exc)
                time.sleep((retry+1)*1.8)
        if name not in cache:
            raise RuntimeError("Cannot render %s: %s" % (name,error))
    return cache[name]

def choose_color(crest):
    small = crest.copy()
    small.thumbnail((90,90))
    counts=Counter()
    for red,green,blue,alpha in small.getdata():
        if alpha < 115 or max(red,green,blue)-min(red,green,blue)<50:
            continue
        if max(red,green,blue)<40:
            continue
        counts[(red//30,green//30,blue//30)] += alpha
    if not counts:
        return (75,103,146)
    rgb=counts.most_common(1)[0][0]
    raw=[min(255, n*30+15) for n in rgb]
    return tuple(round(v*.66+255*.34) for v in raw)

def flat(crest, color):
    im=Image.new("RGBA",(120,96), color+(255,))
    logo=crest.copy()
    logo.thumbnail((92,82), Image.Resampling.LANCZOS)
    x=(120-logo.width)//2
    y=(96-logo.height)//2
    if color[0]+color[1]+color[2]>645:
        # Light badge border for crest visibility
        halo=Image.new("RGBA",(logo.width+6,logo.height+6),(0,0,0,0))
        halo.alpha_composite(logo,(3,3))
        mask=halo.getchannel("A").filter(ImageFilter.MaxFilter(5))
        outline=Image.new("RGBA",halo.size,(30,40,50,64))
        outline.putalpha(mask.point(lambda a:round(a*.23)))
        im.alpha_composite(outline,(max(0,x-3),max(0,y-3)))
    im.alpha_composite(logo,(x,y))
    return im

def wavy(source):
    w,h=120,96
    bg=source.convert("RGBA")
    pixels=bg.load()
    canvas=Image.new("RGBA",(w,h),(0,0,0,0))
    output=canvas.load()
    for y in range(h):
        for x in range(w):
            # Decorative emoji-flag outline; transparent exterior corners.
            shift=3.1*math.sin(y*2*math.pi/60) + 1.6*math.sin(x*2*math.pi/92)
            u=int(round(x-shift))
            v=int(round(y-2.5*math.sin(2*math.pi*x/90)))
            if not (0<=u<w and 0<=v<h):
                continue
            yy=y/(h-1)
            xx=x/(w-1)
            # Subtle wave mask at top and bottom edges.
            top=3+3*math.sin(2*math.pi*xx+0.4)
            bottom=92+3*math.sin(2*math.pi*xx+0.4)
            if y<top or y>bottom:
                continue
            # Transparent rounded corners.
            if x<7 and (y<7-x or y>88+x):
                continue
            if x>112 and (y<x-112 or y>207-x):
                continue
            r,g,b,a=pixels[u,v]
            light=0.94+0.09*math.sin(x*2*math.pi/55+.5)
            output[x,y] = tuple(min(255,max(0,int(v*light))) for v in (r,g,b)) + (a,)
    return canvas

status=[]
for ix, name in enumerate(SOURCES,1):
    id_=1884500100000+ix
    crest, url, digest=get_crest(name)
    color=choose_color(crest)
    base=flat(crest,color)
    flag=OUT/(str(id_)+".png")
    victory=OUT/(str(id_)+"-victory.png")
    base.save(flag,format="PNG",optimize=True)
    wavy(base).save(victory,format="PNG",optimize=True)
    for f in (flag,victory):
        img=Image.open(f)
        assert img.size==(120,96) and img.format=="PNG"
        assert f.stat().st_size > 550
    status.append({"id":id_,"source_path":"logos/spain/"+name+".svg",
                   "source_url":url,"source_sha256":digest,
                   "flag_path":str(flag),"victory_flag_path":str(victory),
                   "background_rgb":color,
                   "flag_sha256":hashlib.sha256(flag.read_bytes()).hexdigest(),
                   "victory_sha256":hashlib.sha256(victory.read_bytes()).hexdigest()})
    print("%d/172 %s %s" % (ix,id_,name),flush=True)

assert len(status)==172
(OUT/"status.json").write_text(json.dumps({"count":172,"size":[120,96],"assets":status,
  "upstream":"JoseArroyave/football-logos","rights_note":"Club emblems are third-party trademarks; used for personal simulator fan project.",
  "source_handling":"Reserve teams may intentionally inherit the parent-club emblem; review before using as unique academy logo."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS 172 flat PNG + 172 victory PNG; source metadata written",flush=True)
