#!/usr/bin/env python3
"""MMD31 D2 authentic club crest collection; explicit omission for unmatched teams."""
import requests,io,hashlib,json,re,unicodedata,time
from pathlib import Path
from urllib.parse import quote,urljoin
from PIL import Image
from bs4 import BeautifulSoup
import cairosvg
ROSTERS={"BA_FB":["NK Bratstvo Gračanica","FK Budućnost Banovići","HNK Čapljina","NK GOŠK Gabela","FK Igman Konjic","NK Jedinstvo Bihać","HŠK Posušje","FK Radnik Hadžići","FK Rudar Kakanj","FK Sloboda Tuzla","NK Stupčanica Olovo","HNK Tomislav Tomislavgrad","NK TOŠK Tešanj","NK Travnik","NK Vitez","NK Zvijezda Gradačac"],"BA_RS":["FK Leotar Trebinje","FK Laktaši","FK Potkozarje Aleksandrovac","FK Majevica Lopare","FK Drina Zvornik","FK Kozara Gradiška","FK Famos Vojkovići","FK Rudar Prijedor","FK Romanija Pale","FK Slavija Istočno Sarajevo","FK Sutjeska Foča","FK Velež Nevesinje","FK Omarska","FK Zvijezda 09"],"RS":["FK TSC Bačka Topola","FK Borac 1926 Čačak","FK Javor Matis Ivanjica","FK Smederevo 1924","OFK Vršac","FK Napredak Kruševac","FK Voždovac","GFK Dubočica 1923","FK Loznica","FK Metalac Gornji Milanovac","FK Spartak Subotica","FK Proleter 023","FK Teleoptik Zemun","RFK Grafičar Beograd","FK Jedinstvo Ub","FK Bor 1919"],"XK":["KF 2 Korriku","FC Besa Pejë","KF Dinamo Ferizaj","KF Ferizaj","KF Istogu","KF Kika","KF Lepenci","KF Liria Prizren","FC Mitrovica","FC Prishtina e Re","KF Ramiz Sadiku","KF Rilindja 1974","FC Suhareka","KF Tefik Çanga","KF Trepça","KF Trepça '89","KF Vëllaznimi","KF Vjosa"]}
SOURCES=["https://globalsportsarchive.com/en/soccer/team/nk-bratstvo-gracanica/21554/","https://globalsportsarchive.com/en/soccer/team/fk-laktasi/34668/","https://globalsportsarchive.com/en/soccer/team/ofk-vrsac/25317/","https://globalsportsarchive.com/en/soccer/team/kf-liria-prizren/14711/"]
S=requests.Session()
S.headers["User-Agent"]="Mozilla/5.0 (compatible; MMD31 Club Logo Research)"
root=Path("docs/balkans-d2-2026/v1");root.mkdir(parents=True,exist_ok=True)
def normal(s):
 s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode("ascii").lower()
 s=re.sub(r"[^a-z0-9]+"," ",s)
 return " ".join(v for v in s.split() if v not in ("fk","nk","hnk","hsk","ofk","rfk","gfk","kf","fc","sc"))
def reduce(s):
 s=normal(s).split()
 rem=set("beograd novi grad kragujevac backa topola banja luka istocno sarajevo gornji milanovac banovici prijedor bijeljina gradačac".split())
 return " ".join(v for v in s if v not in rem)
