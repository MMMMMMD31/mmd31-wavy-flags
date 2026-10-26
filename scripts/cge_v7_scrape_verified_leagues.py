#!/usr/bin/env python3
"""CGE V7: fetch published club crests strictly by league participant name and country.
No placeholder logo, no initials, and no fuzzy cross-team assignment.
"""
import csv,io,os,re,json,time,unicodedata
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageStat,ImageOps

ROOT=Path("docs/cge-v7-authentic-badges-20261026")
ROOT.mkdir(parents=True,exist_ok=True)
TARGETS=ROOT/"targets.csv"
REPORT=ROOT/"sportsdb_league_source_audit.csv"
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"Mozilla/5.0 (compatible; CGE/1.0; badge-source-audit)","Accept":"text/html,image/avif,image/webp,image/apng,*/*"})
LEAGUES=[
("Armenia","https://api.thesportsdb.com/season/4908-armenian-first-league/2026-2027"),
("Azerbaijan","https://api.thesportsdb.com/season/4914-azerbaijan-first-division/2026-2027"),
("Czech Republic","https://api.thesportsdb.com/season/5878-czech-bohemian-football-league-group-a/2026-2027"),
("Czech Republic","https://api.thesportsdb.com/season/5879-czech-bohemian-football-league-group-b/2026-2027"),
("Czech Republic","https://api.thesportsdb.com/season/5880-czech-moravian-silesian-football-league/2026-2027"),
("Faroe Islands","https://api.thesportsdb.com/season/4961-faroe-islands-1.-deild/2026"),
("Norway","https://api.thesportsdb.com/season/5758-norwegian-second-division-group-1/2026"),
("Norway","https://api.thesportsdb.com/season/5759-norwegian-second-division-group-2/2026"),
("Poland","https://api.thesportsdb.com/season/5709-polish-ii-liga/2026-2027"),
("Israel","https://api.thesportsdb.com/season/4966-israeli-liga-leumit/2026-2027"),
]
ALIASES={
"FK Admira Praha":["Admira Praha"],
"SK Aritma Praha":["Aritma Praha"],
"FK Benešov":["Benešov"],
"Povltavská FA":["Povltavská fotbalová akademie","Povltavská FA"],
"SK Zápy":["Zápy"],
"SK Benátky nad Jizerou":["Benátky nad Jizerou"],
"FK Baník Most-Souš":["Baník Most-Souš"],
"FK Čáslav":["Čáslav"],
"FK Horní Ředice":["Horní Ředice"],
"FK Neratovice-Byškovice":["Neratovice-Byškovice"],
"SK Sokol Brozany":["Sokol Brozany"],
"FK Velké Hamry":["Velké Hamry"],
"FC Vsetín":["Vsetín"],
"FK Blansko":["Blansko"],
"FK Hodonín":["Hodonín"],
"FK SK Polanka":["Polanka nad Odrou"],
"MFK Havířov":["Havířov"],
"MFK Vítkovice":["Vitkovice"],
"SFK Vrchovina":["Vrchovina"],
"SK Hranice":["Hranice"],
"TJ Unie Hlubina":["Unie Hlubina"],
"ČSK Uherský Brod":["Uherský Brod"],
"FC Hoyvík":["Hoyvík"],
"FC Suðuroy":["Suðuroy"],
"ÍF Fuglafjørður":["ÍF Fuglafjørður"],
"TB Tvøroyri":["TB Tvøroyri"],
"F.C. Kiryat Yam":["Hapoel Kiryat Yam"],
"FK Hodo":["Hodonín"],
}
PRE= {"fc","fk","sk","mfk","sfk","tj","csk","if","umf","ks","mks","f","c"}

def norm(x):
 x=unicodedata.normalize("NFKD",(x or "").casefold())
 x="".join(ch for ch in x if not unicodedata.combining(ch))
 x=x.translate(str.maketrans({"ł":"l","ø":"o","ð":"d","þ":"th","æ":"ae","ı":"i"}))
 return " ".join(re.findall(r"[a-z0-9]+",x))

def stripped(x):
 w=norm(x).split()
 while w and w[0] in PRE: w.pop(0)
 return " ".join(w)

