#!/usr/bin/env python3
"""Publish the last seven official/authentic crests for CGE V7, 120x96."""
from pathlib import Path
from io import BytesIO
import csv,json
import requests
from PIL import Image, ImageStat

ROOT=Path("docs/cge-v7-authentic-badges-20261026")
SOURCES={
"1906251000034":("Ægir","https://aegirfc.is/wp-content/uploads/2023/10/cropped-aegir_logo_gult_original_transparent-1.png","#1D334C","Official Ægir club website"),
"1906251000036":("Grindavík","https://assets.football-logos.cc/logos/iceland/700x700/grindavik.7cf45aea.png","#E7EFF7","football-logos.cc Iceland team page"),
"1906251000037":("Grótta","https://assets.football-logos.cc/logos/iceland/700x700/grotta.c8c365d9.png","#E8F0FA","football-logos.cc Iceland team page"),
"1906251000040":("Leiknir Reykjavík","https://assets.football-logos.cc/logos/iceland/700x700/leiknir-reykjavik.f29c6a04.png","#E9F0FB","football-logos.cc Iceland team page"),
"1906251000041":("Njarðvík","https://umfn.is/wp-content/themes/umfn/assets/img/nvik_logo2.png","#E4F2E6","Official Njarðvík club website"),
"1906251000042":("Þróttur Reykjavík","https://trottur.is/wp-content/uploads/2020/06/trottur_logo.png","#E4EFF9","Official Þróttur FC website"),
"1906300001011":("Batyr","https://kpl.kz/wp-content/uploads/2022/04/batyr-150x150-1.webp","#E8EDF4","Kazakhstan football club profile"),
}
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (CGE football badge audit; private gameplay database)"})
rows=[]
for team_id,(club,url,bg,source) in SOURCES.items():
 dest=ROOT/(team_id+".png")
 if dest.exists():
  rows.append([team_id,club,"already_published",source,url]);continue
 try:
  r=S.get(url,timeout=35);r.raise_for_status()
  if len(r.content)>4_000_000:raise ValueError("too large")
  im=Image.open(BytesIO(r.content)).convert("RGBA")
  if min(im.size)<60:raise ValueError("too small")
  if max(ImageStat.Stat(im.convert("RGB")).stddev)<8:raise ValueError("not an emblem")
  im.thumbnail((108,86),Image.Resampling.LANCZOS)
  canvas=Image.new("RGBA",(120,96),bg)
  canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  canvas.convert("RGB").save(dest,"PNG",optimize=True)
  assert Image.open(dest).size==(120,96)
  rows.append([team_id,club,"source_verified",source,url])
  print("VERIFIED",club,url,flush=True)
 except Exception as e:
  rows.append([team_id,club,"FAILED",source,str(e)[:180]])
  print("ERROR",team_id,club,repr(e),flush=True)
with (ROOT/"final_seven_source_audit.csv").open("w",encoding="utf8",newline="") as f:
 w=csv.writer(f);w.writerow(["teamId","clubName","status","originalSource","sourceImageOrError"]);w.writerows(rows)
if len([x for x in rows if x[2]=="FAILED"]):
 raise RuntimeError("Some final club logos could not be retrieved. Already downloaded files can be retained by the retry.")
