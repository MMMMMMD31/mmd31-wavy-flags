#!/usr/bin/env python3
"""MMD31: source-authenticated D2 crests (no generic placeholders)."""
import io,json,hashlib,urllib.parse,requests,re
from pathlib import Path
from PIL import Image,ImageOps
import cairosvg
from bs4 import BeautifulSoup
OUT=Path("docs/cge33-adriatic-d2-2026-27/v1");OUT.mkdir(parents=True,exist_ok=True)
NZS="https://www.nzs.si/sites/default/files/media/image/"
# ID, club, source candidates. Source pages accept only exact-club crests.
SOURCES=[
(1942700200001,"NK Triglav Kranj",[NZS+"NKTriglavKranj.svg"]),
(1942700200002,"ND Beltinci",[NZS+"NDBeltinci.svg"]),
(1942700200004,"NK Bistrica",[NZS+"NKBistrica.svg"]),
(1942700200005,"ND Dravinja",[NZS+"NDDravinja.svg"]),
(1942700200007,"ND Bilje",[NZS+"NDBilje.svg"]),
(1942700200008,"NK Jadran Dekani",[NZS+"NKJadranDekani.svg"]),
(1942700200009,"ND Slovan",[NZS+"NDSlovan.svg"]),
(1942700200010,"NK Krka",[NZS+"NKKrka.svg"]),
(1942700200011,"ND Ilirija 1911",[NZS+"NDIlirija1911.svg"]),
(1942700200013,"ŠD Jesenice",[NZS+"NKJesenice.svg"]),
(1942700200014,"NK Brežice 1919",[NZS+"Brezice.svg"]),
(1942700200015,"NK Vrhnika",[NZS+"NKVrhnika.svg"]),
(1942700200105,"HNK Cibalia",["https://cdn-img.zerozero.pt/img/logos/equipas/1859_imgbank_1688380826.png"]),
(1942700200109,"NK Hrvace",["https://r2.thesportsdb.com/images/media/team/badge/4ua0v41751790393.png"]),
(1942700200111,"NK BSK Bijelo Brdo",["https://www.ogol.com.br/img/logos/equipas/61528_imgbank_1688381755.png"]),
(1942700200112,"HNK Orijent",["https://cdn-img.zerozero.pt/img/logos/equipas/28771_imgbank_1688381306.png"]),
(1942700200114,"NK Kustošija",["https://cdn-img.zerozero.pt/img/logos/equipas/66591_imgbank_1688382309.png"]),
(1942700200115,"NK Karlovac 1919",["https://nk-karlovac1919.hr/wp-content/uploads/2025/01/08_nk_karlovac_1919.png"]),
(1942700200201,"OFK Grbalj",["https://cdn.freebiesupply.com/logos/large/2x/fk-grbalj-logo-png-transparent.png"]),
(1942700200202,"FK Budva",["https://fscg.me/en/matches/budva-otrant-olympic-9315967/","https://www.footballlogosandkits.com/LOGO%2BFK%20BUDVA"]),
(1942700200203,"FK Iskra Danilovgrad",["https://assets.football-logos.cc/logos/montenegro/700x700/iskra.1bfddc02.png"]),
(1942700200204,"FK Kom Podgorica",["https://images.seeklogo.com/logo-png/35/1/fk-kom-podgorica-logo-png_seeklogo-357664.png"]),
(1942700200205,"FK Lovćen Cetinje",["https://www.europlan-online.de/files/85714688f89ce66a661da4ef401c9106.png"]),
(1942700200206,"FK Podgorica",["https://assets.football-logos.cc/logos/montenegro/700x700/fk-podgorica.3e7114d0.png"]),
(1942700200207,"FK Berane",["https://upload.wikimedia.org/wikipedia/fr/6/63/FK_Berane.gif"]),
(1942700200209,"FK Zeta Golubovci",["https://football-logos.cc/montenegro/fk-zeta/"]),
(1942700200303,"KF Iliria",["https://kruja.gov.al/rreth-krujes/kultura/sport/"]),
(1942700200306,"KS Burreli",["https://images.seeklogo.com/logo-png/49/1/kf-burreli-logo-png_seeklogo-493592.png"]),
(1942700200307,"KF Korabi",["https://www.playmakerstats.com/img/logos/equipas/48832_imgbank_1686580961.png"]),
(1942700200309,"KS Besëlidhja Lezhë",["https://images.seeklogo.com/logo-png/1/1/beselidhja-lezha-logo-png_seeklogo-18688.png"]),
(1942700200310,"KF Oriku",["https://www.europlan-online.de/files/b31ffc90e8c1196e3c16ba1c8e851888.png"]),
(1942700200311,"KS Sopoti",["https://images.seeklogo.com/logo-png/12/1/sopoti-librazhd-logo-png_seeklogo-129494.png"])]
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 logos research)"})
def load(url):
 try:
  r=S.get(url,timeout=13);r.raise_for_status()
  if len(r.content)>7000000:return None,""
  return r.content,r.headers.get("content-type","")
 except Exception:return None,""
