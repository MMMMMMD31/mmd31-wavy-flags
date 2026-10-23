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
  r=S.get(url,params=params,timeout=6)
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
 # Only trust exact basename tied to an actual club (not decorative/stock website images).
 from urllib.parse import urljoin,unquote
 try:
  from bs4 import BeautifulSoup
  page=get("https://slfl.co.uk/clubs/")
  if not page:return None
  soup=BeautifulSoup(page.text,"html.parser")
  query=norm("Bonnyrigg Rose" if name=="Bonnyrigg Rose Athletic" else name)
  for im in soup.find_all("img"):
   for raw in (im.get("data-src"),im.get("src")):
    if not raw:continue
    u=urljoin("https://slfl.co.uk/",raw)
    if not urlparse(u).path.lower().endswith((".png",".webp",".svg")):continue
    stem=unquote(urlparse(u).path.split("/")[-1]).rsplit(".",1)[0]
    stem=re.sub(r"-\d+x\d+$","",stem)
    if norm(stem)==query:return (u,"Official SLFL website",name)
 except Exception:pass
 return None


# Transfermarkt club numeric IDs taken from their 2026/27 Highland League and Scottish League Two club pages.
CLUB_TM_IDS={
 "The Spartans":17602,
 "Formartine United":23613,
 "Fraserburgh":23616,
 "Banks O'Dee":25442,
 "Clachnacuddin":3459,
 "Strathspey Thistle":23620,
 "Forres Mechanics":3458,
 "Turriff United":23621,
 "Keith":16266,
 "Invergordon":57766,
 "Wick Academy":23337,
 "Rothes":23619,
}
def club_verified_tm_badge(name):
 clubid=CLUB_TM_IDS.get(name)
 if clubid is None:return None
 return ("https://tmssl.akamaized.net/images/wappen/head/"+str(clubid)+".png","Transfermarkt 2026/27 club ID "+str(clubid),name)

def club_logo_archive(name):
 # An individually titled page must identify exactly this club, and the source image must be a crest.
 try:
  from bs4 import BeautifulSoup
  from urllib.parse import urljoin
  slugged={"The Spartans":"the-spartans","University of Stirling":"stirling-university-fc","Bonnyrigg Rose Athletic":"bonnyrigg-rose-fc","Linlithgow Rose":"linlithgow-rose-fc"}.get(name,slug(name))
  url="https://football-logos.cc/scotland/"+slugged+"/"
  r=get(url)
  if not r:return None
  soup=BeautifulSoup(r.text,"html.parser")
  head=soup.find("h1")
  if head is None or not norm(head.get_text(" ",strip=True)).startswith(norm(name if name not in ("University of Stirling","Bonnyrigg Rose Athletic","Linlithgow Rose") else {"University of Stirling":"Stirling University FC","Bonnyrigg Rose Athletic":"Bonnyrigg Rose FC","Linlithgow Rose":"Linlithgow Rose FC"}[name])):return None
  urls=[]
  for img in soup.find_all("img"):
   alt=norm(img.get("alt",""))
   if norm(name) not in alt:continue
   for typ in ("src","data-src","srcset"):
    v=img.get(typ)
    if v:
     for seg in v.split(","):
      u=urljoin(url,seg.strip().split(" ")[0])
      if urlparse(u).path.lower().endswith((".png",".webp",".svg")):urls.append(u)
  for met in soup.find_all("meta"):
   if met.get("property")=="og:image":
    u=urljoin(url,met.get("content",""))
    if urlparse(u).path.lower().endswith((".png",".webp",".svg")):urls.append(u)
  if urls:
   urls.sort(key=lambda u: ("assets.football-logos.cc" not in u,"512" not in u and "256" not in u))
   return urls[0],"football-logos.cc (name exact)",name
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
 if url.startswith('slflpack://'):
  content=SLFL_ZIP_BYTES.get(url[len('slflpack://'):])
  if not content:return None
 else:
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

SLFL_ZIP_SOURCE="https://slfl.co.uk/wp-content/uploads/2026/06/SLFL-Badges-2026-27-2.zip"
SLFL_ZIP_BYTES={}
def load_official_slfl_zip():
 import zipfile
 try:
  r=S.get(SLFL_ZIP_SOURCE,timeout=45)
  if not r.ok:return {}
 except Exception:return {}
 if not r:return {}
 try:
  with zipfile.ZipFile(io.BytesIO(r.content)) as arc:
   paths=[p for p in arc.namelist() if p.lower().endswith((".png",".svg",".webp",".jpg",".jpeg")) and not p.endswith("/")]
   indexed={}
   for p in paths:
    base=p.split("/")[-1].rsplit(".",1)[0]
    normalized=norm(base)
    for suffix in ("badge","crest","logo","team"):
     if normalized.endswith(suffix):normalized=normalized[:-len(suffix)]
    # use club names exactly; do not accept broad substring matches
    if not normalized:continue
    SLFL_ZIP_BYTES[p]=arc.read(p)
    indexed.setdefault(normalized,("slflpack://"+p,"Official SLFL crest pack 2026-27",base))
   (ROOT/"scotland-2026-27-v13/slfl-archive-inventory.json").write_text(json.dumps({"source":SLFL_ZIP_SOURCE,"image_files":paths,"matched_basenames":list(indexed.keys())},ensure_ascii=False,indent=2))
   return indexed
 except Exception as e:
  (ROOT/"scotland-2026-27-v13/slfl-archive-inventory.json").write_text(json.dumps({"source":SLFL_ZIP_SOURCE,"error":str(e)},ensure_ascii=False,indent=2))
  return {}

