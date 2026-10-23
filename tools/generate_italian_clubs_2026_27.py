#!/usr/bin/env python3
"""MMD31: traceable REAL Italian badges on solid club-color 120x96 flags."""
import base64, zlib, re, io, json, time, unicodedata, hashlib
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote
import requests, cairosvg
from PIL import Image
ROSTER_B64 = "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"
NAMES=zlib.decompress(base64.b64decode(ROSTER_B64)).decode("utf-8").splitlines()
assert len(NAMES)==262 and len(set(NAMES))==262
ROOT=Path("docs/italian-clubs-2026-27/v1")
ROOT.mkdir(parents=True,exist_ok=True)
ROOT_REPO="JoseArroyave/football-logos"
ROOT_API="https://api.github.com/repos/"+ROOT_REPO+"/contents/logos/italy"
session=requests.Session()
session.headers.update({"User-Agent":"MMD31ItalyBadges/1.0"})
response=session.get(ROOT_API,timeout=35);response.raise_for_status()
sources=[item["name"] for item in response.json() if item["name"].lower().endswith(".svg")]
STOP=set("asd ac acd fcd ssd us ss ssc as fc football calcio calcistica club società societàsportiva sportiva 1907 1908 1909 1911 1912 1913 1914 1921 1922 1924 1926 1927 1928 1938 1944 1948 1949 1983 1902 1905 1920".split())
def norm(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode("ascii")
    s=re.sub(r"(?<=[a-z])(?=[A-Z])"," ",s)
    s=re.sub(r"[^a-zA-Z0-9]+"," ",s).lower()
    return " ".join(v for v in s.split() if v not in STOP and not re.fullmatch(r"\d+",v))
ALIASES={
"Südtirol":"Suditrol","L.R. Vicenza":"Vicenza","Atalanta U23":"Atalanta",
"Inter U23":"Inter","Milan Futuro":"Milan","Alcione Milano":"Alcione",
"Carpi":"AC_Carpi","Como":"Como_1907","Frosinone":"Frosinone_Calcio",
"Juve Stabia":"Juve_Stabia","Altamura":"Team_Altamura",
"Picerno":"AZ_Picerno","Fiorenzuola":"Fiorenzuola",
"Nuova Ternana":"Ternana","Atletico Ascoli":"Atletico_Ascoli",
"Arzignano Valchiampo":"FC_Arzignano_Valchiampo",
"Chievoverona":"AC_ChievoVerona",
"Ospitaletto Franciacorta":"Ospitaletto",
"Forsempronese":"Fossombrone_Calcio",
"Città di Pontedera":"Pontedera",
"Cittadella Modena":"Cittadella_Vis_Modena",
"Aurora Pro Patria":"Pro_Patria",
"Sant’Angelo":"AC_Sant'Angelo_1907",
"Rovato":"Rovato_Vertovese",
"Seravezza":"Seravezza_Pozzi_Calcio",
"Monastir":"ASD_Monastir_1983",
"Cos Sarrabus Ogliastra":"COS_Sarrabus_Ogliastra",
"Sassari Lattedolce":"Sassari_Calcio_Latte_Dolce",
"Nuova Igea Virtus":"Igea_Virtus_Barcellona",
"Athletic Palermo":"Athletic_Club_Palermo",
"Avola":"Calcio_Avola_1949",
"Castrumfavara":"Castrum_Favara",
"Palmese":"US_Palmese_1912",
"Ischia Isola Verde":"Ischia_Calcio",
"Puteoli Real Normanna":"Real_Normanna",
"Progresso":"SCD_Progresso_Calcio",
"Follonica Gavorrano":"US_Follonica_Gavorrano",
"Aquila Montevarchi":"Aquila_Montevarchi_1902",
"Flaminia Civitacastellana":"Flaminia_Civita_Castellana",
"Cjarlins Muzane":"ASD_Cjarlins_Muzane",
"Brian Lignano":"Brian_Lignano_Calcio",

"Monza":"Monza","Roma":"Roma","Treviso":"Treviso_FBC_1993",
"Palazzolo":"FC_Pro_Palazzolo",
"Scanzorosciate":"USD_Scanzorosciate_Calcio",
"La Rocca Altavilla":"Unione_La_Rocca_Altavilla",
"Castellanzese":"USD_Castellanzese_1921",
"Casatese Merate":"USD_Casatese_Merate",
"Oltrepò":"Oltrepò_FBC","Gelbison":"Gelbison_Cilento",
"Gravina":"FBC_Gravina",
"LME":""
}
def resolve(name):
    selected=ALIASES.get(name)
    if selected is not None:
        if not selected: return None,"no verified source",[]
        possible=[f for f in sources if f.lower().replace(".svg","")==selected.lower()]
        if possible:return possible[0],"manually matched",[]
        return None,"alias source absent",[]
    n=norm(name)
    exact=[f for f in sources if norm(f[:-4])==n]
    if len(exact)==1:return exact[0],"normalized exact",[]
    if len(exact)>1:return None,"ambiguous exact",exact
    ranked=sorted(((SequenceMatcher(None,n,norm(f[:-4])).ratio(),f) for f in sources),reverse=True)
    # Automatic fuzzy matches require high similarity and separation from second candidate.
    if ranked and ranked[0][0]>=.91 and (len(ranked)<2 or ranked[0][0]-ranked[1][0]>.075):
        return ranked[0][1],"strong fuzzy", ranked[:3]
    return None,"not confidently matched",ranked[:3]
def fetch_svg(filename):
    url="https://raw.githubusercontent.com/"+ROOT_REPO+"/main/logos/italy/"+quote(filename)
    last=None
    for _ in range(3):
        try:
            r=session.get(url,timeout=30);r.raise_for_status()
            if not b"<svg" in r.content[:1000] and b"<svg" not in r.content[:2000]:raise ValueError("Not SVG")
            return r.content,url
        except Exception as e: last=e;time.sleep(1)
    raise RuntimeError(str(last))
def get_background(im):
    small=im.copy();small.thumbnail((90,90))
    bins=Counter()
    for r,g,b,a in small.getdata():
        if a<128:continue
        if max(r,g,b)-min(r,g,b)<36:continue
        if max(r,g,b)<48 or min(r,g,b)>236:continue
        bins[(r//24,g//24,b//24)]+=1
    if bins:
        bucket=bins.most_common(1)[0][0]
        c=tuple(min(255,x*24+12) for x in bucket)
    else:c=(70,92,128)
    # Same club hue, softened to preserve contrast against dark crest details.
    if sum(c)/3<100:c=tuple(int(.58*v+.42*245) for v in c)
    elif sum(c)/3<148:c=tuple(int(.72*v+.28*245) for v in c)
    return c
def render(raw):
    img=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=raw,output_width=480))).convert("RGBA")
    bounds=img.getchannel("A").getbbox()
    if not bounds: raise ValueError("Empty badge")
    img=img.crop(bounds);bg=Image.new("RGBA",(120,96),get_background(img)+(255,))
    img.thumbnail((102,84),Image.Resampling.LANCZOS)
    bg.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
    out=bg.convert("RGB")
    assert out.size==(120,96)
    return out,bg.getpixel((0,0))[:3]
