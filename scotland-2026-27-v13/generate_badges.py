import csv,io,json,re,unicodedata,time
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
S=requests.Session()
S.headers.update({"User-Agent":"MMD31-Scottish-Crests/1.0 (personal simulation / documented sourcing)"})
ALIASES={"Celtic B":"Celtic","The Spartans":"Spartans FC","Bonnyrigg Rose Athletic":"Bonnyrigg Rose","Banks O'Dee":"Banks o' Dee"}
def slug(name):
 t=unicodedata.normalize("NFKD",name).encode("ascii","ignore").decode().lower()
 return re.sub("[^a-z0-9]+","-",t).strip("-")
def norm(name):
 s=slug(name)
 for tail in ("-football-club","-fc","-f-c","-football"):
  if s.endswith(tail):s=s[:-len(tail)]
 return s.strip("-")
def get(url,params=None):
 try:
  r=S.get(url,params=params,timeout=17)
  return r if r.ok else None
 except Exception:return None
def espn():
 found={}
 for league in ("sco.1","sco.2","sco.3","sco.4"):
  r=get("https://site.web.api.espn.com/apis/site/v2/sports/soccer/"+league+"/teams?limit=500")
  if not r:continue
  try:
   for item in r.json()["sports"][0]["leagues"][0]["teams"]:
    t=item["team"]
    for name in (t.get("name"),t.get("displayName"),t.get("shortDisplayName")):
     if name and t.get("logos"):found[norm(name)]=(t["logos"][0]["href"],"ESPN",name)
  except Exception:pass
 return found
def sportsdb(name):
 r=get("https://www.thesportsdb.com/api/v1/json/123/searchteams.php",{"t":name})
 if not r:return None
 try:
  for t in r.json().get("teams") or []:
   if t.get("strSport")!="Soccer" or norm(t.get("strTeam",""))!=norm(name):continue
   if t.get("strCountry","").lower() not in ("scotland","united kingdom",""):continue
   u=t.get("strBadge")
   if u and u.startswith("https://"):return(u,"TheSportsDB",t["strTeam"])
 except Exception:pass
 return None

def guardian_catalog():
 raw=get("https://raw.githubusercontent.com/guardian/football-assets/main/source/crests/crests.json")
 if not raw:return {}
 try:
  entries=raw.json()["crests"]
  result={}
  for row in entries:
   name=row.get("team","")
   if not name:continue
   key=norm(name)
   url="https://raw.githubusercontent.com/guardian/football-assets/main/source/crests/"+row["filename"]
   result.setdefault(key,(url,"Guardian football-assets",name))
  return result
 except Exception:return {}


def lowland_club_logo(name):
 # Official Scottish Lowland Football League crest source. Use the team-specific official club page.
 from urllib.parse import urljoin, unquote
 from bs4 import BeautifulSoup
 query=norm(name)
 if name=="Bonnyrigg Rose Athletic":query=norm("Bonnyrigg Rose")
 page=get("https://slfl.co.uk/clubs/")
 if not page:return None
 try:
  soup=BeautifulSoup(page.text,"html.parser")
  for link in soup.find_all("a",href=True):
   href=link["href"]
   if "/clubs/" not in href or href.rstrip("/").endswith("/clubs"):continue
   linktext=link.get_text(" ",strip=True)
   if not norm(linktext).startswith(query):continue
   # Identity is verified by official team-specific club directory link and logo image.
   images=list(link.find_all("img"))
   for img in images:
    u=img.get("data-src") or img.get("src")
    if not u:continue
    u=urljoin("https://slfl.co.uk/",u)
    filename=slug(unquote(urlparse(u).path.split("/")[-1]).split(".")[0])
    if filename and (filename.startswith(query) or query.startswith(filename)):
     return (u,"Official Scottish Lowland Football League",linktext)
   # Some listings have the crest in the team page rather than inside its directory anchor.
   detail=get(urljoin("https://slfl.co.uk/",href))
   if not detail:continue
   bs=BeautifulSoup(detail.text,"html.parser")
   for img in bs.find_all("img"):
    u=img.get("data-src") or img.get("src")
    if not u:continue
    u=urljoin("https://slfl.co.uk/",u)
    fn=norm(unquote(urlparse(u).path.split("/")[-1]).split(".")[0])
    if fn and (fn==query or fn.startswith(query+"-crest") or fn.startswith(query+"-logo")):
     return (u,"Official Scottish Lowland Football League",linktext)
 except Exception:pass
 return None