def decode(binary):
 try:
  if b"<svg" in binary[:1500]:return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=binary,output_width=450)))
  im=Image.open(io.BytesIO(binary));im.load()
  if im.width>55 and im.height>55:return im
 except Exception:pass
 return None
def find_images(url,html,club):
 soup=BeautifulSoup(html,"html.parser")
 # Only logo/badge-tagged images near the club name, never arbitrary team photos.
 candidates=[]
 for elem in soup.select('img, meta[property="og:image"]'):
  u=elem.get("src") or elem.get("data-src") or elem.get("content")
  if not u:continue
  alt=(elem.get("alt") or "")+" "+(elem.get("title") or "")
  name=club.lower().replace("fk ","").replace("ofk ","").replace("kf ","")
  check=(u+" "+alt).lower()
  accept=("logo" in check or "grb" in check or "escudo" in check or "crest" in check)
  if "budva" in name:accept=accept and ("budva" in check or "logo" in alt.lower())
  if "iliria" in name:accept=accept and "iliria" in check
  if "zeta" in name:accept=accept and "zeta" in check
  if accept:candidates.append(urllib.parse.urljoin(url,u))
 return list(dict.fromkeys(candidates))[:15]
def acquire(url,club):
 binary,ctype=load(url)
 if not binary:return None,None
 im=decode(binary)
 if im:return im,url
 if "html" in ctype or b"<html" in binary[:200].lower():
  for u in find_images(url,binary,club):
   dat,_=load(u)
   if dat:
    im=decode(dat)
    if im:return im,u
 return None,None
def adjust(im,teamid):
 im=im.convert("RGBA")
 # avoid square white backgrounds where possible; no generated badge icon
 im.thumbnail((99,82),Image.Resampling.LANCZOS)
 band=(teamid-1942700200000)//100
 col=["#A7CAB7","#B9C9E0","#B5CBE1","#D2B4B7"][band]
 dst=Image.new("RGBA",(120,96),col)
 dst.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return dst.convert("RGB"),col
records=[]
for tid,name,urls in SOURCES:
 rec={"teamId":tid,"club":name,"status":"MISSING_UNVERIFIED","source":None,"attemptedSourceUrls":urls}
 for u in urls:
  im,source=acquire(u,name)
  if not im:continue
  img,col=adjust(im,tid)
  target=OUT/(str(tid)+".png")
  img.save(target,optimize=True)
  rec.update({"source":source,"status":"PUBLISHED_CREST_SOURCE_IDENTIFIED","dimensions":[120,96],"background":col,"sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
  break
 records.append(rec)
 print(tid,name,rec["status"],rec["source"],flush=True)
(OUT/"missing32_manifest.json").write_text(json.dumps({"published":sum(x["source"] is not None for x in records),"total":32,"records":records},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("TOTAL",sum(x["source"] is not None for x in records),"/32",flush=True)
