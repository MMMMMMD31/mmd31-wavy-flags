#!/usr/bin/env python3
"""MMD31 — source-linked R2/R3 2026-27 standard club crest production.
Output is a deterministic set of 120x96 PNGs; each affiliation gets one file,
shared by reserve teams when appropriate. No Victory Flags are created.
"""
from __future__ import annotations
import collections
import concurrent.futures
import hashlib
import io
import json
import math
from pathlib import Path
import colorsys
import time
from collections import deque
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

IN=Path("research-input/MMD31_RECHERCHE_R2_R3_2026_2027.json")
OUT=Path("flags/clubs/standard/r2r3-2026-27")
MANIFEST=Path("docs/research/mmd31-r2r3-2026-27")
UA={"User-Agent":"Mozilla/5.0 (compatible; MMD31 Source-linked Crest Research/1.1)"}

def get_image(affiliation):
    url=f"https://cdn-transverse.azureedge.net/phlogos/BC{affiliation}.jpg"
    error=None
    for trial in range(3):
        try:
            res=requests.get(url,headers=UA,timeout=22)
            res.raise_for_status()
            if not res.headers.get("content-type","").startswith("image/"):
                raise ValueError("image URL responded with non-image MIME")
            payload=res.content
            if len(payload)<450 or len(payload)>3_000_000:
                raise ValueError(f"implausible file size {len(payload)}")
            im=Image.open(io.BytesIO(payload)); im.load()
            if min(im.size)<30 or max(im.size)>5000:
                raise ValueError(f"implausible image size {im.size}")
            im=im.convert("RGBA")
            return {"affiliation":affiliation,"source_url":url,
                    "source_sha256":hashlib.sha256(payload).hexdigest(),
                    "source_dimensions":list(im.size)}, im
        except Exception as exc:
            error=str(exc)
            if trial<2:time.sleep(.4*(trial+1))
    return {"affiliation":affiliation,"status":"unresolved","error":error},None

def remove_white_edges(original):
    im=original.copy().convert("RGBA")
    if im.width*im.height>800_000:
        im.thumbnail((900,900),Image.Resampling.LANCZOS)
    w,h=im.size; px=im.load()
    q=deque([(x,0) for x in range(w)]+[(x,h-1) for x in range(w)]
            +[(0,y) for y in range(h)]+[(w-1,y) for y in range(h)])
    seen=bytearray(w*h)
    while q:
        x,y=q.pop(); pos=y*w+x
        if seen[pos]:continue
        seen[pos]=1
        r,g,b,a=px[x,y]
        if a<20:pass
        elif min(r,g,b)>=239 and max(r,g,b)-min(r,g,b)<=24:
            px[x,y]=(r,g,b,0)
        else:continue
        if x>0:q.append((x-1,y))
        if x+1<w:q.append((x+1,y))
        if y>0:q.append((x,y-1))
        if y+1<h:q.append((x,y+1))
    return im

def tone(original):
    # Dominant richly colored pixels, after ignoring almost-white/gray background.
    thumb=original.copy().convert("RGBA");thumb.thumbnail((110,110))
    freq=collections.Counter()
    for r,g,b,a in thumb.getdata():
        if a<130:continue
        h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
        if s<.22 or v<.18 or (v>.92 and s<.30):continue
        hue_bucket=round(h*24)%24
        freq[hue_bucket]+=max(1,round(s*4))
    if not freq:
        return (194,202,212),"neutral"
    # Pick strongest chromatic hue; preserve enough saturation for club identity.
    hue=freq.most_common(1)[0][0]/24
    r,g,b=colorsys.hsv_to_rgb(hue,.48,.94)
    raw=(round(r*255),round(g*255),round(b*255))
    # blend with white to leave the original crest clearly visible.
    result=tuple(round(0.69*x+0.31*255) for x in raw)
    return result,"dominant_hue_lightened"

def make_icon(img):
    original=img.copy()
    fg=remove_white_edges(img)
    crop=fg.getbbox()
    if crop: fg=fg.crop(crop)
    fg.thumbnail((99,81),Image.Resampling.LANCZOS)
    bgcolor,method=tone(original)
    bg=Image.new("RGBA",(120,96),(*bgcolor,255))
    x=(120-fg.width)//2;y=(96-fg.height)//2
    # Subtle edge shadow on alpha mask, prevents white artwork vanishing on pale field.
    silhouette=Image.new("RGBA",fg.size,(30,36,48,115))
    shadowalpha=fg.getchannel("A").filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.8))
    shadowalpha=shadowalpha.point(lambda v:round(v*.52))
    bg.paste(silhouette,(x,y),shadowalpha)
    bg.alpha_composite(fg,(x,y))
    out=io.BytesIO()
    bg.convert("RGB").save(out,format="PNG",optimize=True)
    return out.getvalue(),bgcolor,method

