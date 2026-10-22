#!/usr/bin/env python3
"""Collect source-linked R1 2026/27 club crests. Never synthesize a club identity.
Experimental, fail-closed research pipeline for a separate GitHub branch.
"""
from __future__ import annotations
import collections, concurrent.futures, hashlib, io, json, re, time, unicodedata
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
from collections import deque

ROOT = "https://thefootdata.com/competitions/regional-1"
SITE = "https://thefootdata.com"
LEAGUES = [
 "auvergne-rhone-alpes","bourgogne-franche-comte","bretagne",
 "centre-val-de-loire","corse","grand-est","hauts-de-france",
 "mediterranee","normandie","nouvelle-aquitaine","occitanie",
 "paris-ile-de-france","pays-de-la-loire"]
BASE = Path("docs/research/mmd31-r1-2026-27")
OUT = Path("flags/clubs/standard/r1-2026-27")
UA = {"User-Agent":"Mozilla/5.0 (compatible; MMD31SourceAudit/1.0)"}
def get(url):
    resp = requests.get(url, headers=UA, timeout=25)
    resp.raise_for_status()
    return resp

def norm(s):
    return re.sub(r"[^a-z0-9]+","-",unicodedata.normalize("NFKD",s)
                  .encode("ascii","ignore").decode("ascii").lower()).strip("-")

def groups_for(league):
    url=f"{ROOT}?organisme={league}"
    soup=BeautifulSoup(get(url).text,"html.parser")
    found={}
    for a in soup.select('a[href]'):
        u=urljoin(url,a['href']); p=parse_qs(urlparse(u).query)
        if p.get("organisme",[None])[0]!=league or not p.get("poule"): continue
        if p.get("saison",["2026"])[0]!="2026": continue
        lbl=a.get_text(" ",strip=True)
        if not lbl.lower().startswith(("poule","groupe")):continue
        found[p['poule'][0]]=u
    return [(league,k,url) for k,url in sorted(found.items())]

def entries_for(task):
    league,poule,url=task
    soup=BeautifulSoup(get(url).text,"html.parser")
    found=[]
    for table in soup.select("table"):
        thead=table.find("thead")
        head=thead.get_text(" ",strip=True).lower() if thead else ""
        if not ("pts" in head and ("équipe" in head or "equipe" in head)):continue
        for tr in table.select("tr"):
            td=tr.find_all("td",recursive=False)
            if len(td)<8 or not re.match(r"^\s*\d+\s*$",td[0].get_text(" ",strip=True)):continue
            a=td[1].find("a",href=True)
            if a is None:continue
            name=a.get_text(" ",strip=True)
            if not name:continue
            found.append({"name":name,"league":league,"group":poule,
                         "club_url":urljoin(SITE,a['href']),"group_url":url})
        if found: break
    return found

def source_for(item):
    obj=dict(item)
    try:
        html=get(item["club_url"]).text
        soup=BeautifulSoup(html,"html.parser")
        text=soup.get_text(" ",strip=True)
        match=re.search(r"\bAffiliation\s+(\d{6,7})\b",text,re.I)
        if not match:raise ValueError("club affiliation not found")
        aff=match.group(1)
        candidates=[]
        for image in soup.select("img[src]"):
            src=urljoin(item["club_url"],image.get("src",""))
            if f"/phlogos/BC{aff}" in src: candidates.append(src)
        if not candidates:raise ValueError("club page does not identify its crest")
        url=candidates[0]
        resp=get(url)
        if not resp.headers.get("content-type","").startswith("image/"):
            raise ValueError("source is not an image")
        img=Image.open(io.BytesIO(resp.content)).convert("RGBA")
        if img.width<35 or img.height<35 or img.width>5000 or img.height>5000:
            raise ValueError("source image has implausible dimensions")
        obj.update({"status":"source_identified","affiliation":aff,"source_image_url":url,
                    "source_sha256":hashlib.sha256(resp.content).hexdigest(),
                    "source_dimensions":[img.width,img.height]})
        return obj,img
    except Exception as exc:
        obj.update({"status":"unresolved","reason":str(exc)[:260]})
        return obj,None

