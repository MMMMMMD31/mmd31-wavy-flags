import requests,bs4,io,re,json,hashlib,unicodedata,concurrent.futures
from pathlib import Path
from PIL import Image
from urllib.parse import quote,urljoin
BASE=Path("docs/europe-d2-cups-2026-27/v1");BASE.mkdir(parents=True,exist_ok=True)
rows=[["MK","FK Belasica Strumica","Belasica Strumica","FK_Belasica"],["MK","FC AP Brera Strumica","Brera Strumica","FC_Akademija_Pandev"],["MK","FK Detonit Plachkovica","Detonit Plachkovica","FK_Detonit_Plachkovica"],["MK","KF Kamjani","Kamjani","KF_Kamjani"],["MK","FK Kozhuf Gevgelija","Kozhuf Gevgelija","FK_Kožuf"],["MK","FK Euromilk Gorno Lisiche","Euromilk","FK_Euromilk_Gorno_Lisiche"],["MK","FK Makedonija Gjorče Petrov","Makedonija GP","FK_Makedonija_Gjorče_Petrov"],["MK","FK Novaci","Novaci","FK_Novaci"],["MK","FK Ohrid Lychnidos","Ohrid Lychnidos","FK_Ohrid"],["MK","FK Osogovo Kočani","Osogovo Kocani","FK_Osogovo"],["MK","FK Pelister Bitola","Pelister Bitola","FK_Pelister"],["MK","FK Rabotnički Skopje","Rabotnicki Skopje","FK_Rabotnički"],["MK","KF Shkupi","Shkupi","KF_Shkupi"],["MK","FK Teteks Tetovo","Teteks Tetovo","FK_Teteks"],["BG","PFC CSKA Sofia II","CSKA Sofia","PFC_CSKA_Sofia"],["BG","FC Vihren Sandanski","Vihren Sandanski","FC_Vihren_Sandanski"],["BG","FC Chernomorets Burgas","Chernomorets Burgas","FC_Chernomorets_Burgas"],["BG","FC Fratria","Fratria","FC_Fratria"],["BG","PFC Beroe Stara Zagora","Beroe Stara Zagora","PFC_Beroe_Stara_Zagora"],["BG","FC Lokomotiv Gorna Oryahovitsa","Lokomotiv Gorna Oryahovitsa","FC_Lokomotiv_Gorna_Oryahovitsa"],["BG","FC Hebar Pazardzhik","Hebar Pazardzhik","FC_Hebar_Pazardzhik"],["BG","FC Yantra Gabrovo","Yantra Gabrovo","FC_Yantra_Gabrovo"],["BG","FC Rilski Sportist Samokov","Rilski Sportist Samokov","FC_Rilski_Sportist_Samokov"],["BG","FC Marek Dupnitsa","Marek Dupnitsa","FC_Marek_Dupnitsa"],["BG","PFC Nesebar","Nesebar","PFC_Nesebar"],["BG","OFC Spartak Pleven","Spartak Pleven","OFC_Spartak_Pleven"],["BG","FC Etar Veliko Tarnovo","Etar Veliko Tarnovo","FC_Etar_Veliko_Tarnovo"],["BG","PFC Ludogorets II","Ludogorets Razgrad","PFC_Ludogorets_Razgrad"],["BG","PFC Montana","Montana","PFC_Montana"],["BG","FC Sportist Svoge","Sportist Svoge","FC_Sportist_Svoge"],["BG","PFC Dobrudzha Dobrich","Dobrudzha Dobrich","PFC_Dobrudzha_Dobrich"],["BG","OFC Pirin Blagoevgrad","Pirin Blagoevgrad","OFC_Pirin_Blagoevgrad"],["RO","CSM Cetatea 1932 Suceava","Cetatea Suceava","CSM_Cetatea_1932_Suceava"],["RO","CSL Ștefăneștii de Jos","Stefanestii de Jos","CSL_Ștefăneștii_de_Jos"],["RO","SCM Râmnicu Vâlcea","SCM Ramnicu Valcea","SCM_Râmnicu_Vâlcea"],["RO","SSU Politehnica Timișoara","Politehnica Timisoara","SSU_Politehnica_Timișoara"],["RO","SC Popești-Leordeni","Popesti-Leordeni","SC_Popești-Leordeni"],["RO","FC Bihor Oradea","FC Bihor Oradea","FC_Bihor_Oradea"],["RO","CSA Steaua București","Steaua Bucuresti","CSA_Steaua_București"],["RO","AFC Chindia Târgoviște","Chindia Targoviste","AFC_Chindia_Târgoviște"],["RO","AFC ASA Târgu Mureș","ASA Targu Mures","ASA_Târgu_Mureș"],["RO","AFC Metalul Buzău","Metalul Buzau","AFC_Metalul_Buzău"],["RO","CSM Slatina","CSM Slatina","CSM_Slatina"],["RO","CS Gloria Bistrița","Gloria Bistrita","CS_Gloria_Bistrița"],["RO","ACS FC Bacău","FC Bacau","FC_Bacău"],["RO","CS Concordia Chiajna","Concordia Chiajna","CS_Concordia_Chiajna"],["RO","CSM Reșița","CSM Resita","CSM_Reșița"],["RO","CS Afumați","CS Afumati","CS_Afumați"],["RO","CSC Dumbrăvița","CSC Dumbravita","CSC_Dumbrăvița"],["RO","CSC 1599 Șelimbăr","CSC Selimbar","CSC_1599_Șelimbăr"],["RO","CS Dinamo București","CS Dinamo Bucuresti","CS_Dinamo_București"],["RO","FC Hermannstadt","Hermannstadt","FC_Hermannstadt"],["RO","AFC Unirea 04 Slobozia","Unirea Slobozia","AFC_Unirea_04_Slobozia"],["RO","FC Metaloglobus București","Metaloglobus","FC_Metaloglobus_București"],["RO","ACS Minerul Lupeni","Minerul Lupeni","CS_Minerul_Lupeni"],["RO","CS Progresul Spartac","Progresul Spartac","FC_Progresul_Spartac"],["RO","CS Sporting Liești","Sporting Liesti","CS_Sporting_Liești"],["RO","CSM Corona Brașov","Corona Brasov","CSM_Corona_Brașov"],["BG","FC Neftohimik Burgas","Neftohimik Burgas","PFC_Neftochimic_Burgas"],["BG","PFC Spartak 1947 Plovdiv","Spartak Plovdiv","FC_Spartak_Plovdiv"]]
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
 c,name,search,page=pair;id=[1900264000101,1900264000102,1900264000103,1900264000104,1900264000105,1900264000106,1900264000107,1900264000108,1900264000109,1900264000110,1900264000111,1900264000112,1900264000113,1900264000114,1900264100101,1900264100102,1900264100103,1900264100104,1900264100105,1900264100106,1900264100107,1900264100108,1900264100109,1900264100110,1900264100111,1900264100112,1900264100113,1900264100114,1900264100115,1900264100116,1900264100117,1900264100118,1900264200101,1900264200102,1900264200103,1900264200104,1900264200105,1900264200106,1900264200107,1900264200108,1900264200109,1900264200110,1900264200111,1900264200112,1900264200113,1900264200114,1900264200115,1900264200116,1900264200117,1900264200118,1900264200119,1900264200120,1900264200121,1900264200122,1900264200201,1900264200202,1900264200203,1900264200204,1900264100201,1900264100202][i]
 rec={"id":id,"country":c,"name":name,"status":"NO_CREST_FOUND","candidate":search}
 prospects=[]
 for q in [search,name]:
  url,meta=sports(q,c)
  if url:prospects.append((url,meta))
 url,meta=wikipedia(page)
 if url:prospects.append((url,meta))

 # Exact-match club-badge sources separately identified against team names and federation/club pages.
 known_urls={"1900264000102":["https://images.seeklogo.com/logo-png/49/1/fc-brera-strumica-logo-png_seeklogo-493901.png","FC Brera Strumica"],"1900264000106":["https://i.ibb.co/h2fZC3H/fk-euromilk-gorno-lisice-1960.png","FK Euromilk Gorno Lisice"],"1900264000108":["https://images.seeklogo.com/logo-png/20/1/fk-novaci-logo-png_seeklogo-201049.png","FK Novaci"],"1900264000114":["https://static.cdnlogo.com/logos/f/41/fudbalski-klub-teteks_800.png","FK Teteks Tetovo"],"1900264100106":["https://seeklogo.com/images/F/fk-lokomotiv-gorna-oryahovitsa-logo-7866807028-seeklogo.com.png","Lokomotiv Gorna Oryahovitsa"],"1900264100107":["https://seeklogo.com/images/F/fk-hebar-pazardzhik-logo-30E158928C-seeklogo.com.png","FK Hebar Pazardzhik"],"1900264100115":["https://www.logotypes101.com/logos/518/8EF57A3C4375307B4A8B01A5C5645879/montana%20%5BConverted%5D.png","FK Montana"],"1900264200102":["https://www.frf-ajf.ro/upload/echipe/10895.jpg","CSL Stefanestii (football regional association photo)"],"1900264200106":["https://www.fcbihor.ro/media/stiri/FC-Bihor-sigla.jpg","FC Bihor (official club badge)"],"1900264200107":["https://commons.wikimedia.org/wiki/Special:FilePath/FC_Steaua_Bucure%C5%9Fti.png","CSA Steaua Bucharest 2025"],"1900264200108":["https://assets.football-logos.cc/logos/romania/1500x1500/chindia-targoviste.bf43227b.png","Chindia Targoviste"],"1900264200105":["https://www.europlan-online.de/files/f4709692ab9cd6fcf556e2b1e678a0d4.png","SC Popesti-Leordeni"],"1900264200109":["https://seeklogo.com/images/A/asa-tg-mures-logo-CBFEE72A6D-seeklogo.com.png","ASA Targu Mures"],"1900264200111":["https://images.seeklogo.com/logo-png/64/1/csm-slatina-logo-png_seeklogo-647022.png","CSM Slatina"],"1900264200112":["https://pbs.twimg.com/profile_images/1031091525437063168/Nt9l0Cf3.jpg","CS Gloria 2018 Bistrita Nasaud"],"1900264200116":["https://images.seeklogo.com/logo-png/29/1/cs-afumai-logo-png_seeklogo-292122.png","CS Afumati"],"1900264200119":["https://media.dcsport.ro/image/202405/w1600/dinamo_sigla_48647900.jpg","CS Dinamo Bucuresti not FC Dinamo"],"1900264200202":["https://ligapunctelorpenny.ro/storage/media/137/Progresul_Spartac.svg.png","AFC Progresul Spartac"],"1900264200204":["https://www.frf-ajf.ro/upload/echipe/8858.jpg","CSM Corona Brasov (regional association)"],"1900264000110":["https://seeklogo.com/images/F/fk-osogovo-kocani-logo-B7C88BADA4-seeklogo.com.png","FK Osogovo Kocani"],"1900264200201":["https://r2.thesportsdb.com/images/media/team/badge/mxbh9l1770270946.png","CS Minerul Lupeni"]}
 if str(id) in known_urls:
  url,title=known_urls[str(id)]
  prospects.insert(0,(url,{"provider":"Exact-identity catalog or federation image","identity":title,"sourceImage":url}))

 # Two separately verified Macedonian club crests; never confuse Tetovo and Haraçinë.
 if id==999999000006:
  prospects.append(("https://r2.thesportsdb.com/images/media/team/badge/lec0bk1779941482.png",{"provider":"TheSportsDB club 155729, Shkëndija Haraçinë 1977","sourcePage":"https://www.thesportsdb.com/team/155729-shk%C3%ABndija-hara%C3%A7in%C3%AB"}))
 if id==999999000009:
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
manifest={"idMapping":{"1900264000101":"FK Belasica Strumica","1900264000102":"FC AP Brera Strumica","1900264000103":"FK Detonit Plachkovica","1900264000104":"KF Kamjani","1900264000105":"FK Kozhuf Gevgelija","1900264000106":"FK Euromilk Gorno Lisiche","1900264000107":"FK Makedonija Gjorče Petrov","1900264000108":"FK Novaci","1900264000109":"FK Ohrid Lychnidos","1900264000110":"FK Osogovo Kočani","1900264000111":"FK Pelister Bitola","1900264000112":"FK Rabotnički Skopje","1900264000113":"KF Shkupi","1900264000114":"FK Teteks Tetovo","1900264100101":"PFC CSKA Sofia II","1900264100102":"FC Vihren Sandanski","1900264100103":"FC Chernomorets Burgas","1900264100104":"FC Fratria","1900264100105":"PFC Beroe Stara Zagora","1900264100106":"FC Lokomotiv Gorna Oryahovitsa","1900264100107":"FC Hebar Pazardzhik","1900264100108":"FC Yantra Gabrovo","1900264100109":"FC Rilski Sportist Samokov","1900264100110":"FC Marek Dupnitsa","1900264100111":"PFC Nesebar","1900264100112":"OFC Spartak Pleven","1900264100113":"FC Etar Veliko Tarnovo","1900264100114":"PFC Ludogorets II","1900264100115":"PFC Montana","1900264100116":"FC Sportist Svoge","1900264100117":"PFC Dobrudzha Dobrich","1900264100118":"OFC Pirin Blagoevgrad","1900264200101":"CSM Cetatea 1932 Suceava","1900264200102":"CSL Ștefăneștii de Jos","1900264200103":"SCM Râmnicu Vâlcea","1900264200104":"SSU Politehnica Timișoara","1900264200105":"SC Popești-Leordeni","1900264200106":"FC Bihor Oradea","1900264200107":"CSA Steaua București","1900264200108":"AFC Chindia Târgoviște","1900264200109":"AFC ASA Târgu Mureș","1900264200110":"AFC Metalul Buzău","1900264200111":"CSM Slatina","1900264200112":"CS Gloria Bistrița","1900264200113":"ACS FC Bacău","1900264200114":"CS Concordia Chiajna","1900264200115":"CSM Reșița","1900264200116":"CS Afumați","1900264200117":"CSC Dumbrăvița","1900264200118":"CSC 1599 Șelimbăr","1900264200119":"CS Dinamo București","1900264200120":"FC Hermannstadt","1900264200121":"AFC Unirea 04 Slobozia","1900264200122":"FC Metaloglobus București","1900264200201":"ACS Minerul Lupeni","1900264200202":"CS Progresul Spartac","1900264200203":"CS Sporting Liești","1900264200204":"CSM Corona Brașov"},"date":"2026-10-24","base":"Official 2026/27 D2 and Romanian Cup group phase","crests":assets,"federationLogos":logs,"status":"DOWNLOADS_CHECKED_BYTES_NOT_MANUAL_VISUAL_AUTHENTICATION"}
(BASE/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print("CRESTS",sum(x["status"]=="SOURCE_IDENTIFIED" for x in assets),"/",len(assets))
print("MISSING",[(x["id"],x["name"]) for x in assets if x["status"]!="SOURCE_IDENTIFIED"])
print("FEDERATIONS",logs)
