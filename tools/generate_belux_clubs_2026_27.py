#!/usr/bin/env python3
"""MMD31 club crests for Belgian D1/D2 and full Luxembourg pyramid, 2026/27."""
import base64,zlib,json,io,re,unicodedata,time,hashlib
from collections import Counter,defaultdict
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import quote,urljoin
import requests,cairosvg
from bs4 import BeautifulSoup
from PIL import Image,ImageFilter
DATA="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"
clubs=[dict(id=a,name=b,group=c) for a,b,c in json.loads(zlib.decompress(base64.b64decode(DATA)))]
assert len(clubs)==133 and len({x['id'] for x in clubs})==133
ROOT=Path("docs/belgium-luxembourg-clubs-2026-27/v1")
ROOT.mkdir(parents=True,exist_ok=True)
s=requests.Session()
s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31ClubBadges/1.0; research/personal football game database)"})
def norm(n):
 n=unicodedata.normalize("NFKD",n.casefold())
 return "".join(ch for ch in n if ch.isalnum() and not unicodedata.combining(ch))
def simplified(n):
 n=norm(n)
 for x in ["fussballclub","footballclub","football","jeunesse","sporting","union","club","fc","us","as","cs","sc","es"]:
  if n.startswith(x) and len(n)>len(x)+5:n=n[len(x):]
 return n
def req(url):
 for attempt in range(3):
  try:
   r=s.get(url,timeout=24)
   r.raise_for_status()
   return r
  except Exception as e:
   if attempt==2:raise
   time.sleep(2+attempt)
repo={}
for country in ["belgium","luxembourg"]:
 url=f"https://api.github.com/repos/JoseArroyave/football-logos/contents/logos/{country}"
 arr=req(url).json()
 repo[country]=[(x["name"].removesuffix(".svg").replace("_"," "),x["download_url"]) for x in arr if x["name"].endswith(".svg")]
 print("REPO",country,len(repo[country]),flush=True)
# No club-badge substitutions from unrelated clubs.
explicit={
"Cercle Brugge":"Cercle Brugge KSV","OH Leuven":"Oud-Heverlee Leuven",
"RAAL La Louvière":"RAAL La Louvière","Royale Union Saint-Gilloise":"Union Saint-Gilloise",
"SK Beveren":"S.K. Beveren","Sporting Charleroi":"Royal Charleroi S.C.",
"KSC Lokeren":"KSC Lokeren-Temse","K. Beerschot VA":"Beerschot",
"SV Zulte Waregem":"Zulte Waregem",
"Club NXT":"Club Brugge","Jong Genk":"KRC Genk",
"Jong KAA Gent":"KAA Gent","RSCA Futures":"RSC Anderlecht",
"F91 Dudelange":"Diddeleng","CS Fola Esch-Alzette":"Fola",
"AS La Jeunesse d’Esch/Alzette":"Jeunesse Esch","Progrès Niederkorn":"Progrès",
"Racing FC Union Luxembourg":"Racing Union","UN Käerjeng 97":"Käerjéng",
"US Hostert":"Hostert","US Rumelange":"Rumelange",
"FC72 Erpeldange":"FC Erpeldange 72","Alisontia Steinsel":"FC Alisontia Steinsel",
"CS Grevenmacher":"Grevenmacher","FC Mondercange":"Mondercange",
"Swift Hesperange":"Swift Hesper",
"Koeppchen Wormeldange":"FC Koeppchen Wormeldange",
"FC Atert Bissen":"FC Atert Bissen","Avenir Beggen":"Avenir",
"Union Titus Pétange":"Union Titus Pétange",
"SC Bettembourg":"SC Bettembourg","FC Schifflange 95":"FC Schifflange 95",
}
def repo_match(club,country):
 lookup=explicit.get(club,club)
 hits=[v for n,v in repo[country] if norm(n)==norm(lookup)]
 if len(hits)==1:return hits[0]
 # Strict unique, almost exact: avoid crest from unrelated team
 ranked=sorted([(SequenceMatcher(None,norm(lookup),norm(n)).ratio(),n,v) for n,v in repo[country]],reverse=True)
 if ranked and ranked[0][0]>=.91 and (len(ranked)==1 or ranked[0][0]-ranked[1][0]>.07):
  print("FUZZY_REPO",club,ranked[0][:2],flush=True)
  return ranked[0][2]
 return None