rows=list(csv.DictReader(open(ROOT/"scotland-2026-27-v13/clubs.csv",encoding="utf-8")))
assert len(rows)==93

# Diagnostic metadata for the official Lowland League crest catalog, to improve exact identity matching.
try:
 from bs4 import BeautifulSoup
 directory=get("https://slfl.co.uk/clubs/")
 if directory:
  directory_soup=BeautifulSoup(directory.text,"html.parser")
  examples=[]
  for anchor in directory_soup.find_all("a",href=True):
   if "/clubs/" not in anchor["href"]:continue
   images=anchor.find_all("img")
   examples.append({"href":anchor["href"],"text":anchor.get_text(" ",strip=True)[:100],"images":[{"alt":v.get("alt"),"src":v.get("data-src") or v.get("src")} for v in images[:2]],"parent_text":anchor.parent.get_text(" ",strip=True)[:100] if anchor.parent else ""})
  (ROOT/"scotland-2026-27-v13/slfl-debug.json").write_text(json.dumps(examples[:100],ensure_ascii=False,indent=2))
except Exception:pass


# Alias verified against the official 2026/27 SLFL badge archive filenames.
SLFL_ARCHIVE_ALIASES={
 "Linlithgow Rose":"linlithgow",
 "Hill of Beath Hawthorn":"hillofbeathhawthorn-",
 "Broxburn Athletic":"broxburn",
 "Bo'ness United":"boness",
 "Musselburgh Athletic":"musselburgh",
 "University of Stirling":"stirling-uni-green",
 "Pollok":"pollokfc",
 "Johnstone Burgh":"johnstone-burgh-fc-",
 "Cumnock Juniors":"cumnock-juniors-fc-",
 "Cumbernauld Colts":"cumbernauld",
 "Newton Stewart":"newton-stewart-f-c-",
 "Bonnyrigg Rose Athletic":"bonnyrigg",
 "Caledonian Braves":"caledonianbraves",
 "Troon":"troon-fc-badge-latest",
 "Beith Juniors":"beith",
}

slflpack=load_official_slfl_zip()
logos=espn()
guardian=guardian_catalog()
prior={}
try:
 report=json.loads((ROOT/"scotland-2026-27-v13/badge-build-report.json").read_text())
 prior={str(z["id"]):z for z in report.get("records",[]) if z.get("dimensions_verified")}
except Exception:pass
statuses=[]
for i,row in enumerate(rows,1):
 name=row["club"];needle=ALIASES.get(name,name)
 candidates=[]
 slflkey=SLFL_ARCHIVE_ALIASES.get(name,norm(needle))
 if row['division'] in ('D3','D4','D5E','D5W') and slflkey in slflpack:candidates.append(slflpack[slflkey])
 if norm(needle) in logos:candidates.append(logos[norm(needle)])
 if norm(needle) in guardian:candidates.append(guardian[norm(needle)])
 tm_candidate=club_verified_tm_badge(name)
 if tm_candidate:candidates.append(tm_candidate)
 if not candidates:
  known_candidate=club_logo_archive(name)
  if known_candidate:candidates.append(known_candidate)
 status={"id":row["club_id"],"club":name,"division":row["division"],"state":"MISSING","source_url":"","source_provider":"","matched_name":"","file":"","dimensions_verified":False,"visual_identity_reviewed":False}
 for url,provider,matched in candidates:
  im=process(url)
  if im is None:continue
  output=ROOT/"docs"/"club-flags"/"scotland-2627"/row["division"].lower()/"standard"/(slug(name)+".png")
  output.parent.mkdir(parents=True,exist_ok=True)
  plate(im).save(output,"PNG")
  with Image.open(output) as check:assert check.size==(120,96) and check.format=="PNG"
  status.update({"state":"SOURCE_FOUND_VISUAL_REVIEW_PENDING","source_url":SLFL_ZIP_SOURCE+"#"+url[len("slflpack://"):] if url.startswith("slflpack://") else url,"source_provider":provider,"matched_name":matched,"file":str(output.relative_to(ROOT)),"dimensions_verified":True})
  break
 if not status["dimensions_verified"] and row["club_id"] in prior:
  old=prior[row["club_id"]]
  old_path=ROOT/old["file"]
  if old_path.is_file():
   try:
    with Image.open(old_path) as old_image:
     if old_image.size==(120,96) and old_image.format=="PNG":status=old
   except Exception:pass
 statuses.append(status)
 print(i,name,status["state"],flush=True)
out=ROOT/"scotland-2026-27-v13"/"badge-build-report.json"
out.write_text(json.dumps({"clubs":93,"generated":sum(z["dimensions_verified"] for z in statuses),"visually_confirmed":0,"status":"NEEDS_REVIEW_AND_URL_VERIFICATION","records":statuses},ensure_ascii=False,indent=2))
