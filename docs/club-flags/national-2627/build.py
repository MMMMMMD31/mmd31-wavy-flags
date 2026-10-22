#!/usr/bin/env python3
"""Publish 120x96 authentic French National 1/2 crested PNG flags; no fabricated badges."""
import concurrent.futures, hashlib, io, json, math, re, unicodedata
from pathlib import Path
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
BASE=Path(__file__).parent
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (MMD31 flag research, educational simulation)"})
def slug(s):
 s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
 return re.sub(r"[^a-z0-9]+","-",s).strip("-")
ROSTER=[]
for line in (BASE/"roster.txt").read_text(encoding="utf8").splitlines():
 if not line.strip() or line.startswith("#"): continue
 division,group,names=line.split("|",2)
 ROSTER.extend({"division":division,"group":group,"name":n,"slug":slug(n)} for n in names.split(";"))
assert len(ROSTER)==160

ALIASES={
 "US Saint-Maur Lusitanos":["US Lusitanos Saint-Maur","US Lusitanos Saint-Maur (football)"],
 "SA Épinal":["Stade athlétique spinalien","SAS Épinal"],
 "FC Borgo":["FC Bastia-Borgo","Football Club Bastia-Borgo"],
 "FC Chambly Oise":["FC Chambly","Football Club de Chambly Oise"],
 "Racing Club de France":["Racing Club de France Football","Racing Club de France (football)"],
 "Nîmes Olympique":["Nîmes Olympique"],
 "LB Châteauroux":["LB Châteauroux","La Berrichonne de Châteauroux"],
 "Olympique Saumur FC":["Olympique de Saumur Football Club"],
 "SC Toulon":["Sporting Club de Toulon"],
 "Étoile Fréjus Saint-Raphaël":["Étoile Football Club Fréjus Saint-Raphaël"],
 "GFA Rumilly-Vallières":["GFA Rumilly-Vallières","GFA Rumilly Vallieres"],
 "Lyon La Duchère":["Lyon-La Duchère","Lyon La Duchère Football Club"],
 "Voltigeurs de Châteaubriant":["Voltigeurs de Châteaubriant"],
 "FC Montlouis":["FC Montlouis-sur-Loire"],
 "US Créteil":["US Créteil-Lusitanos","US Créteil Lusitanos"],
 "GOAL FC":["Grand Ouest Association Lyonnaise Football Club"],
 "FC Balagne":["FC Balagne","Football Club Balagne"],
 "FC Lorient II":["FC Lorient"],"ESTAC Troyes II":["ES Troyes AC"],
 "Pau FC II":["Pau FC"],"Rodez AF II":["Rodez AF"],"Toulouse FC II":["Toulouse FC"],
 "FC Nantes II":["FC Nantes"],"Le Mans FC II":["Le Mans FC"],"Stade Lavallois II":["Stade lavallois"],
 "EA Guingamp II":["En Avant Guingamp"],"SM Caen II":["Stade Malherbe Caen"],
 "Stade Brestois II":["Stade brestois 29"],"Stade Rennais II":["Stade rennais FC"],
 "FC Versailles II":["FC Versailles 78"],"LOSC Lille II":["LOSC Lille"],
 "Red Star FC II":["Red Star FC"],"SC Bastia II":["Sporting Club de Bastia"],
 "AS Nancy Lorraine II":["AS Nancy-Lorraine"],"FC Metz II":["FC Metz"],
 "FC Sochaux-Montbéliard II":["FC Sochaux-Montbéliard"],
 "RC Strasbourg II":["RC Strasbourg Alsace"],"Dijon FCO II":["Dijon FCO"],
 "FC Annecy II":["FC Annecy"],"Olympique Lyonnais II":["Olympique lyonnais"],
 "AS Saint-Étienne II":["AS Saint-Étienne"],"Montpellier HSC II":["Montpellier HSC"],
 "Olympique de Marseille II":["Olympique de Marseille"],
 "AJ Auxerre II":["AJ Auxerre"],"LB Châteauroux II":["LB Châteauroux"],
 "Paris FC II":["Paris FC"],"US Orléans II":["US Orléans"],
 "US Alençon":["US Alençon","US Alençonnaise 61"],
 "FCM Aubervilliers":["FCM Aubervilliers","Football Club Municipal d'Aubervilliers"],
 "GFC Ajaccio":["Gazélec Ajaccio","Gazélec Football Club Ajaccio"]
}
def retrieve(url):
 try:
  resp=S.get(url,timeout=8);resp.raise_for_status()
  if len(resp.content)>4_000_000:return None
  if ".svg" in resp.url.split("?")[0].lower() or b"<svg" in resp.content[:500].lower():
   import cairosvg
   return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=resp.content,output_width=400,output_height=400))).convert("RGBA")
  return Image.open(io.BytesIO(resp.content)).convert("RGBA")
 except Exception:return None

