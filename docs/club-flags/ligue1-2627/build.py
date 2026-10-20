#!/usr/bin/env python3
"""MMD31 - exact crest composites, 120x96 PNG normal and Victory flags."""
import base64, io, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parent
SRC = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
OUT = ROOT
W,H = 120,96

for club in SRC["clubs"]:
    slug = club["slug"]
    crest = Image.open(io.BytesIO(base64.b64decode(club["png_base64"]))).convert("RGBA")
    crest.thumbnail((73,73), Image.Resampling.LANCZOS)
    standard = Image.new("RGBA", (W,H), club["bg"])
    # Slightly illuminated support keeps red/blue crests legible on matching colours.
    plate = Image.new("RGBA", (W,H), (0,0,0,0))
    d = ImageDraw.Draw(plate)
    d.rounded_rectangle((19,9,101,87), radius=15, fill=(255,255,255,62))
    standard = Image.alpha_composite(standard,plate)
    x=(W-crest.width)//2; y=(H-crest.height)//2
    standard.alpha_composite(crest,(x,y))
    (OUT/"standard").mkdir(exist_ok=True)
    standard.save(OUT/"standard"/(slug+".png"), optimize=True)
    # Real waving geometry: horizontal shift per scanline, gently rippled top & bottom.
    # Transparent corners; no pole. All pixels outside the cloth remain transparent.
    srcpix=standard.load()
    victory=Image.new("RGBA",(W,H),(0,0,0,0))
    dst=victory.load()
    for py in range(H):
        left = 4 + round(2.6*math.sin(py*2*math.pi/66))
        right = 117 + round(1.3*math.sin(py*2*math.pi/84+1.1))
        for px in range(W):
            # A shallow wavy edge, flowing horizontally across the fabric.
            crest_warp = 2.4*math.sin(px*2*math.pi/84+py*2*math.pi/125)
            sy = py - crest_warp
            if not (left <= px < right and 4+crest_warp <= py < 92+crest_warp):
                continue
            sx=px-round(3.1*math.sin(py*2*math.pi/72+0.4))
            if 0<=sx<W and 0<=sy<H:
                r,g,b,a=srcpix[sx,max(0,min(H-1,round(sy)))]
                light=1+0.075*math.sin(px*2*math.pi/64+py/20.0)
                dst[px,py]=(min(255,int(r*light)),min(255,int(g*light)),min(255,int(b*light)),a)
    (OUT/"victory").mkdir(exist_ok=True)
    victory.save(OUT/"victory"/(slug+".png"),optimize=True)
    assert standard.size==(120,96) and victory.size==(120,96)
    assert victory.getpixel((0,0))[3]==0
    print(slug, standard.size, "PNG + wavy transparent PNG")
