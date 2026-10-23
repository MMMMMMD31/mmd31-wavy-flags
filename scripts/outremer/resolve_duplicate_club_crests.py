#!/usr/bin/env python3
"""Recover genuine crest for original club ID, not for unrelated similarly named team.
CS St Gilles and EF St Gilles are opponents; La Tamponnaise and ES Tamponnaise
have distinct FFF affiliations 581093 and 582172. Never merge team IDs.
"""
import csv,io,re,colorsys,collections
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image
ROOT=Path("flags/clubs/standard/outremer-2026-27")
QUAR=Path("audit/outremer-2026-27/quarantine")
LOG=Path("audit/outremer-2026-27/duplicate_club_resolution.csv")
ROOT.mkdir(parents=True,exist_ok=True)
checks=[
("1990262000053","La Tamponnaise","581093","restore_only","https://www.sportcorico.com/clubs/la-tamponnaise"),
("1990262000260","E.S. Tamponnaise","582172","try_unique_source","https://www.sportcorico.com/clubs/e-s-tamponnaise"),
("1990262000151","CS St Gilles","529455","restore_only","https://www.sportcorico.com/clubs/cs-st-gilles"),
("1990262000245","EF St Gilles","distinct_from_CS","try_unique_source","https://www.sportcorico.com/clubs/ecole-de-foot-st-gilles"),
]
results=[]
for tid,name,aff,action,page in checks:
 p=ROOT/(tid+".png")
 status="not_fixed";source=""
 if action=="restore_only":
  original=QUAR/(tid+".png")
  if original.exists() and original.stat().st_size>850:
   with Image.open(original) as img:
    if img.format!="PNG" or img.size!=(120,96):raise ValueError("not standard PNG")
   p.write_bytes(original.read_bytes())
   status="restored_original_verified_logo";source="prior independent club source"
 else:
  try:
   resp=requests.get(page,headers={"User-Agent":"Mozilla/5.0"},timeout=20);resp.raise_for_status()
   soup=BeautifulSoup(resp.text,"html.parser")
   title=soup.find("h1").get_text(" ",strip=True)
   expected="E.S. Tamponnaise" if tid=="1990262000260" else "Ecole de Foot St Gilles"
   def norm(s):return re.sub(r"[^a-z]+","",s.lower())
   if norm(title)!=norm(expected):raise ValueError("wrong club "+title)
   if "Réunion" not in soup.get_text(" ",strip=True):raise ValueError("wrong territory")
   urls=[]
   for im in soup.find_all("img"):
    alt=im.get("alt","")
    if re.match(r"^logo\s+",alt,re.I) and norm(re.sub(r"^logo\s+","",alt,flags=re.I))==norm(title):
     src=im.get("src") or im.get("data-src") or ""
     if src and "_nuxt/" not in src:urls.append(urljoin(resp.url,src))
   if len(urls)!=1:raise ValueError("no unique club badge")
   r=requests.get(urls[0],headers={"User-Agent":"Mozilla/5.0"},timeout=20);r.raise_for_status()
   image=Image.open(io.BytesIO(r.content)).convert("RGBA")
   image.thumbnail((102,84),Image.Resampling.LANCZOS)
   cols=collections.Counter()
   for R,G,B,A in image.getdata():
    if A<150:continue
    h,s,v=colorsys.rgb_to_hsv(R/255,G/255,B/255)
    if s>.25 and .15<v<.97:cols[(R//40,G//40,B//40)]+=1
   x=cols.most_common(1)[0][0] if cols else (5,5,5)
   bg=tuple(min(255,round((n*40+20)*.5+255*.5)) for n in x)
   result=Image.new("RGBA",(120,96),bg);result.alpha_composite(image,((120-image.width)//2,(96-image.height)//2))
   result.convert("RGB").save(p,format="PNG",optimize=True)
   status="new_unique_club_logo";source=urls[0]
  except Exception as e:status="pending_unique_logo:"+str(e)[:100]
 results.append(dict(team_id=tid,club=name,affiliation=aff,status=status,source=source,check_page=page))
with LOG.open("w",encoding="utf8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
print(results)
