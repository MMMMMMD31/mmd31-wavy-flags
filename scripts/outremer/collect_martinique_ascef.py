#!/usr/bin/env python3
"""Source-specific verified Martinique ASCEF crest. Never substitute for EER or Golden Lion."""
import io,csv,re,colorsys,collections
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image
TEAMID="1990262000204"
PAGE="https://www.sportcorico.com/clubs/sca-eudorcait-fourniols"
OUT=Path("flags/clubs/standard/outremer-2026-27/"+TEAMID+".png")
OUT.parent.mkdir(parents=True,exist_ok=True)
AUDIT=Path("audit/outremer-2026-27/martinique_last3_audit.csv")
AUDIT.parent.mkdir(parents=True,exist_ok=True)
HEAD={"User-Agent":"Mozilla/5.0"}
def fetch(url):
 r=requests.get(url,headers=HEAD,timeout=20);r.raise_for_status();return r
r=fetch(PAGE)
soup=BeautifulSoup(r.text,"html.parser")
title=soup.find("h1").get_text(" ",strip=True)
page=soup.get_text(" ",strip=True)
if "Eudorcait" not in title or "Martinique" not in page:raise ValueError("wrong club or territory")
matches=[]
for im in soup.select("img"):
 alt=im.get("alt","")
 if re.fullmatch(r"logo (?:S\.CA Eudorcait Fourniols|ASCEF)",alt,re.I):
  url=im.get("src") or im.get("data-src")
  if url and url.startswith("http") and "_nuxt/" not in url:matches.append(url)
if not matches:raise ValueError("Missing authentic club logo image")
source=matches[0]
raw=fetch(source).content
logo=Image.open(io.BytesIO(raw)).convert("RGBA")
if logo.width<35 or logo.height<35:raise ValueError("Image too small")
# Choose pale background with actual crest hue; do not invent logo.
counts=collections.Counter()
for R,G,B,A in logo.getdata():
 if A<180:continue
 h,s,v=colorsys.rgb_to_hsv(R/255,G/255,B/255)
 if s>=.3 and .17<v<.96:counts[(R//40,G//40,B//40)]+=1
if counts:
 tone=counts.most_common(1)[0][0]
 bg=tuple(min(255,round((t*40+20)*.55+255*.45)) for t in tone)
else:bg=(230,230,230)
logo.thumbnail((102,84),Image.Resampling.LANCZOS)
canvas=Image.new("RGBA",(120,96),bg)
canvas.alpha_composite(logo,((120-logo.width)//2,(96-logo.height)//2))
canvas.convert("RGB").save(OUT,format="PNG",optimize=True)
with AUDIT.open("w",newline="",encoding="utf8") as f:
 w=csv.DictWriter(f,fieldnames=["team_id","club","status","source_page","image_url","explanation"]);w.writeheader()
 w.writerow(dict(team_id=TEAMID,club="ASCEF / S.CA Eudorcait Fourniols",status="published",source_page=PAGE,image_url=source,explanation="Logo confirms club and Martinique; 120x96"))
 w.writerow(dict(team_id="1990262000029",club="Golden Lion FC",status="permission_needed",source_page="https://www.sportcorico.com/clubs/golden-lion-football",image_url="",explanation="Earlier explicit no-republication warning; no upload"))
 w.writerow(dict(team_id="1990262000121",club="Entente Etoile Riveraine",status="no_valid_independent_logo",source_page="",image_url="",explanation="2026 entente of two parent clubs; no verified shared crest"))
print("PUBLISHED",TEAMID,OUT,source)
