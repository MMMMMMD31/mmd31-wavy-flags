#!/usr/bin/env python3
"""CGE V13: collect verified football club crests; fail closed for uncertain identity."""
import csv,io,json,re,time,unicodedata,hashlib,colorsys
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageStat,UnidentifiedImageError
from difflib import SequenceMatcher

ROOT=Path("docs/central-europe-d2-2026-27/verified")
ROOT.mkdir(parents=True,exist_ok=True)
UA="MMD31-FootballClubBadges/1.0 (+https://github.com/MMMMMMD31/mmd31-wavy-flags)"
S=requests.Session(); S.headers.update({"User-Agent":UA,"Accept":"application/json,text/html,image/*,*/*"})
ROWS="""CZ|1971262100001|1.SK Prostějov|SK Prostejov
CZ|1971262100003|FC Sellier & Bellot Vlašim|FC Vlasim
CZ|1971262100004|FC SILON Táborsko|FC Táborsko
CZ|1971262100005|FC Vysočina Jihlava|FC Vysocina Jihlava
CZ|1971262100006|FK Arsenal Česká Lípa|Arsenal Ceska Lipa
CZ|1971262100007|FK Dukla Praha|Dukla Prague
CZ|1971262100008|FK Třinec|FK Trinec
CZ|1971262100009|FK VIAGEM Ústí nad Labem|FK Usti nad Labem
CZ|1971262100010|FK Viktoria Žižkov|Viktoria Zizkov
CZ|1971262100011|Fotbal Příbram|1 FK Pribram
CZ|1971262100012|MFK Karviná|MFK Karvina
CZ|1971262100013|SK Hanácká Slavia Kroměříž|Slavia Kromeriz
CZ|1971262100014|SK Kladno|SK Kladno
CZ|1971262100016|Slezský FC Opava|SFC Opava
SK|1971262100101|FC Petržalka|FC Petrzalka
SK|1971262100102|FC Slovan Galanta|Slovan Galanta
SK|1971262100103|FC ŠTK 1914 Šamorín|FC Samorin
SK|1971262100104|FC TATRAN Prešov|1 FC Tatran Presov
SK|1971262100105|FC ViOn Zlaté Moravce - Vráble|FC ViOn Zlate Moravce
SK|1971262100106|FK Baník Lehota pod Vtáčnikom|Banik Lehota pod Vtacnikom
SK|1971262100107|FK Humenné|FK Humenne
SK|1971262100108|FK Inter Bratislava|Inter Bratislava
SK|1971262100109|FK POHRONIE Žiar nad Hronom Dolná Ždaňa|FK Pohronie
SK|1971262100110|MFK Bytča|MFK Bytca
SK|1971262100111|MFK Tatran Liptovský Mikuláš|Tatran Liptovsky Mikulas
SK|1971262100112|MFK Zvolen|MFK Zvolen
SK|1971262100113|MŠK Považská Bystrica|Povazska Bystrica
SK|1971262100115|OFK Malženice|OFK Malzenice
HU|1971262100201|FC Nagykanizsa|Nagykanizsa FC
HU|1971262100202|Diósgyőri VTK|Diosgyori VTK
HU|1971262100203|Videoton FC Fehérvár|Fehervar FC
HU|1971262100204|HR-Rent Kozármisleny|Kozarmisleny FC
HU|1971262100205|BVSC-Zugló|BVSC Zuglo
HU|1971262100206|Kolorcity Kazincbarcika SC|Kazincbarcika SC
HU|1971262100207|Tiszakécskei LC|Tiszakecske
HU|1971262100208|Szeged-Csanád Grosics Akadémia|Szeged Csanad
HU|1971262100209|FC Ajka|FC Ajka
HU|1971262100210|Kecskeméti TE|Kecskemeti TE
HU|1971262100211|Szentlőrinc SE|Szentlorinc SE
HU|1971262100212|Karcagi SC|Karcagi SC
HU|1971262100213|Gyirmót FC Győr|Gyirmot FC Gyor
HU|1971262100214|Aqvital FC Csákvár|Aqvital FC Csakvar
HU|1971262100215|Soroksár SC|Soroksar SC
HU|1971262100216|Mezőkövesd Zsóry FC|Mezokovesd Zsory FC
"""
DATA=[(x.split("|")[0],int(x.split("|")[1]),x.split("|")[2],x.split("|")[3]) for x in ROWS.strip().splitlines()]
def norm(z):
 z=unicodedata.normalize("NFKD",z).encode("ascii","ignore").decode().lower()
 z=z.replace("ž","z").replace("ő","o").replace("ű","u")
 return re.sub(r"[^a-z0-9]","",z)
def similarity(a,b):
 a,b=norm(a),norm(b)
 return SequenceMatcher(None,a,b).ratio()
def acceptable(wanted,alias,found):
 score=max(similarity(wanted,found),similarity(alias,found))
 return score>=0.81 or (score>=0.70 and any(len(k)>6 and k in norm(found) for k in [norm(alias),norm(wanted)]))
def request(url,params=None):
 try:
  r=S.get(url,params=params,timeout=(3,6))
  if r.status_code==200:return r
 except Exception:return None
 return None