def main():
    assert IN.is_file(),f"Missing source research: {IN}"
    o=json.loads(IN.read_text(encoding="utf-8"))
    groups=o["groups"]
    if len(groups)!=153:raise SystemExit(f"expected 153 groups, got {len(groups)}")
    pairs=[(g,t) for g in groups for t in g["teams"]]
    if len(pairs)!=1848:raise SystemExit(f"expected 1848 raw participants, got {len(pairs)}")
    bykey={}
    for group,entry in pairs:
        key=entry.get("source_team_key")
        if not key or not entry.get("fff_affiliation"):
            raise SystemExit(f"Missing identity for {entry}")
        prev=bykey.get(key)
        # Source has two duplicate squad entries across R2/R3; retain the actual active R2
        # group entry, not an R3 line with zero games.
        val=(int(entry.get("played") or 0), 1 if group["division"]=="R2" else 0)
        if prev is None or val>(int(prev[1].get("played") or 0),1 if prev[0]["division"]=="R2" else 0):
            bykey[key]=(group,entry)
    if len(bykey)!=1846: raise SystemExit(f"expected 1846 distinct squad keys, got {len(bykey)}")
    affiliation_teams=collections.defaultdict(list)
    for squad_key,(group,entry) in bykey.items():
        affiliation_teams[str(entry["fff_affiliation"])].append({
            "source_team_key":squad_key,"name":entry["name"],
            "division":group["division"],"region":group["region"],
            "group":group.get("group"),"club_url":entry["club_url"]})
    print(f"SQUADS={len(bykey)} AFFILIATIONS={len(affiliation_teams)}",flush=True)
    OUT.mkdir(parents=True,exist_ok=True);MANIFEST.mkdir(parents=True,exist_ok=True)
    affils=sorted(affiliation_teams)
    image_results={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        fut={executor.submit(get_image,aff):aff for aff in affils}
        n=0
        for future in concurrent.futures.as_completed(fut):
            aff=fut[future]; image_results[aff]=future.result()
            n+=1
            if n%200==0 or n==len(affils):
                print(f"Image fetch {n}/{len(affils)}; success={sum(x[1] is not None for x in image_results.values())}",flush=True)
    # Reject a fallback/placeholder shared between different registered clubs.
    hashes=collections.defaultdict(set)
    for aff,(meta,img) in image_results.items():
        if img is not None:hashes[meta["source_sha256"]].add(aff)
    resolved={}; problems=[]
    contact=[]
    for aff in affils:
        meta,im=image_results[aff]
        meta["teams"]=affiliation_teams[aff]
        if im is not None and len(hashes[meta["source_sha256"]])>1:
            meta["status"]="unresolved"
            meta["error"]="same source-image hash used for distinct affiliations; possible placeholder"
            im=None
        if im is not None:
            data,bg,method=make_icon(im)
            path=OUT/f"bc{aff}.png"
            path.write_bytes(data)
            meta.update({"status":"published_candidate","path":path.as_posix(),
                         "raw_url":f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-r2r3-standard-crests-20261022/{path.as_posix()}",
                         "png_sha256":hashlib.sha256(data).hexdigest(),
                         "size":[120,96],"background_rgb":list(bg),"background_rule":method})
            resolved[aff]=meta
            if len(contact)<120 and (len(resolved)-1)%max(1,len(affils)//120)==0:
                contact.append((aff,Image.open(io.BytesIO(data)).convert("RGB")))
        else:
            problems.append(meta)
        image_results[aff]=(meta,None)
    cols=10;tilew=130;tileh=123
    sheet=Image.new("RGB",(cols*tilew,math.ceil(len(contact)/cols)*tileh),"white")
    draw=ImageDraw.Draw(sheet)
    for i,(aff,im) in enumerate(contact):
        x=i%cols*tilew+5;y=i//cols*tileh+5
        sheet.paste(im,(x,y))
        draw.text((x,y+98),f"FFF {aff}",fill="black")
    sheet.save(MANIFEST/"contact_sheet.png",optimize=True)
    manifest={
        "season":"2026-2027","source":"TheFootData 2026-27 / FFF affiliation / original club crest",
        "format":"120x96 RGB PNG, centered genuine crest on dominant/secondary-like lightened color, no Victory Flags",
        "branch":"mmd31-r2r3-standard-crests-20261022",
        "expected_squad_keys":1846,"squad_count":len(bykey),
        "distinct_affiliations":len(affils),"published_affiliations":len(resolved),
        "unresolved_affiliations":len(problems),
        "items":{aff:meta for aff,(meta,_) in image_results.items()}
    }
    (MANIFEST/"crest_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    (MANIFEST/"unresolved.json").write_text(json.dumps(problems,ensure_ascii=False,indent=2),encoding="utf-8")
    readme=[
        "# MMD31 — R2/R3 club crest audit","",
        f"- Unique verified squad IDs: **{len(bykey)}**",
        f"- Distinct club affiliations: **{len(affils)}**",
        f"- Standard PNGs: **{len(resolved)}**",
        f"- Unresolved source crests: **{len(problems)}**",
        "- Format: 120 × 96 RGB PNG with centered actual crest and lighter dominant-hue background.",
        "- A club's B/C teams reuse its affiliation crest. No Victory Flags.",
        "- Every image is linked to its original club affiliation and source URL in the manifest.",
        "- Synthetic/impostor logos are not used; unresolved crest URLs remain unchanged in JSON.",
        "- This is an automated source-linked technical check, not manual verification of every crest."
    ]
    (MANIFEST/"README.md").write_text("\n".join(readme)+"\n",encoding="utf-8")
    print(f"DONE PNG={len(resolved)} UNRESOLVED={len(problems)}",flush=True)
    if len(resolved)<int(len(affils)*.90):
        raise SystemExit("Low source retrieval success — do not publish this batch")

if __name__=="__main__":main()