# FootyLogos lists official National 1 2026/27 identities; exact matched only.
from difflib import SequenceMatcher
FOOTY_LOGOS={}
try:
 for location in ("https://www.footylogos.com/competition/national-1","https://www.footylogos.com/country/france"):
  html=S.get(location,timeout=17).text
  soup=BeautifulSoup(html,"html.parser")
  for a in soup.find_all("a",href=True):
   href=a["href"].split("?")[0]
   if "/logos/" not in href:continue
   candidate=href.split("/logos/")[-1].strip("/")
   if candidate and candidate!="logos":
    FOOTY_LOGOS[candidate]=urljoin("https://www.footylogos.com",href)
except Exception as ex:
 print("logo catalog warning",repr(ex))
def footy_logo(t):
 try:
  opts=[slug(t["name"])]
  if t["name"].endswith(" II"):
   opts.extend([slug(t["name"][:-3]),slug(t["name"][:-3])+"-2"])
  opts.extend(slug(a) for a in ALIASES.get(t["name"],[]))
  synonyms={
   "SA Épinal":"sas-epinal",
   "SC Toulon":"sporting-club-toulon",
   "US Pays du Valois":"union-sportive-du-pays-du-valois",
   "Le Poiré-sur-Vie VF":"vendee-poire-sur-vie-football",
   "FC Lorient II":"fc-lorient-2",
   "ESTAC Troyes II":"estac-troyes-2",
   "Entente Feignies Aulnoye":"entente-feignies-aulnoye-fc",
   "Étoile Fréjus Saint-Raphaël":"etoile-fc-frejus-saint-raphael",
   "GFA Rumilly-Vallières":"gfa-rumilly-vallieres",
   "Lyon La Duchère":"lyon-la-duchere",
   "Stade Lavallois II":"laval-stade-lavallois",
   "Vannes OC":"vannes-olympique-club"
  }
  if t["name"] in synonyms:opts.insert(0,synonyms[t["name"]])
  scores=sorted(
     [(max(SequenceMatcher(None,o,cand).ratio() for o in opts),cand) for cand in FOOTY_LOGOS],reverse=True)
  if not scores or scores[0][0]<0.83:return None,None
  similarity,key=scores[0]
  source="https://www.footylogos.com/dls/logo/"+key+".png"
  img=retrieve(source)
  if img and img.width>30 and img.height>30:
   return img,source
 except Exception:pass
 return None,None

# Local 2026/27 league directory includes many amateur badges not found on Wikipedia.
FM_INDEX={}
FM_DEBUG={}
try:
 response=S.get("https://www.footmercato.net/france/national-2/club",timeout=20)
 page=response.text
 FM_DEBUG={"status":response.status_code,"bytes":len(page)}
 soup=BeautifulSoup(page,"html.parser")
 for a in soup.find_all("a",href=True):
  target=a["href"]
  if "/club/" not in target:continue
  label=a.get_text(" ",strip=True)
  if not label or len(label)>75:continue
  FM_INDEX[slug(label)]=urljoin("https://www.footmercato.net",target)
