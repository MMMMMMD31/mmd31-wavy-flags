import requests,bs4,io,re,json,hashlib,unicodedata,concurrent.futures
from pathlib import Path
from PIL import Image
from urllib.parse import quote,urljoin
BASE=Path("docs/europe-d1-2026-27/v1");BASE.mkdir(parents=True,exist_ok=True)
rows=[
("MK","FK Shkëndija","Shkendija","KF_Shkëndija"),("MK","FC Struga Trim-Lum","Struga Trim Lum","FC_Struga"),("MK","FK Vardar","Vardar","FK_Vardar"),
("MK","GFK Tikveš","Tikves","GFK_Tikveš"),("MK","FK Sileks","Sileks","FK_Sileks"),("MK","KF Shkëndija Haraçinë 77","Shkendija Haracine","KF_Shkëndija_Haraçinë_77"),
("MK","FK Bregalnica Štip","Bregalnica Stip","FK_Bregalnica_Štip"),("MK","KF Arsimi 1973","KF Arsimi","KF_Arsimi"),("MK","KF Bashkimi 1947","FK Bashkimi Kumanovo","KF_Bashkimi"),("MK","FK Skopje","FK Skopje","FK_Skopje"),
("BG","PFC Levski Sofia","Levski Sofia","PFC_Levski_Sofia"),("BG","PFC CSKA Sofia","CSKA Sofia","PFC_CSKA_Sofia"),("BG","PFC Ludogorets Razgrad","Ludogorets Razgrad","PFC_Ludogorets_Razgrad"),("BG","FC CSKA 1948 Sofia","CSKA 1948 Sofia","FC_CSKA_1948_Sofia"),
("BG","PFC Botev Plovdiv","Botev Plovdiv","PFC_Botev_Plovdiv"),("BG","PFC Arda Kardzhali","Arda Kardzhali","FC_Arda_Kardzhali"),("BG","PFC Spartak Varna","Spartak Varna","FC_Spartak_Varna"),("BG","PFC Slavia Sofia","Slavia Sofia","PFC_Slavia_Sofia"),
("BG","POFC Botev Vratsa","Botev Vratsa","POFC_Botev_Vratsa"),("BG","PFC Lokomotiv Sofia 1929","Lokomotiv Sofia","PFC_Lokomotiv_Sofia"),("BG","FC Dunav Ruse","Dunav Ruse","FC_Dunav_Ruse"),("BG","PFC Lokomotiv Plovdiv","Lokomotiv Plovdiv","PFC_Lokomotiv_Plovdiv"),
("BG","PFC Septemvri Sofia","Septemvri Sofia","PFC_Septemvri_Sofia"),("BG","PFC Cherno More Varna","Cherno More Varna","PFC_Cherno_More_Varna"),
("RO","FC Dinamo București","Dinamo Bucuresti","FC_Dinamo_București"),("RO","FC Rapid București","Rapid Bucuresti","FC_Rapid_București"),("RO","CS Universitatea Craiova","Universitatea Craiova","CS_Universitatea_Craiova"),
("RO","FC Petrolul Ploiești","Petrolul Ploiesti","FC_Petrolul_Ploiești"),("RO","FC Universitatea Cluj","Universitatea Cluj","FC_Universitatea_Cluj"),("RO","FCSB","FCSB","FCSB"),
("RO","FC Farul Constanța","Farul Constanta","FC_Farul_Constanța"),("RO","CFR Cluj","CFR Cluj","CFR_Cluj"),("RO","CS Corvinul Hunedoara","Corvinul Hunedoara","FC_Corvinul_Hunedoara"),
("RO","FC UTA Arad","UTA Arad","FC_UTA_Arad"),("RO","FC Botoșani","FC Botosani","FC_Botoșani"),("RO","Sepsi OSK Sfântu Gheorghe","Sepsi OSK","Sepsi_OSK_Sfântu_Gheorghe"),
("RO","FC Argeș Pitești","FC Arges","FC_Argeș_Pitești"),("RO","ASC Oțelul Galați","Otelul Galati","ASC_Oțelul_Galați"),("RO","FC Voluntari","FC Voluntari","FC_Voluntari"),
("RO","FK Csíkszereda Miercurea Ciuc","Csikszereda","FK_Csíkszereda_Miercurea_Ciuc")]
federations=[
("MK","Football Federation of Macedonia","Football_Federation_of_Macedonia"),
("BG","Bulgarian Football Union","Bulgarian_Football_Union"),
("RO","Romanian Football Federation","Romanian_Football_Federation")]
def norm(x):return re.sub(r"[^a-z0-9]","",unicodedata.normalize("NFKD",x).encode("ascii","ignore").decode().lower())
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (MMD31 historical 2026 club logos)"})
def get(u):r=s.get(u,timeout=19);r.raise_for_status();return r
def sports(name,country):
 try:
  j=get("https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t="+quote(name)).json()
  a=j.get("teams") or []
  q=[x for x in a if ("football" in (x.get("strSport") or "").lower() or (x.get("strSport") or "").lower()=="soccer")]
  if len(q)>1:q=[x for x in q if country in str([x.get("strCountry"),x.get("strLeague")]).upper()] or q
  exact=[x for x in q if norm(x.get("strTeam") or "")==norm(name)]
  if len(exact)==1:q=exact
  if len(q)==1 and q[0].get("strBadge"):
   return q[0]["strBadge"],{"provider":"TheSportsDB","matched":q[0].get("strTeam"),"country":q[0].get("strCountry"),"source":"https://www.thesportsdb.com"}
 except Exception:pass
 return None,None
