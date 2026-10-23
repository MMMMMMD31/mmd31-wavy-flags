#!/usr/bin/env python3
"""Render 147 German D1–D4 actual club crest images for MMD31.
Source artwork is traced per-club to JoseArroyave/football-logos.
No invented logos, no wave effect, no victory flag. Creates 120x96 PNG.
"""
from __future__ import annotations
import hashlib
import io
import json
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import cairosvg
import requests
from PIL import Image, ImageDraw

ROOT = Path("docs/german-clubs-2026-27/v1")
ROOT.mkdir(parents=True, exist_ok=True)
CATALOG = json.loads(Path("tools/german_clubs_2026_27_sources.json").read_text(encoding="utf-8"))
assert len(CATALOG) == 147 and len({r["id"] for r in CATALOG}) == 147
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "MMD31-GermanyCrests/1.0 (GitHub Actions; contact via GitHub mmd31-wavy-flags)"})

def source_url(path):
    return "https://raw.githubusercontent.com/JoseArroyave/football-logos/main/" + "/".join(quote(seg, safe="") for seg in path.split("/"))

def fetch(url):
    error = None
    for attempt in range(4):
        try:
            resp = SESSION.get(url, timeout=28)
            resp.raise_for_status()
            if len(resp.content) < 150 or not b"<svg" in resp.content[:1500].lower():
                raise ValueError("Upstream SVG missing or unrecognizable")
            return resp.content
        except Exception as exc:
            error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Cannot load SVG {url}: {error}")

def color_palette(img):
    thumb = img.copy()
    thumb.thumbnail((90, 90))
    colored = Counter()
    for r,g,b,a in thumb.getdata():
        if a < 65:
            continue
        if max(r,g,b)-min(r,g,b) < 30:
            continue
        key = (r//32,g//32,b//32)
        colored[key] += a
    out = []
    for key,_ in colored.most_common(5):
        col = tuple(min(255,x*32+16) for x in key)
        softened = tuple(int(.78*x+.22*255) for x in col)
        out.append(softened)
    return out or [(75, 101, 136)]

def draw_crest(svg):
    rendered = cairosvg.svg2png(bytestring=svg, output_width=480)
    image = Image.open(io.BytesIO(rendered)).convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if not bounds:
        raise ValueError("Transparent/invisible crest")
    image = image.crop(bounds)
    bg_color = color_palette(image)[0]
    # Render actual club crest at maximum comfortable size and keep aspect.
    image.thumbnail((104,84), Image.Resampling.LANCZOS)
    x = (120-image.width)//2
    y = (96-image.height)//2
    bg = Image.new("RGBA",(120,96),bg_color+(255,))
    # A subtle backing plate may improve white-only source crests.
    colored = [p for p in image.getdata() if p[3]>85]
    white = sum(1 for r,g,b,a in colored if min(r,g,b)>220)
    if colored and white/len(colored)>.55:
        pad=3
        ImageDraw.Draw(bg).rounded_rectangle(
           (max(0,x-pad),max(0,y-pad),min(119,x+image.width+pad),min(95,y+image.height+pad)),
           radius=7, fill=(245,246,247,210))
    bg.alpha_composite(image,(x,y))
    return bg.convert("RGB"), bg_color

assets = []
for i,row in enumerate(CATALOG, 1):
    url = source_url(row["source_path"])
    svg = fetch(url)
    image, color = draw_crest(svg)
    output = ROOT / (str(row["id"])+".png")
    image.save(output,format="PNG",optimize=True)
    assert Image.open(output).size == (120,96), row["name"]
    assets.append({"id":row["id"],"name":row["name"],"source":url,
                   "source_sha256":hashlib.sha256(svg).hexdigest(),
                   "github_path":str(output),"background_rgb":list(color),
                   "png_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
                   "png_bytes":output.stat().st_size})
    print(f"{i:03d}/147 {row['name']} -> {output.name}",flush=True)

assert len(assets)==147
status = {"count":len(assets),"expected":147,"canvas":[120,96],
          "source_repository":"JoseArroyave/football-logos",
          "victory_flags_created":0,"assets":assets}
(ROOT/"status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SUCCESS: 147/147 real German club crests rendered in 120x96",flush=True)