def matches(team,source):
 candidates=[team]+ALIASES.get(team,[])
 normalized_source=norm(source)
 stripped_source=stripped(source)
 for cand in candidates:
  if normalized_source==norm(cand):return True
  if stripped_source and len(stripped_source)>3 and stripped(cand)==stripped_source:return True
 return False

def get(url):
 r=SESSION.get(url,timeout=42);r.raise_for_status();return r

def search_season(country,url):
 try:
  soup=BeautifulSoup(get(url).text,"html.parser")
 except Exception as e:
  print("LEAGUE_ERR",country,url,repr(e),flush=True)
  return {},str(e)
 out={}
 # Layout: img.team-badge/tiny followed by sibling a: name of participant.
 for img in soup.select('img[src*="/images/media/team/badge/"]'):
  a=img.find_next_sibling("a")
  if not a:continue
  href=a.get("href","")
  if "/season/" not in href or "&t=" not in href:continue
  label=a.get_text(" ",strip=True)
  raw=img.get("src","")
  if not raw.startswith("https://"):continue
  url_full=raw.removesuffix("/tiny").removesuffix("/medium").removesuffix("/small")
  # The season is reliable ground truth for participant country.
  out.setdefault(norm(label),[]).append((label,url_full,url))
 print("PAGE",country,len(out),url,flush=True)
 return out,None

def crest_img(source_url):
 r=get(source_url)
 if len(r.content)>3_000_000:raise ValueError("oversized crest")
 img=Image.open(io.BytesIO(r.content)).convert("RGBA")
 if min(img.size)<80:raise ValueError(f"crest too small: {img.size}")
 # Avoid transparent spacer badges.
 extrema=ImageStat.Stat(img.convert("RGB")).stddev
 if max(extrema)<8:raise ValueError("image nearly solid; probably placeholder")
 return img

def preprocess(img,src_path):
 img.thumbnail((106,84),Image.Resampling.LANCZOS)
 # Keep original logo intact, including white detail; a neutral slightly tinted
 # background contrasts with most badges and helps dark edges remain distinct.
 bg=(226,233,243,255)
 dst=Image.new("RGBA",(120,96),bg)
 dst.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
 dst.convert("RGB").save(src_path,format="PNG",optimize=True)
 check=Image.open(src_path)
 assert check.size==(120,96)

def main():
 pages={}
 for country,url in LEAGUES:
  row,err=search_season(country,url)
  if err:continue
  pages.setdefault(country,{}).update(row)
  time.sleep(.13)
 targets=list(csv.DictReader(TARGETS.open(encoding="utf8")))
 audit=[]
 for target in targets:
  id_,name,country=target["teamId"],target["clubName"],target["country"]
  output=ROOT/(id_+".png")
  if output.exists():
   audit.append([id_,name,country,"already_published","","",""])
   continue
  candidates=[]
  for _,xs in pages.get(country,{}).items():
   for label,source,season in xs:
    if matches(name,label):
     candidates.append((label,source,season))
  candidates=list(dict.fromkeys(candidates))
  if len(candidates)!=1:
   audit.append([id_,name,country,"ambiguous" if candidates else "not_found","","",str(len(candidates))])
   continue
  label,source,season=candidates[0]
  try:
   im=crest_img(source)
   preprocess(im,output)
   audit.append([id_,name,country,"source_verified",label,source,season])
   print("SUCCESS",name,source,flush=True)
  except Exception as e:
   print("FAIL_DOWNLOAD",name,str(e)[:170],flush=True)
   audit.append([id_,name,country,"download_failed",label,source,str(e)[:170]])
  time.sleep(.16)
 with REPORT.open("w",newline="",encoding="utf8") as f:
  w=csv.writer(f);w.writerow(["teamId","clubName","country","status","matchedParticipant","sourceImage","sourceLeagueOrError"]);w.writerows(audit)
 print("AUDIT",json.dumps(dict(Counter(r[3] for r in audit))),flush=True)
 if len(audit)!=79:
  raise ValueError("Expected 78 missing clubs plus Hellas; got "+str(len(audit)))

if __name__=="__main__":main()