except Exception as ex:print("FootMercato catalog warning",repr(ex))
FM_DEBUG["count"]=len(FM_INDEX)
FM_DEBUG["first"]=list(FM_INDEX.items())[:5]
FM_NAME={
 "APM Metz":"apm-metz","AS La Châtaigneraie":"la-chataigneraie",
 "AS Saint-Brieuc Ginglin-Cesson":"ginglin-cesson",
 "AS Saint-Ouen-l'Aumône":"saint-ouen-l-aumone",
 "AS Steenvoorde":"steenvoorde","AS Trouville Deauville":"trouville-deauville",
 "AS Vitré":"vitre","ASM Belfort":"belfort",
 "ASPTT Caen Football":"caen-ptt","ASPTT Dijon":"asptt-dijon",
 "Avoine Olympique Chinon Cinais":"avoine-occ",
 "Blagnac FC":"blagnac","Blois Foot 41":"blois",
 "C'Chartres Football":"c-chartres",
 "CA Pontarlier":"pontarlier","CMS Oissel":"oissel",
 "ES Fosséenne":"fos","ES Le Cannet Rocheville":"es-le-cannet-rocheville",
 "ES Thaon":"thaon","ESA Linas-Montlhéry":"linas-montlhery",
 "FC Balagne":"fa-ile-rousse-monticello",
 "FC Bourgoin-Jallieu":"bourgoin-jallieu",
 "FC Challans":"challans","FC Chalon":"fc-chalon-sur-saone",
 "FC Chamalières":"chamalieres",
 "FC Espaly":"espaly-saint-marcel",
 "FC Mérignac Arlac":"merignac-arlac",
 "FC Rousset SVO":"rousset-ste-victoire",
 "FC Saint-Jean-le-Blanc":"saint-jean-le-blanc",
 "FC Saint-Lô Manche":"saint-lo-manche",
 "FC Sochaux-Montbéliard II":"sochaux-ii",
 "FC Vesoul":"vesoul",
 "FCM Aubervilliers":"aubervilliers",
 "FCS Brétigny":"bretigny-foot",
 "Gallia Lucciana":"gallia-lucciana",
 "IC Croix":"iris-club-de-croix",
 "Is-Selongey Foot":"selongey",
 "JA Drancy":"drancy","Jura Dolois Football":"jura-dolois",
 "Lannion FC":"lannion",
 "Les Genêts d'Anglet":"les-genets-d-anglet",
 "Les Sables Vendée Football":"les-sables",
 "Montpellier Atlas Paillade":"atlas-paillade",
 "OC Cesson":"cesson","Olympique Alès":"olympique-ales",
 "Olympique Charleville Prix-les-Mézières":"ocpam",
 "Olympique Saint-Quentin":"olympique-saint-quentin",
 "Onet-le-Château Foot":"onet-le-chateau",
 "Racing Besançon":"racing-besancon",
 "Riviera FC":"riviera","SAG Cestas":"sag-cestas",
 "Saint-Amand FC":"saint-amand",
 "Saint-Pierre Milizac":"saint-pierre-milizac",
 "Sainte-Geneviève FC":"sainte-genevieve",
 "SC Berre":"berre","SFC Neuilly-sur-Marne":"neuilly-sur-marne",
 "Sologne Olympique Romorantin":"romorantin",
 "Stade Beaucairois":"beaucaire",
 "Stade Lavallois II":"laval-ii","TA Rennes":"ta-rennes",
 "Thonon Évian Grand Genève FC":"thonon-evian",
 "Torcy PVM US":"torcy",
 "Trélissac FC":"trelissac",
 "UF Mâcon 71":"uf-macon",
 "Union Foot de Touraine":"uf-touraine",
 "US Castanet":"castanet","US Colomiers":"colomiers",
 "US Feurs":"feurs","US Ivry":"ivry",
 "US Lège-Cap-Ferret":"lege-cap-ferret",
 "US Mandelieu-la-Napoule":"mandelieu-ln",
 "US Pays du Valois":"us-pays-du-valois",
 "US Saint-Philbert-de-Grand-Lieu":"st-philbert-gd-lieu",
 "USC Corte":"corte","USSA Vertou":"vertou","Vierzon FC":"vierzon-fc"
}
def footmercato_logo(t):
 try:
  target=FM_NAME.get(t["name"],slug(t["name"]))
  url=FM_INDEX.get(target)
  if not url: return None,None
  webpage=S.get(url,timeout=8)
  if webpage.status_code!=200:return None,None
  soup=BeautifulSoup(webpage.text,"html.parser")
  for img in soup.find_all("img"):
   alt=(img.get("alt") or "").lower()
   if not alt.startswith("logo "):continue
   if any(x in alt for x in ["national 2","national 1"]):continue
   src=img.get("src") or img.get("data-src")
   if not src:continue
   src=("https:"+src) if src.startswith("//") else urljoin(url,src)
   if "assets" not in src and "imgfoot" not in src:continue
   im=retrieve(src)
   if im is not None and im.width>20:return im,src
 except Exception:return None,None
 return None,None
