#!/usr/bin/env python3
"""Only add sourced crests missing from MMD31 National 1/2 2026/27. Never modify established 114 pairs."""
import concurrent.futures, hashlib, io, json, math, re, unicodedata, time
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parent
AUDIT=json.loads((BASE/"crest-audit.json").read_text(encoding="utf-8"))
missing=[x for x in AUDIT["results"] if not x.get("source")]
assert len(missing)==46,(len(missing), "unexpected roster")
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (MMD31 sourced football club badges)"})
def norm(x):
 return re.sub("[^a-z0-9]+","-",unicodedata.normalize("NFKD",x).encode("ascii","ignore").decode().lower()).strip("-")
ALIASES={
 "US Pays du Valois":"Union Sportive du Pays du Valois",
 "Union Foot de Touraine":"UF Touraine",
 "AS Saint-Brieuc Ginglin-Cesson":"AS Ginglin Cesson",
 "C'Chartres Football":"C'Chartres Football",
 "ES Le Cannet Rocheville":"Entente Sportive Cannet Rocheville",
 "Olympique Alès":"Olympique Alès Cévennes",
 "FC Saint-Lô Manche":"FC Saint-Lô Manche",
 "Sologne Olympique Romorantin":"SO Romorantin",
 "FCM Aubervilliers":"FC Municipal Aubervilliers",
 "FC Balagne":"FC Balagne",
 "AS Saint-Ouen-l'Aumône":"AS Saint-Ouen-l'Aumône",
 "Jura Dolois Football":"Jura Dolois Football",
 "Racing Besançon":"Racing Besançon",
 "UF Mâcon 71":"UF Mâconnais",
 "Is-Selongey Foot":"Is-Selongey",
 "Montpellier Atlas Paillade":"Atlas Paillade",
 "Olympique Charleville Prix-les-Mézières":"Olympique Charleville Prix-les-Mézières",
 "Thonon Évian Grand Genève FC":"Thonon Évian FC",
 "US Mandelieu-la-Napoule":"US Mandelieu la Napoule"
}
MANUAL={
 "AS Steenvoorde":"https://www.europlan-online.de/files/ff324fe214ddc522518eaa60d6fc3221.png",
 "AS Saint-Brieuc Ginglin-Cesson":"https://media.letelegramme.fr/api/v1/images/view/687f83bd22f9a8f6230f2672/keep_ratio/687f83bd22f9a8f6230f2672.1",
 "ASPTT Caen Football":"https://d1yjjnpx0p53s8.cloudfront.net/styles/logo-original-577x577/s3/122018/asptt_caen_football.gif?g.wpIr0U0El0HHB_dFHLDON9.L2tGPtq=&itok=U0TfIdUX",
 "C'Chartres Football":"https://www.actufoot.com/assets/CChartresFootball-logo.png",
 "ES Le Cannet Rocheville":"https://r2.thesportsdb.com/images/media/team/badge/19u64p1731809606.png",
 "FC Saint-Lô Manche":"https://images.seeklogo.com/logo-png/62/1/fc-saint-lo-manche-logo-png_seeklogo-624112.png",
 "AS Saint-Ouen-l'Aumône":"https://www.logotypes101.com/logos/226/2BC72BE2CCD6C7D0053661B4BBA49165/as_saint-ouen-laumone.png",
 "FC Bourgoin-Jallieu":"https://images.seeklogo.com/logo-png/55/1/fc-bourgoin-jallieu-logo-png_seeklogo-557074.png",
 "Olympique Alès":"https://images.seeklogo.com/logo-png/55/1/olympique-ales-logo-png_seeklogo-559520.png",
}
# Individually matched, independently sourced football-club emblems (not placeholders).
MANUAL.update({
  "ASPTT Dijon": "https://www.fcsochaux.fr/upload/team_thumbnail/61e96b249ec80457990111.png",
  "Blois Foot 41": "https://images.seeklogo.com/logo-png/63/1/blois-football-41-logo-png_seeklogo-632055.png",
  "ES Fosséenne": "https://d1e67q5w736kt2.cloudfront.net/france/clubs/es-fosseenne.jpg",
  "ESA Linas-Montlhéry": "https://www.europlan-online.de/files/b3db7211bead9080bfe39d4394f8ad2f.png",
  "FC Espaly": "https://images.seeklogo.com/logo-png/67/1/football-club-espaly-logo-png_seeklogo-675565.png",
  "FC Rousset SVO": "https://www.liguesdefoot.fr/images/logo_du_club_de_football_fc-rousset-ste-vict_de_rousset.png",
  "FC Vesoul": "https://cdn.helloasso.com/img/logos/fc%20vesoul-6e18383c8c8048d2afb9a1a9018a023a.jpg",
  "IC Croix": "https://images.seeklogo.com/logo-png/61/1/iris-club-de-croix-logo-png_seeklogo-616640.png",
  "Is-Selongey Foot": "https://www.europlan-online.de/files/97b0dfffe64eee203dfe5c205a865cc5.png",
  "Montpellier Atlas Paillade": "https://www.liguesdefoot.fr/images/logo_du_club_de_football_mont-atlas-paillade_de_montpellier.png",
  "OC Cesson": "https://media.letelegramme.fr/api/v1/images/view/687f83c0884401ad430f5e78/keep_ratio/687f83c0884401ad430f5e78.1",
  "Olympique Charleville Prix-les-Mézières": "https://d1e67q5w736kt2.cloudfront.net/france/clubs/olympique-charleville-prix-ardenne-metropole.jpg",
  "Saint-Amand FC": "https://r2.thesportsdb.com/images/media/team/badge/uu3bm31763261283.png",
  "SC Berre": "https://img.besport.com/384/LIndyW7tJ1QEsNXY4kMKRxUFTnw",
  "SFC Neuilly-sur-Marne": "https://www.europlan-online.de/files/2f172445aed578db01f6b584e1ca5285a.png",
  "Sologne Olympique Romorantin": "https://commons.wikimedia.org/wiki/Special:FilePath/Logo_SF_Romorantin_2026.svg",
  "Stade Beaucairois": "https://www.ogol.com.br/img/logos/equipas/13173_imgbank_1763647995.png",
  "Torcy PVM US": "https://s1.static-footeo.com/1200/uploads/torcyfoot/logo__qfrrky.png",
  "UF Mâcon 71": "https://d1e67q5w736kt2.cloudfront.net/france/clubs/macon-71.jpg",
  "US Feurs": "https://www.liguesdefoot.fr/images/logo_du_club_de_football_us-feurs_de_feurs.png",
  "US Mandelieu-la-Napoule": "https://d1e67q5w736kt2.cloudfront.net/france/clubs/us-mandelieu-football.jpg"
})

