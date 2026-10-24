#!/usr/bin/env python3
"""Collect 2026-27 first-division badge images from 2026-updated club crest catalog.
Authenticity is visually subject to verification, all source URLs are recorded.
No fabricated badges or placeholders are used.
"""
import re,io,json,hashlib,collections
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps
from concurrent.futures import ThreadPoolExecutor
ROOT=Path("flags/clubs/standard/cge3-europe-2026-27")
LOGO=Path("flags/competition/cge3-europe-2026-27")
AUD=Path("audit/cge3-europe-2026-27")
for p in (ROOT,LOGO,AUD):p.mkdir(parents=True,exist_ok=True)
countries={
"CH":{"url":"https://escudosfc.com.br/swit.htm","clubs":[
("2026102401001","FC Basel 1893","Basel"),("2026102401002","Grasshopper Club Zürich","Grasshoper"),
("2026102401003","FC Lausanne-Sport","Lausanne"),("2026102401004","FC Lugano","Lugano"),
("2026102401005","FC Luzern","Luzern"),("2026102401006","Servette FC","Servette"),
("2026102401007","FC Sion","Sion"),("2026102401008","FC St.Gallen 1879","St. Gallen"),
("2026102401009","FC Thun","Thun"),("2026102401010","FC Vaduz","Vaduz"),
("2026102401011","BSC Young Boys","Young Boys"),("2026102401012","FC Zürich","Zurich")]},
"AT":{"url":"https://escudosfc.com.br/aut.htm","clubs":[
("2026102402001","SC Austria Lustenau","Austria Lustenau"),("2026102402002","FK Austria Wien","Austria Vienna"),
("2026102402003","Grazer AK 1902","Grazer"),("2026102402004","TSV Hartberg","Hartberg"),
("2026102402005","LASK","LASK Linz"),("2026102402006","SK Rapid Wien","Rapid Vienna"),
("2026102402007","FC Red Bull Salzburg","Red Bull Salzburg"),("2026102402008","SCR Altach","Rheindorf Altach"),
("2026102402009","SV Ried","Ried"),("2026102402010","SK Sturm Graz","Sturm Graz"),
("2026102402011","Wolfsberger AC","Wolfsberger"),("2026102402012","WSG Tirol","Swarovski Tirol")]},
"SM":{"url":"https://escudosfc.com.br/san_m.htm","clubs":[
("2026102403001","SP Cailungo","Cailungo"),("2026102403002","SS Cosmos","Cosmos"),
("2026102403003","FC Domagnano","Domagnano"),("2026102403004","SC Faetano","Faetano"),
("2026102403005","FC Fiorentino","Fiorentino"),("2026102403006","SS Folgore/Falciano","Folgore/Falciano"),
("2026102403007","AC Juvenes/Dogana","Juvenes Dogana"),("2026102403008","SP La Fiorita","La Fiorita"),
("2026102403009","AC Libertas","Libertas"),("2026102403010","SS Murata","Murata"),
("2026102403011","SS Pennarossa","Pennarossa"),("2026102403012","SS San Giovanni","San Giovanni"),
("2026102403013","San Marino Academy","San Marino Academy"),("2026102403014","SP Tre Fiori","Tre Fiori"),
("2026102403015","SP Tre Penne","Tre Penne"),("2026102403016","AC Virtus","Virtus")]}
}
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (MMD31 visual football club crest archive audit)"})
def get(url):
 r=session.get(url,timeout=32);r.raise_for_status()
 if len(r.content)>7_000_000:raise ValueError("oversized source")
 return r