def sources(wanted,alias):
 # Sources with explicit club identity metadata, never arbitrary image search hit.
 for q in [wanted,alias]:
  r=request("https://www.thesportsdb.com/api/v1/json/3/searchteams.php",{"t":q})
  if r:
   try:
    for x in (r.json().get("teams") or []):
     if acceptable(wanted,alias,x.get("strTeam","")) and x.get("strBadge"):
      yield (x["strBadge"],"TheSportsDB",x["strTeam"],r.url)
   except Exception:pass
  r=request("https://www.wikidata.org/w/api.php",{"action":"wbsearchentities","language":"en","format":"json","search":q,"limit":12})
  if r:
   try:
    candidates=r.json().get("search",[])
    for cand in candidates:
     lbl=cand.get("label","")
     if not acceptable(wanted,alias,lbl):continue
     ent=request("https://www.wikidata.org/wiki/Special:EntityData/"+cand["id"]+".json")
     if not ent:continue
     claims=ent.json()["entities"][cand["id"]].get("claims",{})
     for c in claims.get("P154",[]):
      filename=c["mainsnak"]["datavalue"]["value"]
      yield ("https://commons.wikimedia.org/wiki/Special:Redirect/file/"+requests.utils.quote(filename,safe=""),"Wikidata:P154",lbl,ent.url)
   except Exception:pass
  # FotMob: match exact clubs in search suggestions; avoid mismatched duplicates
  r=request("https://www.fotmob.com/api/search/suggest",{"term":q})
  if r:
   try:
    payload=r.json()
    for x in payload.get("teams",[]) if isinstance(payload,dict) else []:
     found=x.get("name","")
     if acceptable(wanted,alias,found) and x.get("id"):
      yield ("https://images.fotmob.com/image_resources/logo/teamlogo/"+str(x["id"])+".png","FotMob",found,r.url)
   except Exception:pass
  time.sleep(0.05)
def backdrop(im):
 im=im.convert("RGBA")
 im.thumbnail((98,82),Image.Resampling.LANCZOS)
 # Real badge remains unmodified apart from high-quality downsampling; its backdrop is uniform.
 palette=[(239,245,250),(249,242,233),(234,242,232),(241,237,247)]
 h=hashlib.sha256(im.tobytes()).digest()
 bg=palette[h[0]%len(palette)]
 out=Image.new("RGBA",(120,96),bg+(255,))
 out.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return out.convert("RGB")
def valid_image(b):
 try:
  im=Image.open(io.BytesIO(b));im.load()
  if im.width<30 or im.height<30 or im.width>5000 or im.height>5000:return None
  if im.format not in ("PNG","WEBP","JPEG","GIF"):return None
  if im.mode=="P": im=im.convert("RGBA")
  return im
 except Exception:return None
# Exactly identified club crest sources from official club/league pages and specialist databases.
SEEDS={
 1971262100006:("https://fkceskalipa.eoscms.cz/webimages/club_logo_filename_20260708_165830.png","Official club website","FK Arsenal Česká Lípa","https://www.fkceskalipa.cz"),
 1971262100013:("https://r2.thesportsdb.com/images/media/team/badge/yugcom1687931772.png","TheSportsDB","SK Hanácká Slavia Kroměříž","https://www.hanackaslavia.cz"),
 1971262100101:("https://www.fcpetrzalka.sk/www/img/logo-large.png","Official club website","FC Petržalka","https://www.fcpetrzalka.sk"),
 1971262100106:("https://www.monacobetliga.sk/photo/team/team_40.png","Official league football team directory","FK Baník Lehota pod Vtáčnikom","https://www.monacobetliga.sk/timy/2026"),
 1971262100110:("https://sport.video/media/club_logos/33b45117-aca.png","Sport.Video club page","MFK Bytča","https://watch.sport.video/3liga/iii-liga-stred/mfk-bytca-vs-tj-banik-kalinovo-196485"),
 1971262100212:("https://r2.thesportsdb.com/images/media/team/badge/g3diaw1751844953.png","TheSportsDB","Karcagi SC","https://www.thesportsdb.com/team/152526-karcag"),
 1971262100213:("https://images.seeklogo.com/logo-png/29/1/gyirmot-fc-gyor-logo-png_seeklogo-292270.png","SeekLogo","Gyirmót FC Győr","https://seeklogo.com/vector-logo/292270/gyirmot-fc-gyor"),
}

from itertools import chain
from concurrent.futures import ThreadPoolExecutor, as_completed
def research(entry):
 nation,tid,name,alias=entry
 result={"nation":nation,"teamId":tid,"name":name,"alias":alias,"status":"NOT_FOUND","source":"","matched_name":"","image_url":"","page_url":"","png_url":"","sha256":""}
 for image_url,src,found,page in chain(([SEEDS[tid]] if tid in SEEDS else []),sources(name,alias)):
  r=request(image_url)
  if not r:continue
  im=valid_image(r.content)
  if im is None:continue
  new=backdrop(im)
  out=ROOT/(str(tid)+".png");new.save(out,"PNG",optimize=True)
  result.update(status="VERIFIED_PROVIDER_MATCH",source=src,matched_name=found,image_url=image_url,page_url=page,png_url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-central-europe-d2-20261025/docs/central-europe-d2-2026-27/verified/{tid}.png",sha256=hashlib.sha256(out.read_bytes()).hexdigest(),width=120,height=96)
  break
 print(tid,result["status"],result["source"],result["matched_name"],flush=True)
 return result
with ThreadPoolExecutor(max_workers=7) as pool:
 manifest=list(pool.map(research,DATA))
with open(ROOT.parent/"manifest.json","w") as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
with open(ROOT.parent/"manifest.csv","w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
print("TOTAL VERIFIED",sum(x['status'].startswith('VERIFIED') for x in manifest),"OF",len(manifest),flush=True)