INDEX={}
try:
 page=S.get("https://football-logos.cc/france/",timeout=26); page.raise_for_status()
 for a in BeautifulSoup(page.text,"html.parser").find_all("a",href=True):
  href=a["href"];text=a.get_text(" ",strip=True)
  if href.startswith("/france/") and len(text)>3:
   INDEX.setdefault(norm(text),[]).append((text,urljoin(page.url,href)))
except Exception as exc:print("index error:",str(exc))
def site_candidate(team):
 name=team["team"]
 opts=[name,ALIASES.get(name,name)]
 good=[]
 for alias in set(opts):
  good+=INDEX.get(norm(alias),[])
 # Site might show exact team name under different punctuation
 if not good:
  for key,pairs in INDEX.items():
   match=max(SequenceMatcher(None,key,norm(alias)).ratio() for alias in opts)
   if match>=0.97 and abs(len(key)-len(norm(name)))<=9:good+=pairs
 return sorted(set(good)),None
def load_image(url):
 try:
  r=S.get(url,timeout=20);r.raise_for_status()
  if len(r.content)>5_000_000 or len(r.content)<900:return None
  if "svg" in r.headers.get("Content-Type","").lower() or ".svg" in url.split("?")[0].lower():
   import cairosvg
   return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=r.content,output_width=400,output_height=400))).convert("RGBA")
  im=Image.open(io.BytesIO(r.content));im.load()
  if im.width<50 or im.height<50:return None
  return im.convert("RGBA")
 except Exception:return None