def wikipedia(name):
 for title in (name+" F.C.",name+" football club"):
  r=get("https://en.wikipedia.org/w/api.php",{"action":"query","format":"json","generator":"search","gsrsearch":"intitle:"+title,"gsrlimit":5,"prop":"pageimages","piprop":"original"})
  if not r:continue
  try:
   pages=r.json().get("query",{}).get("pages",{}).values()
   for p in pages:
    page=p.get("title","");u=p.get("original",{}).get("source","")
    if not u:continue
    if not (norm(name) in norm(page) or norm(page) in norm(name)):continue
    filename=urlparse(u).path.lower()
    if any(token in filename for token in ("logo","badge","crest","fc.svg","fc.png","f.c.svg","f.c.png")) and filename.endswith((".svg",".png",".webp",".jpg",".jpeg")):return (u,"Wikipedia",page)
  except Exception:pass
 return None
def process(url):
 r=get(url)
 if not r:return None
 content=r.content
 if urlparse(url).path.lower().endswith(".svg") or b"<svg" in content[:512]:
  try:
   import cairosvg
   content=cairosvg.svg2png(bytestring=content,output_width=512,output_height=512)
  except Exception:return None
 try:
  im=Image.open(io.BytesIO(content)).convert("RGBA")
  if min(im.size)<60:return None
  return im
 except Exception:return None
def plate(crest):
 from collections import Counter
 rect=crest.getbbox()
 if rect:crest=crest.crop(rect)
 crest.thumbnail((84,76),Image.Resampling.LANCZOS)
 colors=[(r,g,b) for r,g,b,a in crest.getdata() if a>180 and 30<max(r,g,b)<245 and max(r,g,b)-min(r,g,b)>36]
 if colors:
  common=Counter(tuple(c//32 for c in color) for color in colors).most_common(1)[0][0]
  bg=tuple(min(235,int((c+0.5)*32)) for c in common)
 else:bg=(42,70,105)
 tile=Image.new("RGBA",(120,96),bg+(255,))
 tile.alpha_composite(crest,((120-crest.width)//2,(96-crest.height)//2))
 return tile.convert("RGB")
rows=list(csv.DictReader(open(ROOT/"scotland-2026-27-v13/clubs.csv",encoding="utf-8")))
assert len(rows)==93
logos=espn()
guardian=guardian_catalog()
statuses=[]
for i,row in enumerate(rows,1):
 name=row["club"];needle=ALIASES.get(name,name)
 candidates=[]
 if norm(needle) in logos:candidates.append(logos[norm(needle)])
 if norm(needle) in guardian:candidates.append(guardian[norm(needle)])
 for result in (lowland_club_logo(name) if row['division'] in ('D3','D4','D5E','D5W') else None,sportsdb(needle),wikipedia(needle)):
  if result:candidates.append(result)
 status={"id":row["club_id"],"club":name,"division":row["division"],"state":"MISSING","source_url":"","source_provider":"","matched_name":"","file":"","dimensions_verified":False,"visual_identity_reviewed":False}
 for url,provider,matched in candidates:
  im=process(url)
  if im is None:continue
  output=ROOT/"docs"/"club-flags"/"scotland-2627"/row["division"].lower()/"standard"/(slug(name)+".png")
  output.parent.mkdir(parents=True,exist_ok=True)
  plate(im).save(output,"PNG")
  with Image.open(output) as check:assert check.size==(120,96) and check.format=="PNG"
  status.update({"state":"SOURCE_FOUND_VISUAL_REVIEW_PENDING","source_url":url,"source_provider":provider,"matched_name":matched,"file":str(output.relative_to(ROOT)),"dimensions_verified":True})
  break
 statuses.append(status)
 print(i,name,status["state"],flush=True)
out=ROOT/"scotland-2026-27-v13"/"badge-build-report.json"
out.write_text(json.dumps({"clubs":93,"generated":sum(z["dimensions_verified"] for z in statuses),"visually_confirmed":0,"status":"NEEDS_REVIEW_AND_URL_VERIFICATION","records":statuses},ensure_ascii=False,indent=2))
