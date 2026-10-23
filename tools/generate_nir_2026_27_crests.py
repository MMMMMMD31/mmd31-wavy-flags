#!/usr/bin/env python3
"""MMD31 Northern Ireland club crests: source-verified 120x96 images, no invented logos."""
import json, re, io, time, hashlib, concurrent.futures, unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import quote
import requests, cairosvg
from PIL import Image, ImageDraw

ROOT=Path("docs/nir-clubs-2026-27/v1")
ROOT.mkdir(parents=True,exist_ok=True)
CAT=json.loads(Path("tools/nir_2026_27_sources.json").read_text())
assert len(CAT)==142 and len({x["id"] for x in CAT})==142

def norm(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    for t in (" football club"," fc"," afc"):s=s.replace(t,"")
    return re.sub("[^a-z0-9]","",s.replace("&","and"))

def download(url,timeout=19):
    r=requests.get(url,timeout=timeout,headers={"User-Agent":"MMD31ClubCrestAudit/1.0"})
    r.raise_for_status()
    if not 200<len(r.content)<7000000:raise ValueError("Invalid image size")
    return r.content

def load(blob,url):
    if url.split("?")[0].lower().endswith(".svg"):
        blob=cairosvg.svg2png(bytestring=blob,output_width=480)
    im=Image.open(io.BytesIO(blob))
    im.load()
    if min(im.size)<50 or max(im.size)>6000:raise ValueError("Invalid dimensions")
    im=im.convert("RGBA")
    if not im.getchannel("A").getbbox():raise ValueError("Empty image")
    return im

def source(c):
    if c.get("svg"):
        url="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/northern-ireland/"+quote(c["svg"])
        return load(download(url),url),url,"public_svg"
    url="https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t="+quote(c["name"])
    data=json.loads(download(url,timeout=12))
    hits=[]
    for t in data.get("teams") or []:
        if norm(t.get("strTeam") or "")!=norm(c["name"]):continue
        if (t.get("strCountry") or "").lower().strip() not in ("northern ireland","united kingdom","uk","n. ireland"):continue
        if (t.get("strSport") or "").lower() not in ("soccer","football"):continue
        u=t.get("strBadge") or t.get("strLogo")
        if u and u.startswith("https://"):hits.append(u)
    if len(hits)!=1:raise ValueError("No uniquely identified matching badge")
    url=hits[0]
    return load(download(url),url),url,"sportsdb_exact_name_country"

def dominant(im):
    thumb=im.copy();thumb.thumbnail((90,90))
    histogram=Counter()
    for r,g,b,a in thumb.getdata():
        if a<110 or max(r,g,b)-min(r,g,b)<37:continue
        histogram[(r//32,g//32,b//32)]+=a
    if histogram:
        rgb=tuple(min(255,n*32+16) for n in histogram.most_common(1)[0][0])
    else:rgb=(70,100,160)
    return tuple(int(.68*x+.32*255) for x in rgb)

def render(original):
    img=original.crop(original.getchannel("A").getbbox())
    bg=dominant(img)
    canvas=Image.new("RGBA",(120,96),bg+(255,))
    img.thumbnail((102,82),Image.Resampling.LANCZOS)
    x=(120-img.width)//2;y=(96-img.height)//2
    opaque=[(r,g,b) for r,g,b,a in img.getdata() if a>110]
    if opaque and sum(min(p)>225 for p in opaque)/len(opaque)>.56:
        ImageDraw.Draw(canvas,"RGBA").rounded_rectangle((max(0,x-4),max(0,y-3),min(119,x+img.width+3),min(95,y+img.height+3)),radius=3,fill=(255,255,255,140))
    canvas.alpha_composite(img,(x,y))
    return canvas.convert("RGB"),bg

def process(c):
    entry={"id":c["id"],"name":c["name"],"division":c["division"],"status":"missing"}
    try:
        src,url,kind=source(c)
        im,bg=render(src)
        path=ROOT/(str(c["id"])+".png")
        im.save(path,optimize=True)
        with Image.open(path) as verified:assert verified.size==(120,96) and verified.format=="PNG"
        entry.update(status="created",source_url=url,source_kind=kind,background_rgb=bg,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    except Exception as ex:entry["error"]=str(ex)[:180]
    print(entry["status"],entry["id"],entry["name"],entry.get("error",""),flush=True)
    return entry

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    rows=list(pool.map(process,CAT))
rows.sort(key=lambda r:r["id"])
result={"created":sum(x["status"]=="created" for x in rows),"expected":len(CAT),"missing_count":sum(x["status"]=="missing" for x in rows),"size":[120,96],"victory_flags_created":0,"crests":rows}
(ROOT/"status.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
assert sum(x["status"]=="created" for x in rows[:12])==12,"All 12 top-flight sources must resolve"
print("DONE",result["created"],"of",result["expected"])
