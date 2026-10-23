#!/usr/bin/env python3
"""Download and inspect candidate Italian lower-league crests; never silently assume logo identity."""
import requests,unicodedata,re,hashlib,json,io,time,concurrent.futures
from collections import Counter
from pathlib import Path
from PIL import Image,ImageOps
BASE=Path("docs/italian-clubs-2026-27/research")
BASE.mkdir(parents=True,exist_ok=True)
CAND=BASE/"candidate-previews"
CAND.mkdir(exist_ok=True)
PROBE=json.loads((BASE/"probe.json").read_text())
NAMES=["Alessandria","Borgosesia","Lascaris","Fezzanese","Millesimo","Pavonese","Tritium","Fiorenzuola","Nibbiano e Valtidone","LME","Virtus Bolzano","Sandonà","Schio","Arconatese","Solbiatese","Grassina","Rondinella Marzocco","Mezzolara","Montecchio Gallo","Città di Lanciano","Santegidiese","Angelana","Pietralunghese","Ossese","Albalonga","Aranova","Certosa V. Campagnano","Città di Anagni","Venafro","Bisceglie","Brindisi","Flegrea Puteolana","Real Forio","Ebolitana","Gladiator","Licata","Modica","Digiesse Praiatortora"]
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode("ascii").lower()
    return re.sub("-+","-",re.sub(r"[^a-z0-9]+","-",s)).strip("-")
OVERRIDES={
 "Borgosesia":["https://www.borgosesiacalcio.com/wp-content/uploads/logo-borgosesiacalcio-colore_fondo-trasparente.png"],
 "Nibbiano e Valtidone":["https://commons.wikimedia.org/wiki/Special:Redirect/file/Escudo_ASD_Nibbiano_%26_Valtidone.png"],
 "Sandonà":["https://img.datasport.it/img/logos/squadre/sandona.png"],
 "Città di Lanciano":["https://img.datasport.it/img/logos/squadre/lanciano.png"],
 "Montecchio Gallo":["https://img.datasport.it/img/logos/squadre/montecchio.png"],
 "Certosa V. Campagnano":["https://img.datasport.it/img/logos/squadre/certosa.png"],
 "Digiesse Praiatortora":["https://img.datasport.it/img/logos/squadre/digiesse-praiatortora.png"],
 "Flegrea Puteolana":["https://img.datasport.it/img/logos/squadre/puteolana.png"],
 "Pietralunghese":["https://img.datasport.it/img/logos/squadre/pietralunghese.png"],
}
def fetch_row(args):
    name,url=args
    d={"name":name,"url":url}
    try:
        r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0 (compatible; MMD31 club crest validator)"})
        d["status"]=r.status_code
        d["final_url"]=r.url
        d["size_bytes"]=len(r.content)
        if not r.ok:return d
        im=Image.open(io.BytesIO(r.content))
        d["format"]=im.format;d["original_size"]=list(im.size)
        if im.width<40 or im.height<40: return d
        im=im.convert("RGBA")
        im.thumbnail((110,88),Image.Resampling.LANCZOS)
        bg=Image.new("RGBA",(120,96),(242,244,248,255))
        bg.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
        pix=im.copy();pix.thumbnail((40,40))
        colors=Counter(pix.getdata())
        d["unique_colors"]=len(colors)
        d["dominant_pixel_fraction"]=round(colors.most_common(1)[0][1]/max(1,pix.width*pix.height),3)
        d["sha256"]=hashlib.sha256(r.content).hexdigest()
        d["alpha_opaque_fraction"]=round(sum(1 for x in pix.getdata() if x[3]>230)/max(1,pix.width*pix.height),3)
        output=CAND/(slug(name)+"-"+d["sha256"][:10]+".png")
        bg.convert("RGB").save(output)
        d["preview_path"]=output.as_posix()
    except Exception as e:d["error"]=str(e)[:140]
    return d
tasks=[]
for name in NAMES:
    source_urls=[]
    for item in PROBE:
        if item["name"]!=name or item.get("status")!=200:continue
        source_urls.extend([x["src"] for x in item.get("images",[]) if x.get("alt","").lower().startswith("logo ") and ("datasport" not in x.get("alt","").lower()) and "img.datasport.it" in x.get("src","")])
    source_urls.extend(OVERRIDES.get(name,[]))
    for s in [slug(name),slug(name).replace("-",""),slug(name).replace("citta-di-",""),slug(name).replace("digiesse-",""),slug(name).replace("virtus-",""),slug(name).replace("flegrea-","")]:
        source_urls.append("https://img.datasport.it/img/logos/squadre/"+s+".png")
    seen=set()
    for url in source_urls:
        if url not in seen:
            tasks.append((name,url));seen.add(url)
with concurrent.futures.ThreadPoolExecutor(max_workers=14) as pool:
    results=list(pool.map(fetch_row,tasks))
(BASE/"probe_images.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
for name in NAMES:
    opts=[x for x in results if x["name"]==name and x.get("format")=="PNG" and x.get("unique_colors",0)>12]
    print(name,len(opts),[(x["url"],x["original_size"],x.get("sha256","")[:10]) for x in opts[:4]])
print("TOTAL",len(tasks),"candidates",sum(x.get("format")=="PNG" for x in results))
