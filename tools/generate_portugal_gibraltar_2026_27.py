#!/usr/bin/env python3
"""Render identified Portuguese and Gibraltar crests on solid club-hued 120x96 backgrounds.
Only real source images are used; missing/invalid downloads are explicitly audited.
"""
import csv, io, json, hashlib, time, concurrent.futures, math
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image, ImageOps, ImageChops
import requests
import cairosvg

SRC=Path("tools/portugal_gibraltar_2026_27_sources.csv")
OUT=Path("docs/portugal-gibraltar-clubs-2026-27/v1")
OUT.mkdir(parents=True, exist_ok=True)
rows=list(csv.DictReader(SRC.open(encoding="utf-8-sig",newline="")))
assert len(rows)==400, len(rows)
assert len(set(r["team_id"] for r in rows))==400
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31-ClubCrestRenderer/1.0)"})
cache={}

def fetch(url):
    err=None
    for attempt in range(3):
        try:
            r=SESSION.get(url, timeout=(12,28), headers={"Accept":"image/avif,image/webp,image/svg+xml,image/png,image/jpeg,image/gif,*/*"})
            r.raise_for_status()
            b=r.content
            if len(b)<80 or len(b)>5_000_000: raise RuntimeError("invalid byte size")
            if "<html" in b[:1000].decode("utf-8","ignore").lower():raise RuntimeError("HTML instead of image")
            if ".svg" in urlsplit(url).path.lower() or b"<svg" in b[:2048].lower():
                b=cairosvg.svg2png(bytestring=b, output_width=480)
            im=Image.open(io.BytesIO(b)).convert("RGBA")
            im.load()
            if im.width<20 or im.height<20: raise ValueError("tiny crest")
            return im,hashlib.sha256(b).hexdigest()
        except Exception as e:
            err=e
            time.sleep(.45*(attempt+1))
    raise RuntimeError(str(err)[:160])

def trim_white_margin(image):
    im=image
    al=im.getchannel("A")
    bbox=al.getbbox()
    if bbox: im=im.crop(bbox)
    # Crop only fully empty peripheral white rows; do not erase white parts of club crest
    if im.width>50 and im.height>50:
        px=im.load()
        corner=[px[0,0],px[im.width-1,0],px[0,im.height-1],px[im.width-1,im.height-1]]
        if all(min(p[:3])>240 and p[3]>230 for p in corner):
            diff=ImageChops.difference(im.convert("RGB"),Image.new("RGB",im.size,(255,255,255)))
            bb=diff.point(lambda v:0 if v<24 else 255).getbbox()
            if bb and bb[2]>bb[0]+18 and bb[3]>bb[1]+18:
                im=im.crop(bb)
    return im

def get_background(im, given):
    px=im.copy()
    px.thumbnail((112,112))
    buckets=Counter()
    for r,g,b,a in px.getdata():
        if a<150: continue
        hi,lo=max(r,g,b),min(r,g,b)
        if hi-lo<40 or hi<70 or lo>228: continue
        key=(r//24,g//24,b//24)
        buckets[key]+=a
    if buckets:
        k=buckets.most_common(1)[0][0]
        color=tuple(min(255,v*24+12) for v in k)
        provenance="derived from crest chromatic pixels"
    elif given and given.upper()!="#ECECEC":
        color=tuple(int(given[i:i+2],16) for i in (1,3,5))
        provenance="manifest club color"
    else:
        color=(209,217,227)
        provenance="neutral fallback: crest has no reliable chromatic dominant color"
    # Lighten to avoid placing dark details of the badge on a dark background.
    brightness=sum(color)/3
    mix=.40 if brightness<100 else (.28 if brightness<158 else .12)
    color=tuple(round(c*(1-mix)+245*mix) for c in color)
    return color, provenance

def work(row):
    tid=int(row["team_id"]); url=row["source"].strip(); name=row["team"].strip()
    try:
        im,src_sha=fetch(url)
        im=trim_white_margin(im)
        if not im.getchannel("A").getbbox(): raise ValueError("transparent crest")
        color,color_origin=get_background(im,row["color"])
        canvas=Image.new("RGBA",(120,96),color+(255,))
        im.thumbnail((100,84), Image.Resampling.LANCZOS)
        canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
        target=OUT/(str(tid)+".png")
        canvas.convert("RGB").save(target,format="PNG",optimize=True)
        with Image.open(target) as verify:
            assert verify.size==(120,96) and verify.format=="PNG"
            if len(verify.getcolors(120*96) or [])<10: raise ValueError("empty or single-color image")
        return {"id":tid,"name":name,"source":url,"source_sha256":src_sha,
                "path":target.as_posix(),"background":"#%02X%02X%02X"%color,
                "background_basis":color_origin,"png_sha256":hashlib.sha256(target.read_bytes()).hexdigest()}
    except Exception as e:
        return {"id":tid,"name":name,"source":url,"error":str(e)[:250]}

with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    output=sorted(ex.map(work,rows),key=lambda x:x["id"])
good=[x for x in output if "path" in x]
missing=[x for x in output if "error" in x]
status={"expected":400,"created":len(good),"missing_count":len(missing),
        "format":"PNG 120x96, real crest centered on solid club color derived from crest when possible",
        "generated_at":"2026-10-23","assets":good,"missing":missing}
(OUT/"status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("REAL CLUB CRESTS CREATED:",len(good),"/ 400 | FAILED:",len(missing),flush=True)
for entry in missing:print("FAIL",entry["id"],entry["name"],entry["error"],flush=True)
# Exit without failing so status.json and any successful real images are still published