def tint(img):
    # Extract an approximate dominant non-neutral tone from the genuine crest.
    sample=img.copy(); sample.thumbnail((96,96))
    colors=[]
    for r,g,b,a in sample.getdata():
        if a<90:continue
        spread=max(r,g,b)-min(r,g,b)
        if max(r,g,b)>235 and min(r,g,b)>225:continue
        if max(r,g,b)<50:continue
        if spread<32:continue
        colors.append((r//48,g//48,b//48))
    if not colors:return (65,75,91)
    tup=collections.Counter(colors).most_common(1)[0][0]
    r,g,b=[min(245,v*48+24) for v in tup]
    return (max(20,int(r*.78)),max(20,int(g*.78)),max(20,int(b*.78)))

def remove_white_border(img):
    """Only flood-remove nearly white edge pixels; keep white inside the crest."""
    im=img.convert("RGBA")
    w,h=im.size
    if w*h>1_200_000:
        im.thumbnail((1000,1000),Image.Resampling.LANCZOS)
        w,h=im.size
    px=im.load()
    if not any(px[x,y][0]>242 and px[x,y][1]>242 and px[x,y][2]>242 for x,y in
               ((0,0),(w-1,0),(0,h-1),(w-1,h-1))):
        return im
    dq=deque([(x,0) for x in range(w)]+[(x,h-1) for x in range(w)]+
             [(0,y) for y in range(h)]+[(w-1,y) for y in range(h)])
    visited=bytearray(w*h)
    while dq:
        x,y=dq.pop()
        k=y*w+x
        if visited[k]:continue
        visited[k]=1
        r,g,b,a=px[x,y]
        if min(r,g,b)<240 or max(r,g,b)-min(r,g,b)>20:continue
        px[x,y]=(r,g,b,0)
        if x>0:dq.append((x-1,y))
        if x+1<w:dq.append((x+1,y))
        if y>0:dq.append((x,y-1))
        if y+1<h:dq.append((x,y+1))
    return im

def format_png(original):
    img=remove_white_border(original)
    box=img.getbbox()
    if box:img=img.crop(box)
    bg=Image.new("RGB",(120,96),tint(original))
    img.thumbnail((99,81),Image.Resampling.LANCZOS)
    bg.paste(img,((120-img.width)//2,(96-img.height)//2),img)
    output=io.BytesIO(); bg.save(output,format="PNG",optimize=True)
    return output.getvalue()

def main():
    BASE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    tasks=[]
    for league in LEAGUES:
        try:tasks.extend(groups_for(league))
        except Exception as exc:print("GROUP_LIST_ERROR",league,exc,flush=True)
    print("GROUPS",len(tasks),flush=True)
    # Strictly do not process wrong season or missing groups.
    if len(tasks)!=24:raise SystemExit(f"expected 24 mainland groups, observed {len(tasks)}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        listings=list(pool.map(entries_for,tasks))
    entries=[v for group in listings for v in group]
    print("CLUBS",len(entries),flush=True)
    if len(entries)<280:raise SystemExit("too few clubs: likely source parsing error")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        assets=list(pool.map(source_for,entries))
    by_hash=collections.defaultdict(set)
    for e,img in assets:
        if img is not None: by_hash[e["source_sha256"]].add(e["affiliation"])
    manifest=[]
    for entry,img in assets:
        if img is not None and len(by_hash[entry["source_sha256"]])>1:
            entry["status"]="unresolved"
            entry["reason"]="identical logo image across distinct affiliations; possible placeholder"
        if img is not None and entry["status"]=="source_identified":
            fn=norm(entry["name"])+".png"
            path=OUT/fn
            if path.exists():
                entry["status"]="unresolved";entry["reason"]="nonunique normalized name, collision"
            else:
                path.write_bytes(format_png(img))
                entry["status"]="published_candidate"
                entry["target_path"]=str(path)
                entry["target_url"]=("https://raw.githubusercontent.com/"
                    "MMMMMMD31/mmd31-wavy-flags/mmd31-r1-standard-crests-audit-20261022/"+str(path))
                entry["image_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append(entry)
    result={"source":ROOT,"season":"2026-2027","method":"linked club page affiliation + linked crest; fail closed",
        "groups":len(tasks),"clubs":len(entries),
        "states":dict(collections.Counter(x["status"] for x in manifest)),
        "items":manifest}
    (BASE/"crest_manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Source-linked Regional 1 crests — research branch",
           "",f"- Groups: {len(tasks)}",f"- Clubs: {len(entries)}",
           f"- Status: {result['states']}",
           "- Club pages: TheFootData; images: identified by the club's 6–7 digit affiliation number.",
           "- Any ambiguous or missing crest is omitted, not replaced with another club's image.",
           "- Generated images: 120 × 96 standard PNG only (no victory flags).",
           "- **Verification pending:** inspect produced assets and manifest before JSON injection.",
           "- Brand marks remain property of their respective clubs; verify reuse permissions.",
           ""]
    (BASE/"crest_audit.md").write_text("\n".join(lines),encoding="utf-8")
    print(result["states"],flush=True)
if __name__=="__main__":main()
