#!/usr/bin/env python3
"""Converts manually checked club crest sources to 120x96 PNG, no invented graphics.
Runs only for the curated source list. Review licensing/trademarks before redistribution.
"""
import csv
import io
import os
import re
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
CLUBS=[
 (1990262000028,"C. Franciscain","https://club-franciscain.footeo.com/actualite.html","#338657"),
 (1990262000032,"C. Colonial","https://club-colonial.footeo.com/page/histoire-palmares.html","#4B4B4B"),
 (1990262000054,"As Excelsior","https://fr.wikipedia.org/wiki/Association_sportive_Excelsior_(Saint-Joseph)","#F2992E"),
 (1990262000061,"A.S. Jeanne D'Arc","https://www.besoccer.com/team/ss-la-jeanne-darc","#D8CAEF"),
 (1990262000317,"AS Magenta","https://asmagentafootball.footeo.com/","#C49A6C"),
 (1990262000319,"Tiga Sports","https://tigasport.footeo.com/","#F6D3D8"),
 (1990262000321,"Hienghène Sport","https://hienghene-sport.footeo.com/","#69C5DE"),
]
DIR=Path("flags/clubs/standard/outremer-2026-27"); DIR.mkdir(parents=True,exist_ok=True)
def fetch(url):
    resp=requests.get(url,timeout=25,headers={"User-Agent":"Mozilla/5.0 (compatible; MMD31LogoVerification/1.0)"})
    resp.raise_for_status()
    return resp.content
def get_url(page):
    soup=BeautifulSoup(fetch(page),"html.parser")
    def img_url(tag):
        for key in ("data-src","data-original","data-lazy-src","src"):
            val=tag.get(key)
            if val and not val.startswith("data:"):
                return urljoin(page,val)
        return None
    names=[]
    for img in soup.find_all("img"):
        alt=img.get("alt","").strip()
        if re.search(r"logo du club|logo du as excelsior|^logo |^logo$",alt,re.I):
            link=img_url(img)
            if link:
                names.append((alt,link))
    if not names: raise ValueError("No logo image with a descriptive alt attribute")
    if any("_nuxt/" in u for _,u in names):
        names=[(n,u) for n,u in names if "_nuxt/" not in u]
    if not names: raise ValueError("Generic platform logo only, not club logo")
    return names[0][1]
results=[]
for cid,name,source,bg in CLUBS:
    try:
        asset_url = ("https://cdn.resfu.com/img_data/equipos/61880.png" if cid==1990262000061 else get_url(source))
        raw=fetch(asset_url)
        im=Image.open(io.BytesIO(raw))
        im.verify()
        logo=Image.open(io.BytesIO(raw)).convert("RGBA")
        if logo.width<25 or logo.height<25:
            raise ValueError("Source logo below 25 px")
        logo.thumbnail((102,84),Image.Resampling.LANCZOS)
        canvas=Image.new("RGBA",(120,96),bg)
        canvas.alpha_composite(logo,((120-logo.width)//2,(96-logo.height)//2))
        output=DIR/(str(cid)+".png")
        canvas.convert("RGB").save(output,format="PNG",optimize=True)
        if Image.open(output).size!=(120,96): raise ValueError("PNG wrong dimensions")
        print("OK",cid,name,asset_url,output)
        results.append(dict(id=cid,club=name,source_page=source,image_url=asset_url,status="ready",file=str(output)))
    except Exception as exc:
        print("ERROR",cid,name,str(exc))
        results.append(dict(id=cid,club=name,source_page=source,image_url="",status="failed: "+str(exc),file=""))
with open(DIR/"manifest.csv","w",encoding="utf-8",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=["id","club","source_page","image_url","status","file"])
    writer.writeheader(); writer.writerows(results)
success=sum(1 for r in results if r["status"]=="ready")
print("TOTAL",success,"/",len(CLUBS))
if not success:
    raise SystemExit("No published crest")