PAGES={"l0":"10","lp":"11","l1a":"960","l1b":"961","l2a":"958","l2b":"959","l3":"962"}
flf=defaultdict(list)
diagnostics={}
for group,league in PAGES.items():
 url=f"https://www.flf.lu/tabellen-80253v4/leagues/{league}"
 try:
  html=req(url).text
  soup=BeautifulSoup(html,"html.parser")
  rows=soup.find_all("tr")
  found=[]
  for row in rows:
   img=row.find("img")
   if not img:continue
   src=img.get("src") or img.get("data-src") or img.get("srcset","").split(" ")[0]
   if not src:continue
   src=urljoin(url,src)
   label=row.get_text(" ",strip=True)
   if "images/teams" in src or "clubee" in src:
    found.append((label,src))
  if not found:
   for img in soup.find_all("img"):
    src=img.get("src") or img.get("data-src") or ""
    if "images/teams" not in src:continue
    parent=img
    for i in range(6):
     parent=parent.parent
     if parent is None:break
     label=parent.get_text(" ",strip=True)
     if len(label)>6:break
    found.append((label,urljoin(url,src)))
  flf[group]=list(dict.fromkeys(found))
  diagnostics[group]={"html_length":len(html),"tr_count":len(rows),"found_count":len(found),"sample":found[:2],"image_total":len(soup.find_all("img"))}
  print("FLF",group,diagnostics[group],flush=True)
 except Exception as e:
  diagnostics[group]={"error":str(e)}
  print("FLF ERROR",group,e,flush=True)
def flf_match(name,group):
 matches=flf[group]
 if not matches:return None,None
 target=norm(name);short=simplified(name)
 ranked=[]
 for label,url in matches:
  txt=norm(label)
  alts=[target,short]
  if target in txt or short in txt:
   score=1.0 if target in txt else .93
  else:
   tokens=[t for t in re.split(r"[^a-zA-ZÀ-ž0-9]+",name) if len(t)>3]
   hits=sum(norm(t) in txt for t in tokens)
   score=(hits/max(1,len(tokens)))*.75
  ranked.append((score,url,label))
 ranked.sort(reverse=True)
 if ranked[0][0]>=.75 and (len(ranked)==1 or ranked[0][0]>ranked[1][0]+.045):
  return ranked[0][1],ranked[0][2]
 return None,ranked[:2]
def crest_image(content):
 if content.lstrip()[:500].lower().find(b"<svg")>=0 or (b"<svg" in content[:3000]):
  content=cairosvg.svg2png(bytestring=content,output_width=520)
 im=Image.open(io.BytesIO(content)).convert("RGBA")
 bbox=im.getchannel("A").getbbox()
 if not bbox or bbox[2]-bbox[0]<4 or bbox[3]-bbox[1]<4:raise ValueError("blank/invalid badge")
 return im.crop(bbox)
def background_color(image):
 im=image.copy()
 im.thumbnail((96,96))
 colors=Counter()
 for r,g,b,a in im.getdata():
  if a<95:continue
  if max(r,g,b)-min(r,g,b)<36:continue
  if max(r,g,b)<45:continue
  key=(r//24,g//24,b//24)
  colors[key]+=a
 if colors:
  r,g,b=[min(255,x*24+12) for x in colors.most_common(1)[0][0]]
 else:r,g,b=55,88,135
 return tuple(int(.64*v+.36*255) for v in (r,g,b))
def render(crest):
 fill=background_color(crest)
 bg=Image.new("RGBA",(120,96),fill+(255,))
 crest.thumbnail((97,82),Image.Resampling.LANCZOS)
 x=(120-crest.width)//2;y=(96-crest.height)//2
 alpha=crest.getchannel("A")
 sh=Image.new("RGBA",crest.size,(0,0,0,0))
 sh.putalpha(alpha.filter(ImageFilter.GaussianBlur(.8)).point(lambda a:int(a*.28)))
 bg.alpha_composite(sh,(x+1,y+1))
 bg.alpha_composite(crest,(x,y))
 return bg.convert("RGB"),fill
status=[];rawhash={}
for club in clubs:
 country="belgium" if club["group"].startswith("b") else "luxembourg"
 source=repo_match(club["name"],country)
 source_type="github:J.A.football-logos" if source else None
 if not source and country=="luxembourg":
  source,match=flf_match(club["name"],club["group"])
  if source:source_type="flf.lu"
 row={**club,"status":"missing","source_url":source,"source_type":source_type}
 if not source:
  row["problem"]="No unique authentic crest source"
  status.append(row);continue
 try:
  content=req(source).content
  im=crest_image(content)
  # Track same crest sources (reserve teams deliberately share badge).
  img,fill=render(im)
  path=ROOT/(str(club["id"])+".png")
  img.save(path,optimize=True)
  assert Image.open(path).size==(120,96)
  row.update(status="ok",url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-crests-test-2026/{path.as_posix()}",background=fill,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 except Exception as e:row["problem"]=str(e)
 status.append(row)
 print("RESULT",club["id"],club["name"],row["status"],row.get("problem",""),flush=True)
report={"expected":133,"ok":sum(x["status"]=="ok" for x in status),"missing":sum(x["status"]!="ok" for x in status),"size":[120,96],"victoryFlags":0,"source_attribution":"Clubee/FLF official website and JoseArroyave football-logos","flf_page_diagnostics":diagnostics,"assets":status}
(ROOT/"status.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("FINAL",report["ok"],"/133 success; missing:",[x["name"] for x in status if x["status"]!="ok"],flush=True)