assets=[];missing=[];cache={}
for i,name in enumerate(NAMES):
    tid=1793400200000+i
    source,rule,alt=resolve(name)
    if not source:
        missing.append({"id":tid,"name":name,"reason":rule,"candidates":alt})
        continue
    try:
        if source not in cache:
            data,url=fetch_svg(source)
            cache[source]=render(data)+(hashlib.sha256(data).hexdigest(),url)
        im,color,sha,url=cache[source]
        target=ROOT/(str(tid)+".png")
        im.save(target,format="PNG",optimize=True)
        with Image.open(target) as check:assert check.size==(120,96) and check.format=="PNG"
        assets.append({"id":tid,"name":name,"source_svg":url,"source_filename":source,"source_sha256":sha,"github_path":target.as_posix(),"background_rgb":list(color),"matching":rule,"bytes":target.stat().st_size})
    except Exception as e:
        missing.append({"id":tid,"name":name,"reason":"SVG failed: "+str(e)[:250]})
status={"format":"solid background 120x96 real club crest centered","expected":262,"created":len(assets),"missing_count":len(missing),"victory_flags_created":0,"original_badges":ROOT_REPO,"assets":assets,"missing":missing}
(ROOT/"status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Published",len(assets),"of 262; missing",len(missing),flush=True)
for x in missing:print("MISSING",x["name"],x["reason"],flush=True)
assert len(assets)>150, "Too few high-confidence logos; inspect data before publication"