def fetch_site(team):
 candidates,_=site_candidate(team)
 for label,url in candidates:
  try:
   r=S.get(url,timeout=16);r.raise_for_status()
   soup=BeautifulSoup(r.text,"html.parser")
   tag=soup.find("meta",property="og:image")
   title=soup.find("h1")
   title=title.get_text(" ",strip=True) if title else ""
   if not tag or "logo" not in title.lower():continue
   source=tag.get("content")
   if "football-logos.cc/logos/france/" not in source:continue
   im=load_image(source)
   if im:return im,source,"football-logos.cc",label
  except Exception:continue
 return None,None,None,None
def sportsdb(team):
 target=ALIASES.get(team["team"],team["team"])
 for name in dict.fromkeys([team["team"],target]):
  try:
   res=S.get("https://www.thesportsdb.com/api/v1/json/3/searchteams.php",params={"t":name},timeout=10)
   for item in (res.json().get("teams") or []):
    title=item.get("strTeam") or ""
    if item.get("strSport","").lower()!="soccer":continue
    if max(SequenceMatcher(None,norm(title),norm(v)).ratio() for v in (name,target))<0.95:continue
    country=(item.get("strCountry") or "").lower()
    if country and country not in ("france","fr"):continue
    src=item.get("strBadge") or item.get("strTeamBadge")
    if src:
     img=load_image(src)
     if img:return img,src,"thesportsdb.com",title
  except Exception:continue
 return None,None,None,None