def wikipedia(page):
 for lang in ("en","ro","bg","mk"):
  try:
   url=f"https://{lang}.wikipedia.org/wiki/"+quote(page)
   r=get(url)
   doc=bs4.BeautifulSoup(r.text,"html.parser")
   inf=doc.select_one("table.infobox")
   if not inf:continue
   imgs=inf.select("img")
   for im in imgs[:6]:
    alt=(im.get("alt") or "").lower();src=im.get("src") or im.get("data-src") or ""
    if any(w in alt for w in ("kit","shirt","home","away")):continue
    if src and (".svg" in src or ".png" in src or ".jpg" in src):
     if src.startswith("//"):src="https:"+src
     elif src.startswith("/"):src=urljoin(url,src)
     return src,{"provider":f"Wikipedia infobox ({lang})","sourcePage":url,"alt":alt}
  except Exception:pass
 return None,None
def acquire(pair,i):
 c,name,search,page=pair;id={"MK":1900264000000,"BG":1900264100000,"RO":1900264200000}[c] + 1+sum(x[0]==c for x in rows[:i])
 rec={"id":id,"country":c,"name":name,"status":"NO_CREST_FOUND","candidate":search}
 prospects=[]
 for q in [search,name]:
  url,meta=sports(q,c)
  if url:prospects.append((url,meta))
 url,meta=wikipedia(page)
 if url:prospects.append((url,meta))
 # Two separately verified Macedonian club crests; never confuse Tetovo and Haraçinë.
 if id==1900264000006:
  prospects.append(("https://r2.thesportsdb.com/images/media/team/badge/lec0bk1779941482.png",{"provider":"TheSportsDB club 155729, Shkëndija Haraçinë 1977","sourcePage":"https://www.thesportsdb.com/team/155729-shk%C3%ABndija-hara%C3%A7in%C3%AB"}))
 if id==1900264000009:
  prospects.append(("https://images.seeklogo.com/logo-png/62/1/fc-bashkimi-kumanovo-logo-png_seeklogo-626423.png",{"provider":"Seeklogo FC Bashkimi Kumanovë 1947","sourcePage":"https://seeklogo.com/vector-logo/626423/fc-bashkimi-kumanovo"}))
 for url,meta in prospects:
  try:
   r=get(url)
   image=Image.open(io.BytesIO(r.content));image.load()
   assert image.width>=48 and image.height>=48
   assert len(r.content)<8000000
   image=image.convert("RGBA")
   bounds=image.getchannel("A").getbbox()
   if bounds:image=image.crop(bounds)
   # Original club crest, centered without changing the drawing
   image.thumbnail((104,84),Image.Resampling.LANCZOS)
   bg=(225,232,240) if c=="MK" else ((239,226,225) if c=="BG" else (236,229,211))
   canvas=Image.new("RGBA",(120,96),bg+(255,))
   canvas.alpha_composite(image,((120-image.width)//2,(96-image.height)//2))
   fn=BASE/(str(id)+".png");canvas.convert("RGB").save(fn,format="PNG",optimize=True)
   with Image.open(fn) as check:assert check.size==(120,96) and check.format=="PNG"
   rec.update({"status":"SOURCE_IDENTIFIED","url":url,"provider":meta,"sha256":hashlib.sha256(fn.read_bytes()).hexdigest(),"dimensions":[120,96],"output":str(fn)})
   break
  except Exception as e:rec["last_error"]=str(e)[:160]
 return rec
def acquire_federation(group):
 c,name,page=group
 rec={"country":c,"organizer":name,"status":"NO_LOGO_FOUND"}
 # Use explicitly identified federation page logo, not commercial league sponsor.
 url,meta=wikipedia(page)
 if not url:url,meta=sports(name,c)
 if url:
  try:
   r=get(url);im=Image.open(io.BytesIO(r.content));im.load();im=im.convert("RGBA")
   assert im.width>=45 and im.height>=45
   im.thumbnail((450,450),Image.Resampling.LANCZOS)
   bg=Image.new("RGBA",(512,512),(255,255,255,255))
   bg.alpha_composite(im,((512-im.width)//2,(512-im.height)//2))
   fn=BASE/(f"federation_{c}.png");bg.convert("RGB").save(fn,optimize=True)
   rec.update({"status":"SOURCE_IDENTIFIED","sourceImage":url,"provider":meta,"sha256":hashlib.sha256(fn.read_bytes()).hexdigest(),"output":str(fn),"dimensions":[512,512]})
  except Exception as e:rec["error"]=str(e)[:160]
 return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
 assets=list(pool.map(lambda x:acquire(x[1],x[0]),enumerate(rows)))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 logs=list(pool.map(acquire_federation,federations))
manifest={"date":"2026-10-24","base":"MMD31 Club Badges 2026/27","crests":assets,"federationLogos":logs,"status":"DOWNLOADS_CHECKED_BYTES_NOT_MANUAL_VISUAL_AUTHENTICATION"}
(BASE/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print("CRESTS",sum(x["status"]=="SOURCE_IDENTIFIED" for x in assets),"/",len(assets))
print("MISSING",[(x["id"],x["name"]) for x in assets if x["status"]!="SOURCE_IDENTIFIED"])
print("FEDERATIONS",logs)