def render(raw):
 im=Image.open(io.BytesIO(raw));im.load()
 im=im.convert("RGBA")
 if not (im.width>18 and im.height>18):raise ValueError("source smaller than 20 px")
 # Empty white corners in many older GIF / JPEG club crests.
 corners=[im.getpixel(pt) for pt in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]]
 white=sum(1 for r,g,b,a in corners if a>225 and r>242 and g>242 and b>242)
 if white>=3:
  p=list(im.getdata())
  new=[]
  for r,g,b,a in p:
   if min(r,g,b)>246 and max(r,g,b)-min(r,g,b)<10:new.append((r,g,b,0))
   else:new.append((r,g,b,a))
  im.putdata(new)
 bb=im.getchannel("A").getbbox()
 if bb:im=im.crop(bb)
 freq=collections.Counter()
 sm=im.copy();sm.thumbnail((80,80))
 for r,g,b,a in sm.getdata():
  if a>160 and max(r,g,b)-min(r,g,b)>35 and 20<max(r,g,b)<246:
   freq[(r//30,g//30,b//30)]+=1
 primary=freq.most_common(1)[0][0] if freq else (5,5,5)
 bg=tuple(int((x*30+15)*.45+255*.55) for x in primary)
 canvas=Image.new("RGBA",(120,96),bg+(255,))
 im.thumbnail((104,84),Image.Resampling.LANCZOS)
 canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 b=io.BytesIO();canvas.convert("RGB").save(b,format="PNG",optimize=True)
 return b.getvalue(),bg
results=[]
for nation,grp in countries.items():
 soup=BeautifulSoup(get(grp["url"]).content,"html.parser")
 imgs=[]
 for im in soup.find_all("img"):
  alt=(im.get("alt") or im.get("title") or "").strip()
  src=im.get("src") or im.get("data-src")
  if not src:continue
  imgs.append((alt,urljoin(grp["url"],src)))
 seen=set()
 for tid,name,match in grp["clubs"]:
  matches=[(alt,url) for alt,url in imgs if alt.strip().lower().lstrip().startswith(match.lower())]
  if not matches:matches=[(alt,url) for alt,url in imgs if match.lower() in alt.lower()]
  row={"team_id":tid,"country":nation,"club":name,"match_alt":match,"catalog":grp["url"],"status":"missing"}
  try:
   if not matches:raise ValueError("No image alt matching club")
   # Prefer first occurrence at top of page (division 1), reject generic graphic repeated for distinct clubs.
   alt,url=matches[0]
   raw=get(url).content
   png,bg=render(raw)
   assert len(png)>=500,("tiny image may be placeholder",tid)
   out=ROOT/(tid+".png")
   assert not out.exists(),tid
   out.write_bytes(png)
   row.update(status="published",source_alt=alt,source_url=url,bytes=len(png),
              sha256=hashlib.sha256(png).hexdigest(),background_rgb=bg)
   if row["sha256"] in seen:raise ValueError("Duplicate image SHA")
   seen.add(row["sha256"])
  except Exception as e:
   row["status"]="failed";row["error"]=str(e)[:180]
   (ROOT/(tid+".png")).unlink(missing_ok=True)
  results.append(row)
  print(nation,tid,name,row["status"],row.get("error",""),flush=True)
logos={
"CH":("https://origins-sportlab-payload-s3.origins-digital.com/sfl/images/RZ_SFL_Logo_Portrait_RGB%20-%20Copy.png","Swiss Football League"),
"AT":("https://europeanleagues.com/wp-content/uploads/2016/10/AUT_%C3%96FBL_H_RGB.png","Österreichische Fußball-Bundesliga"),
"SM":("https://www.sanmarinortv.sm/media/cache/fe_article_detail_full_big/uploads/img/photo/60/601d70601db68769895533.jpg","Federazione Sammarinese Giuoco Calcio")}
logo_results=[]
for code,(url,org) in logos.items():
 rec={"country":code,"organism":org,"source_url":url,"status":"missing"}
 try:
  r=get(url);im=Image.open(io.BytesIO(r.content));im.load();im=im.convert("RGBA")
  im.thumbnail((512,512),Image.Resampling.LANCZOS)
  p=LOGO/(code+"_federation.png")
  im.save(p,"PNG",optimize=True)
  rec.update(status="published",source_page={"CH":"https://sfl.ch","AT":"https://europeanleagues.com/member/osterreichische-fusball-bundesliga/","SM":"https://www.sanmarinortv.sm/sport/calcio-sammarinese-c15/nuovo-logo-per-la-federcalcio-di-san-marino-a200825"}[code],size=list(im.size),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 except Exception as e:rec["error"]=str(e)[:160]
 logo_results.append(rec)
AUD.joinpath("club_badge_manifest.json").write_text(json.dumps({"season":"2026-27","source":"2026-updated country logo catalogs","total":len(results),"published":sum(r["status"]=="published" for r in results),"entries":results},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
AUD.joinpath("federation_logo_manifest.json").write_text(json.dumps(logo_results,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("TOTAL",sum(r["status"]=="published" for r in results),"/40 CLUB BADGES",sum(r["status"]=="published" for r in logo_results),"/3 FEDERATIONS",flush=True)