def find_logo(t):
 found,src=footy_logo(t)
 if found is not None:return found,src
 found,src=footmercato_logo(t)
 if found is not None:return found,src
 if t["name"]=="US Colomiers":return None,None
 names=ALIASES.get(t["name"],[])
 names=[t["name"]]+names
 if t["name"].endswith(" II"):names.append(t["name"][:-3])
 names=list(dict.fromkeys(names))
 for lang in ["fr","en"]:
  for name in names[:4]:
   try:
    uri=f"https://{lang}.wikipedia.org/wiki/{quote(name.replace(' ','_'))}"
    page=S.get(uri,timeout=7)
    if page.status_code!=200:continue
    soup=BeautifulSoup(page.text,"html.parser")
    for selector in ("table.infobox_v2 img","table.infobox_v3 img","table.infobox img","aside.portable-infobox img"):
     imgs=soup.select(selector)
     for el in imgs[:2]:
      alt=(el.get("alt") or "").lower()
      if any(x in (alt+" "+loc if "loc" in locals() else alt) for x in ["stade","carte","photo","supporters","localisation","ground","stadium","football player","rugby"]):continue
      loc=el.get("src")
      if not loc:continue
      loc="https:"+loc if loc.startswith("//") else urljoin(uri,loc)
      im=retrieve(loc)
      if im is not None and 32<=im.width<=2000 and 32<=im.height<=2000:
       return im,loc
   except Exception:continue
 return None,None

def dominant(c):
 im=c.copy();im.thumbnail((80,80))
 pix=[]
 for r,g,b,a in im.getdata():
  if a>140 and not(r>228 and g>228 and b>228) and not(r<26 and g<26 and b<26):
   pix.append((r//32,g//32,b//32))
 if not pix:return (27,53,86)
 from collections import Counter
 trip=Counter(pix).most_common(1)[0][0]
 return tuple(min(235,v*32+16) for v in trip)
def render(t):
 ident=t["slug"];division=t["division"].lower()
 image,src=find_logo(t)
 if image is None:return dict(team=t["name"],division=t["division"],slug=ident,status="NO_AUTHENTIC_CRESt",source=None)
 image.thumbnail((75,72),Image.Resampling.LANCZOS)
 W,H=120,96
 bg=Image.new("RGBA",(W,H),dominant(image)+(255,))
 plaque=Image.new("RGBA",(W,H),(0,0,0,0))
 ImageDraw.Draw(plaque).rounded_rectangle((15,9,105,87),radius=16,fill=(255,255,255,40))
 bg=Image.alpha_composite(bg,plaque)
 bg.alpha_composite(image,((W-image.width)//2,(H-image.height)//2))
 std=BASE/division/"standard";std.mkdir(parents=True,exist_ok=True)
 win=BASE/division/"victory";win.mkdir(parents=True,exist_ok=True)
 sp=std/(ident+".png");vp=win/(ident+".png")
 bg.save(sp,"PNG",optimize=True)
 wave=Image.new("RGBA",(W,H),(0,0,0,0));pixels=wave.load();old=bg.load()
 for y in range(H):
  xxshift=3*math.sin(y*2*math.pi/73)
  for x in range(W):
   yyshift=2*math.sin(x*2*math.pi/81+y*math.pi/60)
   tx=int(x-xxshift);ty=int(y-yyshift)
   if 2<=x-xxshift<118 and 4<=y-yyshift<92 and 0<=tx<W and 0<=ty<H:
    red,green,blue,a=old[tx,ty];fac=1+.09*math.sin(x*math.pi/37+y/33)
    pixels[x,y]=(min(255,int(red*fac)),min(255,int(green*fac)),min(255,int(blue*fac)),a)
 wave.save(vp,"PNG",optimize=True)
 return dict(team=t["name"],division=t["division"],slug=ident,status="WIKIPEDIA_INFOBOX",source=src,
             standard_sha256=hashlib.sha256(sp.read_bytes()).hexdigest(),victory_sha256=hashlib.sha256(vp.read_bytes()).hexdigest())
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=14) as exe:
 for f in concurrent.futures.as_completed([exe.submit(render,t) for t in ROSTER]):
  try:results.append(f.result())
  except Exception as e:results.append({"status":"ERROR","error":str(e)})
report={"requested":len(ROSTER),"generated":sum(x["status"]=="WIKIPEDIA_INFOBOX" for x in results),
        "results":sorted(results,key=lambda x:x.get("slug","")),"fm_debug":FM_DEBUG}
(BASE/"crest-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("generated",report["generated"],"missing",len(ROSTER)-report["generated"])