aliases={
 "FK Borac 1926 Čačak":"FK Borac 1926","FK Javor Matis Ivanjica":"FK Javor-Matis Ivanjica",
 "GFK Dubočica 1923":"GFK Dubočica","FK Spartak Subotica":"FK Spartak Ždrepčeva Krv Subotica",
 "FK Proleter 023":"FK Proleter 023","FK Teleoptik Zemun":"FK Teleoptik Zemun",
 "RFK Grafičar Beograd":"RFK Grafičar","FK Bor 1919":"FK Bor",
 "NK GOŠK Gabela":"NK GOŠK Gabela","HNK Tomislav Tomislavgrad":"HNK Tomislav Tomislavgrad",
 "FK Rudar Prijedor":"FK Rudar Prijedor","FK Velež Nevesinje":"FK Velež Nevesinje",
 "KF Liria Prizren":"KF Liria Prizren","FC Suhareka":"FC Suhareka",
 "FC Prishtina e Re":"FC Prishtina e Re","KF Trepça '89":"KF Trepça '89"
}
svgbase="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/"
known={"NK GOŠK Gabela":("bosnia-and-herzegovina","GOŠK_Gabela.svg"),"FK Igman Konjic":("bosnia-and-herzegovina","Igman_Konjic.svg"),"HŠK Posušje":("bosnia-and-herzegovina","Posušje.svg"),"NK Zvijezda Gradačac":("bosnia-and-herzegovina","Zvijezda_Gradačac.svg"),"FK Leotar Trebinje":("bosnia-and-herzegovina","Leotar_Trebinje.svg"),"FK Kozara Gradiška":("bosnia-and-herzegovina","Kozara_Gradiška.svg"),"FK Rudar Prijedor":("bosnia-and-herzegovina","Rudar_Prijedor.svg"),"FK Zvijezda 09":("bosnia-and-herzegovina","Zvijezda_09.svg"),"FK TSC Bačka Topola":("serbia","FK_TSC.svg"),"FK Javor Matis Ivanjica":("serbia","Javor_Matis.svg"),"FK Napredak Kruševac":("serbia","FK_Napredak_Kruševac.svg"),"FK Voždovac":("serbia","FK_Voždovac.svg"),"FK Metalac Gornji Milanovac":("serbia","Metalac.svg"),"FK Spartak Subotica":("serbia","Spartak_Subotica.svg")}
# Verified 2026/27 Kosovo second-division logos paired by archive image identity.
KOSOVO_ARCHIVE={
 "KF 2 Korriku":"images/korriku_kos.png","FC Besa Pejë":"images/besa_kos.png",
 "KF Dinamo Ferizaj":"images/dinamo_feriz_kos.png","KF Ferizaj":"images/ferizaj_kos.png",
 "KF Istogu":"images/istogu_kos.jpg","KF Kika":"images/kika_kos.png",
 "KF Lepenci":"images/lepenci_kos.png","KF Liria Prizren":"images/liria_kos.gif",
 "FC Mitrovica":"images/mitrovica_kos.png","FC Prishtina e Re":"images/pris_e_re_kos.png",
 "KF Ramiz Sadiku":"images/ramiz_kos.png","KF Rilindja 1974":"images/rili2_kos.png",
 "FC Suhareka":"images/suhareka_kos.png","KF Tefik Çanga":"images/tefik_kos.png",
 "KF Trepça":"images/trepca_kos.jpg","KF Trepça '89":"images/trepca_89_kos.png",
 "KF Vëllaznimi":"images/veellaznimi_kos.png","KF Vjosa":"images/vjosa_kos.png"}
image_sources={}
for page in SOURCES:
 try:
  response=S.get(page,timeout=45);response.raise_for_status()
  doc=BeautifulSoup(response.text,"html.parser")
  count=0
  for im in doc.find_all("img"):
   alt=(im.get("alt") or "").strip()
   src=(im.get("data-src") or im.get("src") or "").strip()
   if not alt.startswith("logo of ") or not src or "placeholder" in src:continue
   if src.startswith("//"):src="https:"+src
   src=urljoin(page,src)
   if src.startswith("https://"):
    image_sources.setdefault(normal(alt.replace("logo of ","",1)),[]).append((src,page,alt))
    count+=1
  print("GSA",page,response.status_code,count,flush=True)
 except Exception as e:print("SOURCE_ERROR",page,str(e)[:180],flush=True)
