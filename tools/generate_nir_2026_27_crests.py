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

def download(url,timeout=27):
    last=None
    for i in range(3):
        try:
            r=requests.get(url,timeout=timeout,headers={"User-Agent":"MMD31ClubCrestAudit/1.0"})
            r.raise_for_status()
            if not 200<len(r.content)<7000000:raise ValueError("Invalid image size")
            return r.content
        except requests.exceptions.Timeout as e:
            last=e
            time.sleep(i+1)
    raise last

def load(blob,url):
    if url.split("?")[0].lower().endswith(".svg"):
        blob=cairosvg.svg2png(bytestring=blob,output_width=480)
    im=Image.open(io.BytesIO(blob))
    im.load()
    if min(im.size)<24 or max(im.size)>6000:raise ValueError("Invalid dimensions")
    im=im.convert("RGBA")
    # Remove only the border-connected near-white source background.
    from PIL import ImageDraw
    for point in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]:
        px=im.getpixel(point)
        if min(px[:3])>=243 and px[3]>230:
            ImageDraw.floodfill(im,point,(255,255,255,0),thresh=13)
    if not im.getchannel("A").getbbox():raise ValueError("Empty image")
    return im

# Authoritative COMET standings and club catalogue from the Northern Amateur Football League.
def nafl_index():
    index={}
    for resource in ("tables.json","clubs-dev.json"):
        url="https://www.thenafl.co.uk/data/"+resource
        try:
            data=json.loads(download(url,timeout=25))
            if resource=="tables.json":
                for div,section in data.items():
                    for entry in section.get("table",[]):
                        badge=entry.get("badge")
                        name=entry.get("team","")
                        if name and badge and norm(name) not in index:
                            index[norm(name)]=(name,"https://www.thenafl.co.uk/images/badges/"+badge,"official_nafl_comet_standings")
            else:
                for entry in data:
                    badge=entry.get("badge")
                    name=entry.get("name","")
                    if name and badge and norm(name) not in index:
                        index[norm(name)]=(name,"https://www.thenafl.co.uk/images/badges/"+badge,"official_nafl_club_catalogue")
        except Exception as e:print("NAFL INDEX FAILURE",resource,str(e)[:170],flush=True)
    return index