def dominant(img):
 im=img.copy();im.thumbnail((80,80))
 from collections import Counter
 cols=[(r//32,g//32,b//32) for r,g,b,a in im.getdata() if a>160 and not(r>225 and g>225 and b>225) and not(r<24 and g<24 and b<24)]
 if not cols:return (35,57,83)
 tup=Counter(cols).most_common(1)[0][0]
 return tuple(min(238,32*x+16) for x in tup)
def generate(team,img):
 slug=team["slug"];div=team["division"].lower()
 b=BASE/div
 p=b/"standard"/(slug+".png"); v=b/"victory"/(slug+".png")
 if p.exists() and v.exists():return True
 bg=Image.new("RGBA",(120,96),dominant(img)+(255,))
 ImageDraw.Draw(bg).rounded_rectangle((14,9,106,87),radius=11,fill=(255,255,255,32))
 im=img.copy(); im.thumbnail((79,74),Image.Resampling.LANCZOS)
 bg.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 p.parent.mkdir(parents=True,exist_ok=True);v.parent.mkdir(parents=True,exist_ok=True)
 bg.save(p,optimize=True)
 wave=Image.new("RGBA",(120,96),(0,0,0,0))
 wp=wave.load();bp=bg.load()
 for y in range(96):
  dx=3*math.sin(y*2*math.pi/73)
  for x in range(120):
   yy=int(y-2*math.sin(x*2*math.pi/81+y*math.pi/60))
   xx=int(x-dx)
   if 2<=xx<118 and 4<=yy<92:
    r,g,b,a=bp[xx,yy];f=1+.09*math.sin(x*math.pi/37+y/33)
    wp[x,y]=(min(255,int(r*f)),min(255,int(g*f)),min(255,int(b*f)),a)
 wave.save(v,optimize=True)
 return True

def apm_metz_logo():
 for page in ("https://scorenco.com/football/clubs/apm-metz-2qz4","https://www.sportcorico.com/clubs/am-du-personnel-municipal-metz-fc","https://apm-metz.footeo.com/"):
  try:
   r=S.get(page,timeout=13);r.raise_for_status()
   soup=BeautifulSoup(r.text,"html.parser")
   for tag in soup.find_all("img"):
    label=(tag.get("alt") or "").lower()
    if not any(x in label for x in ("apm","personnel municipal","logo du club")):continue
    u=tag.get("data-src") or tag.get("src")
    if not u:continue
    u=urljoin(page,u)
    if any(x in u.lower() for x in ("placeholder","default","grey","empty")):continue
    im=load_image(u)
    if im:return im,u,"verified-club-page",page
  except Exception:continue
 return None,None,None,None

# Source-page alternatives for the one remaining sports crest.
BERRE_DEBUG=[]
def berre_logo():
 base="LIndyW7tJ1QEsNXY4kMKRxUFTnw"
 candidates=[
  "https://img.besport.com/384/"+base,
  "https://wsrv.nl/?url=img.besport.com/384/"+base,
  "https://images.weserv.nl/?url=img.besport.com/384/"+base,
  "https://wsrv.nl/?url=https%3A%2F%2Fimg.besport.com%2F384%2F"+base,
  "https://img.besport.com/512/"+base,
  "https://img.besport.com/128/"+base
 ]
 for page in ["https://scorenco.com/football/clubs/berre-sporting-club-2inp",
              "https://www.sportcorico.com/clubs/berre-spc",
              "https://www.besport.com/group/19641"]:
  try:
   resp=S.get(page,timeout=15); resp.raise_for_status()
   soup=BeautifulSoup(resp.text,"html.parser")
   for imgtag in soup.find_all("img"):
    alt=(imgtag.get("alt") or "").lower()
    if "berre" not in alt:continue
    for key in ("data-src","src"):
     raw=imgtag.get(key)
     if not raw or raw.startswith("data:"):continue
     if any(word in raw.lower() for word in ("placeholder","default","blank","grey")):continue
     candidates.append(urljoin(page,raw))
   BERRE_DEBUG.append({"page":page,"status":resp.status_code,"candidate_count":len(candidates)})
  except Exception as ex:BERRE_DEBUG.append({"page":page,"error":str(ex)[:140]})
 for url in dict.fromkeys(candidates):
  try:
   resp=S.get(url,timeout=16)
   rec={"url":url[:200],"status":resp.status_code,"bytes":len(resp.content),
        "mime":resp.headers.get("Content-Type","")}
   BERRE_DEBUG.append(rec)
   if resp.status_code!=200 or len(resp.content)<900:continue
   pic=load_image(url)
   if pic:return pic,url,"verified_berre_club","Berre Sporting Club"
  except Exception as ex:BERRE_DEBUG.append({"url":url[:150],"error":str(ex)[:130]})
 return None,None,None,None

def process(t):
 im,source,origin,matched=fetch_site(t)
 if im is None and t['team']=='APM Metz': im,source,origin,matched=apm_metz_logo()
 if im is None and t["team"] in MANUAL:
  src=MANUAL[t["team"]];im=load_image(src)
  if im is not None:source,origin,matched=src,"curated_external",t["team"]
 if im is None: im,source,origin,matched=sportsdb(t)
 if im is None and t['team']=='SC Berre':im,source,origin,matched=berre_logo()
 if im is not None:
  try:
   generate(t,im)
   return dict(t,status="ADDED",source=source,provider=origin,matched=matched)
  except Exception as ex:
   return dict(t,status="ERROR_RENDER",error=str(ex))
 candidates,_=site_candidate(t)
 return dict(t,status="MISSING",candidates=[{"name":x,"link":y} for x,y in candidates])
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 for obj in pool.map(process,missing):results.append(obj)
report={"berre_debug":BERRE_DEBUG,"initial":len(missing),"added":sum(x["status"]=="ADDED" for x in results),"missing":sum(x["status"]=="MISSING" for x in results),"results":results,"catalogue_count":len(INDEX)}
(BASE/"crest-completion-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("COMPLETION",report["added"],"MISSING",report["missing"],"CATALOGUE",len(INDEX))