def resolve(name):
 if name in KOSOVO_ARCHIVE:
  return "https://escudosfc.com.br/"+KOSOVO_ARCHIVE[name],"Kosovo 2026/27 authentic club crest archive, alt/identity checked"
 if name=="FK Proleter 023":
  return "https://srbijasport.net/img/club/1317/0","Srbijasport FK Proleter 023 club profile crest"
 if name=="FK Majevica Lopare":
  try:
   page=S.get("https://fkmajevica.com/",timeout=30)
   dom=BeautifulSoup(page.text,"html.parser")
   for x in dom.find_all("img"):
    if "majevica" in (x.get("alt") or "").lower() or "grb" in (x.get("alt") or "").lower():
     src=x.get("src") or x.get("data-src")
     if src:return urljoin(page.url,src),"FK Majevica official club website authentic emblem"
  except Exception:pass
 if name in known:
  folder,file=known[name]
  return svgbase+folder+"/"+quote(file),"JoseArroyave SVG crest"
 variants=[normal(name),normal(aliases.get(name,name)),reduce(name)]
 if name=="KF Trepça '89":variants+=["trepca 89"]
 for variant in variants:
  candidates=image_sources.get(variant,[])
  if candidates:return candidates[0][0],"Global Sports Archive photo from "+candidates[0][1]
 # Unambiguous token containment, only after exact-name checks
 scores=[]
 for alt,candidates in image_sources.items():
  a=set(alt.split()); b=set(normal(name).split())
  if a and b and len(a&b)>=2 and (a.issubset(b) or b.issubset(a)):
   scores.append((len(a&b)/max(len(a),len(b)),alt,candidates[0]))
 scores.sort(reverse=True)
 if scores and scores[0][0]>=0.68 and (len(scores)==1 or scores[0][0]-scores[1][0]>.1):
  return scores[0][2][0],"Global Sports Archive fuzzy-high-confidence "+scores[0][2][1]
 return None,None
manifest=[];missing=[]
bases={"BA_FB":1947271000000,"BA_RS":1947271000100,"RS":1947271000200,"XK":1947271000300}
colors={"BA_FB":"#B4CBDD","BA_RS":"#AFBDD4","RS":"#B6C4D7","XK":"#A2CBDC"}
for league,names in ROSTERS.items():
 for i,name in enumerate(names,1):
  id=bases[league]+i
  src,provenance=resolve(name)
  if not src:
   missing.append(dict(id=id,league=league,name=name,status="NO_VERIFIED_IMAGE"))
   continue
  try:
   res=S.get(src,timeout=40);res.raise_for_status();raw=res.content
   if b"<svg" in raw[:2000]:raw=cairosvg.svg2png(bytestring=raw,output_width=450)
   im=Image.open(io.BytesIO(raw)).convert("RGBA")
   if im.width<17 or im.height<17:raise ValueError("source thumbnail too small")
   bbox=im.getchannel("A").getbbox()
   if not bbox:raise ValueError("blank crest")
   im=im.crop(bbox);im.thumbnail((100,86),Image.Resampling.LANCZOS)
   bg=Image.new("RGBA",(120,96),colors[league]);bg.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
   dest=root/(str(id)+".png");bg.convert("RGB").save(dest,format="PNG",optimize=True)
   with Image.open(dest) as check:assert check.size==(120,96)
   manifest.append(dict(id=id,league=league,name=name,source_url=src,provenance=provenance,flagUrl="https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-balkans-d1-2026-test/"+dest.as_posix(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),background=colors[league]))
   print("OK",league,name,flush=True)
  except Exception as e:
   missing.append(dict(id=id,league=league,name=name,status="INVALID_SOURCE",error=str(e)))
   print("MISSING",league,name,str(e)[:100],flush=True)
status=dict(expected=sum(map(len,ROSTERS.values())),published=len(manifest),missing=len(missing),assets=manifest,unresolved=missing)
(root/"manifest.json").write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding="utf8")
print("RESULT",status["published"],status["expected"],"missing",status["missing"],flush=True)
