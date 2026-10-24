#!/usr/bin/env python3
import io,json,hashlib,urllib.parse,requests
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
import cairosvg
R=Path("docs/cge33-adriatic-d2-2026-27/v1");R.mkdir(parents=True,exist_ok=True)
RAW="""slovenia|ND Primorje|Primorje.svg|nd-primorje
slovenia|NK Triglav Kranj||triglav-kranj
slovenia|ND Beltinci||beltinci
slovenia|NK Tabor Sežana|Tabor.svg|tabor-sezana
slovenia|NK Bistrica||bistrica
slovenia|ND Dravinja||dravinja
slovenia|NK Rudar Velenje|Rudar_Velenje.svg|rudar-velenje
slovenia|ND Bilje||bilje
slovenia|NK Jadran Dekani||jadran-dekani
slovenia|ND Slovan||slovan-ljubljana
slovenia|NK Krka||krka
slovenia|ND Ilirija 1911||ilirija-1911
slovenia|NK Krško Posavje|Krško.svg|krsko-posavje
slovenia|ŠD Jesenice||jesenice
slovenia|NK Brežice 1919||brezice-1919
slovenia|NK Vrhnika||vrhnika
croatia|NK Sesvete||sesvete
croatia|NK Dugopolje|NK_Dugopolje.svg|dugopolje
croatia|NK Mladost Ždralovi||mladost-zdralovi
croatia|HNK Segesta|HNK_Segesta_Sisak.svg|segesta
croatia|GNK Dinamo Zagreb II|GNK_Dinamo_Zagreb.svg|dinamo-zagreb
croatia|HNK Cibalia||cibalia
croatia|NK Croatia Zmijavci||croatia-zmijavci
croatia|NK Jadran Luka Ploče||jadran-luka-ploce
croatia|NK Opatija||opatija
croatia|NK Hrvace||hrvace
croatia|NK Dubrava Tim Kabel||dubrava
croatia|NK BSK Bijelo Brdo||bsk-bijelo-brdo
croatia|HNK Orijent||orijent
croatia|HNK Vukovar 1991|HNK_Vukovar.svg|vukovar-1991
croatia|NK Kustošija||kustosija
croatia|NK Karlovac 1919||karlovac-1919
montenegro|FK Jedinstvo Bijelo Polje|FK_Jedinstvo_Bijelo_Polje.svg|jedinstvo-bijelo-polje
montenegro|OFK Grbalj||grbalj
montenegro|FK Budva||budva
montenegro|FK Iskra Danilovgrad||iskra-danilovgrad
montenegro|FK Kom Podgorica||kom-podgorica
montenegro|FK Lovćen Cetinje||lovcen
montenegro|FK Podgorica||podgorica
montenegro|FK Berane||berane
montenegro|FK Rudar Pljevlja||rudar-pljevlja
montenegro|FK Zeta Golubovci||zeta-golubovci
albania|KF Bylis|Bylis.svg|bylis
albania|FC Flamurtari|Flamurtari.svg|flamurtari
albania|KF Pogradeci|Pogradec.svg|pogradeci
albania|KF Iliria||iliria
albania|KF Besa|Besa.svg|besa-kavaje
albania|KF Kastrioti|Kastrioti.svg|kastrioti
albania|KS Burreli||burreli
albania|KF Korabi||korabi
albania|FK Kukësi|Kukës.svg|kukesi
albania|KS Besëlidhja Lezhë||beselidhja-lezhe
albania|KF Oriku||oriku
albania|KS Sopoti||sopoti"""
ss=requests.Session();ss.headers["User-Agent"]="Mozilla/5.0 (compatible; MMD31 club emblem audit)"
def fetch(url):
 try:
  r=ss.get(url,timeout=10);r.raise_for_status()
  if len(r.content)>7_000_000: return None,""
  return r.content,r.headers.get("content-type","")
 except Exception:return None,""
def img(data):
 try:
  if b"<svg" in data[:1800]:return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data,output_width=400)))
  im=Image.open(io.BytesIO(data));im.load()
  if im.width>=55 and im.height>=55:return im
 except Exception:pass
 return None
def retrieve(country,n,slug,name):
 candidates=[]
 if n:candidates.append("https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/"+country+"/"+urllib.parse.quote(n))
 candidates.append("https://assets.footylogos.com/logos/"+slug+"/"+slug+"-logo-footylogos.svg")
 for stem in [slug,slug.removeprefix("nk-").removeprefix("fk-"),slug.removeprefix("hnk-")]:
  candidates.append("https://football-logos.cc/"+country+"/"+stem+"/")
  if country=="croatia":candidates.append("https://football-logos.cc/"+stem+"/")
 for url in candidates:
  data,typ=fetch(url)
  if not data:continue
  im=img(data)
  if im:return im,url
  if "html" in typ or b"<html" in data[:300].lower():
   try:
    soup=BeautifulSoup(data,"html.parser")
    possible=[]
    for z in soup.select("img"):
     alt=z.get("alt","").lower()
     u=z.get("data-src") or z.get("src")
     if u and ("logo" in alt or "crest" in alt or "badge" in alt or "escudo" in alt):possible.append(urllib.parse.urljoin(url,u))
    for z in soup.select('meta[property="og:image"]'):
     if z.get("content"):possible.append(urllib.parse.urljoin(url,z["content"]))
    for u in list(dict.fromkeys(possible))[:8]:
     binary,_=fetch(u)
     if binary:
      ii=img(binary)
      if ii:return ii,u
   except Exception:pass
 return None,None
rows=[]
for raw in RAW.splitlines():
 country,name,filename,slug=raw.split("|")
 ci={"slovenia":0,"croatia":1,"montenegro":2,"albania":3}[country]
 index=len([x for x in rows if x["country"]==country])
 tid=1942700200000+ci*100+index
 im,source=retrieve(country,filename,slug,name)
 info={"teamId":tid,"name":name,"country":country,"source":source,"sourceCandidate":filename or slug}
 if im:
  cols={"slovenia":"#A9D0B7","croatia":"#B7CDEA","montenegro":"#BAD1E8","albania":"#D7B2B2"}
  im=im.convert("RGBA");im.thumbnail((100,82),Image.Resampling.LANCZOS)
  dst=Image.new("RGBA",(120,96),cols[country]);dst.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  out=R/(str(tid)+".png");dst.save(out,optimize=True)
  info.update({"status":"PNG_REAL_SOURCE_CANDIDATE","sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"dimensions":[120,96],"background":cols[country]})
 else:info["status"]="MISSING_REAL_CREST"
 rows.append(info);print(country,name,info["status"],source,flush=True)
(R/"manifest.json").write_text(json.dumps({"edition":"2026-27","records":rows,"published":sum(x["status"].startswith("PNG") for x in rows)},ensure_ascii=False,indent=2),encoding="utf-8")
print("PUBLISHED",sum(x["status"].startswith("PNG") for x in rows),"/",len(rows),flush=True)