NAFL=nafl_index()
NAFL_ALIASES={
    "Dunmurry Young Men":"Dunmurry YM",
    "Derriaghy Cricket Club":"Derriaghy CC",
    "Larne Technical Old Boys":"Larne Tech OB",
    "1st Bangor Old Boys":"1st Bangor",
    "Kilmore Recreation":"Kilmore Rec",
    "Dunmurry Recreation":"Dunmurry Rec",
    "18th Newtownabbey Old Boys":"18th Newtownabbey OB",
    "Ballywalter Rec":"Ballywalter Rec",
    "Comber Recreation":"Comber Rec",
    "Rosario Youth":"Rosario YC",
}
MUFL_SOURCE_OVERRIDE={
    "St Mary’s YC":"stmarys",
}
EUROPLAN={
"Fivemiletown United":"8ffcfc7accf484c83020df676e501145.png",
"Richhill AFC":"2e345d7bdd99c23688929967e57d27da.png",
"Newtowne":"60b6b69b88e1a80c68209657c382fe16.png",
"Desertmartin":"5292b6012bf24f2cfb1bd89135d2b58e.png",
"Heights FC":"45b955641e85c8f0a2da517e3ec302f7.png",
"Wellington Recreation":"70eb1589506dacf7cb501c35b70425c7.png",
"Newbuildings United":"534394d9a63c2675809fa163cac18693.png",
"Belfast Celtic":"45c37000f60e449f258e628e88db893b.png",
"Maiden City":"932aaf418d4fba1a4388537cebed84fd.png"
}
SEEKLOGO={
"Cookstown Youth":"https://images.seeklogo.com/logo-png/63/1/cookstown-youth-football-club-logo-png_seeklogo-634100.png",
"Killymoon Rangers":"https://images.seeklogo.com/logo-png/20/1/killymoon-rangers-fc-logo-png_seeklogo-208144.png",
"Inspired Talents":"https://images.seeklogo.com/logo-png/63/1/inspired-talents-fc-logo-png_seeklogo-634041.png"
}
def source(c):
    if c["name"]=="Trojans YCG":
        # The original crest from the club's own Pitchero page (club ID 73051).
        sources=[
            ("https://img-res.pitchero.com/?url=images.pitchero.com%2Fclub_logos%2F73051%2Fclublogo_58f3dcf90586c.png&bg=null&h=360&w=360&t=absolute&q=null","trojans_official_pitchero_club_badge"),
            ("https://cfkzqicresplbojnqrej.supabase.co/storage/v1/object/public/partner-images/clubs/cmobp00gs005dpu1vn4kn2iuc.png","trojans_identified_junior_grassroots_hub"),
        ]
        for url,kind in sources:
            try:return load(download(url,timeout=25),url),url,kind
            except Exception as e:print("TROJANS BADGE SOURCE ERROR",str(e)[:120],flush=True)
    if c["name"] in EUROPLAN:
        url="https://www.europlan-online.de/files/"+EUROPLAN[c["name"]]
        try:return load(download(url,timeout=25),url),url,"europlan_verified_named_club"
        except Exception as e:print("EUROPLAN FAILURE",c["name"],str(e)[:100],flush=True)
    if c["name"] in SEEKLOGO:
        url=SEEKLOGO[c["name"]]
        try:return load(download(url,timeout=25),url),url,"seeklogo_exact_identified_club"
        except Exception as e:print("SEEKLOGO FAILURE",c["name"],str(e)[:100],flush=True)
    if c.get("direct_url"):
        url=c["direct_url"]
        return load(download(url),url),url,"visually_checked_2026_crest"
    if c.get("svg"):
        url="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/northern-ireland/"+quote(c["svg"])
        return load(download(url),url),url,"public_svg"
    # Original crest in public-domain Wikimedia library for this particular club.
    if c["name"]=="Dromara Village":
        url="https://commons.wikimedia.org/wiki/Special:Redirect/file/Dromara_Village_FC.png"
        try:return load(download(url),url),url,"commons_identified_authentic_badge"
        except Exception:pass
    # Official Mid Ulster league publishes one club badge file per club.
    if c["division"] in ("D4_MUFL","D5_MUFL"):
        stem=MUFL_SOURCE_OVERRIDE.get(c["name"],norm(c["name"]))
        url="https://midulsterfootballleague.co.uk/wp-content/uploads/2026/06/"+stem+".jpg"
        try:return load(download(url,timeout=20),url),url,"official_mid_ulster_club_profile"
        except Exception as e:print("MIDULSTER ERROR",c["name"],str(e)[:80],flush=True)
    # Cross-check club identity against official Northern Amateur League 2026/27.
    nafl_name=NAFL_ALIASES.get(c["name"],c["name"])
    entry=NAFL.get(norm(nafl_name))
    if c["division"] in ("D4_NAFL","D5_NAFL","D6_NAFL_1B","D7_NAFL_1C") and entry:
        original_name,url,kind=entry
        if norm(original_name)!=norm(nafl_name):raise ValueError("NAFL ambiguous team")
        return load(download(url,timeout=25),url),url,kind
    if c["division"] in ("D4_MUFL","D5_MUFL"):
        url="https://www.midulsterfootballleague.co.uk/img/badges/"+norm(c["name"])+".jpg"
        try:
            return load(download(url,timeout=12),url),url,"official_midulster_filename_candidate"
        except Exception:
            pass
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
    dest=ROOT/(str(c["id"])+".png")
    if dest.exists() and c["id"] in PRIOR and PRIOR[c["id"]].get("status")=="created":
        entry=dict(PRIOR[c["id"]])
        entry["preserved_existing"]=True
        return entry
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

old_status_file=ROOT/"status.json"
PRIOR={}
if old_status_file.exists():
    old=json.loads(old_status_file.read_text())
    PRIOR={x["id"]:x for x in old.get("crests",[]) if x.get("status")=="created"}
print("existing verified 120x96 crests",len(PRIOR),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    rows=list(pool.map(process,CAT))
rows.sort(key=lambda r:r["id"])
result={"created":sum(x["status"]=="created" for x in rows),"expected":len(CAT),"missing_count":sum(x["status"]=="missing" for x in rows),"size":[120,96],"victory_flags_created":0,"crests":rows}
(ROOT/"status.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
assert sum(x["status"]=="created" for x in rows[:12])==12,"All 12 top-flight sources must resolve"
print("DONE",result["created"],"of",result["expected"])
