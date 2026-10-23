#!/usr/bin/env python3
"""Probe publicly accessible Italian 2026-27 club logo sources; no automatic club identity assumptions."""
import requests, bs4, unicodedata, re, json, concurrent.futures
from pathlib import Path
from urllib.parse import urljoin
NAMES=["Alessandria","Borgosesia","Lascaris","Fezzanese","Millesimo","Pavonese","Tritium","Fiorenzuola","Nibbiano e Valtidone","LME","Virtus Bolzano","Sandonà","Schio","Arconatese","Solbiatese","Grassina","Rondinella Marzocco","Mezzolara","Montecchio Gallo","Città di Lanciano","Santegidiese","Angelana","Pietralunghese","Ossese","Albalonga","Aranova","Certosa V. Campagnano","Città di Anagni","Venafro","Bisceglie","Brindisi","Flegrea Puteolana","Real Forio","Ebolitana","Gladiator","Licata","Modica","Digiesse Praiatortora"]
assert len(NAMES)==38
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode("ascii").lower()
    return re.sub("-+","-",re.sub(r"[^a-z0-9]+","-",s)).strip("-")
def probe(args):
    name,url=args
    data={"name":name,"url":url}
    try:
        resp=requests.get(url,timeout=18,headers={"User-Agent":"Mozilla/5.0 (compatible; MMD31/1.0; Italian club logo source audit)"})
        data["status"]=resp.status_code
        data["final_url"]=resp.url
        if not resp.ok: return data
        doc=bs4.BeautifulSoup(resp.text,"html.parser")
        data["title"]=doc.title.get_text(" ",strip=True)[:150] if doc.title else ""
        data["headings"]=[x.get_text(" ",strip=True)[:100] for x in doc.select("h1,h2")[:3]]
        images=[]
        for tag in doc.select("img"):
            desc=(" ".join(str(tag.get(a) or "") for a in ("alt","title","class","id"))).lower()
            raw=tag.get("src") or tag.get("data-src") or tag.get("data-lazy-src")
            if not raw:continue
            full=urljoin(resp.url,raw)
            if len(images)<8 or any(w in desc+full.lower() for w in ("logo","stemma","squadra","crest","shield","badge")):
                images.append({"alt":(tag.get("alt") or "")[:80],"src":full[:350],"width":tag.get("width"),"height":tag.get("height")})
        data["images"]=images[:28]
        data["og_images"]=[urljoin(resp.url,m.get("content")) for m in doc.select('meta[property="og:image"]') if m.get("content")]
    except Exception as e:data["error"]=str(e)[:160]
    return data
ALT_SLUGS={
"Pavonese":["pavonese-cigolese","calcio-pavonese"],
"Tritium":["tritium-calcio-1908"],
"Sandonà":["sandona-1922","sandona-calcio"],
"Schio":["calcio-schio"],
"Montecchio Gallo":["k-sport-montecchio-gallo","k-sport-montecchio"],
"Città di Lanciano":["lanciano-fc","lanciano-1920","citta-di-lanciano-fc"],
"Santegidiese":["nuova-santegidiese-1948"],
"Angelana":["asd-angelana","angelana-1930"],
"Pietralunghese":["pol-pietralunghese"],
"Ossese":["polisportiva-ossese"],
"Certosa V. Campagnano":["certosa-vigor-campagnano","certosa"],
"Venafro":["us-venafro"],
"Brindisi":["brindisi-football-club"],
"Real Forio":["real-forio-2014"],
"Licata":["licata-calcio"],
"Modica":["new-modica-calcio"],
}
tasks=[]
for name in NAMES:
    tasks.append((name,"https://www.datasport.it/calcio/squadra/"+slug(name)+".html"))
    tasks.append((name,"https://www.datasport.it/calcio/squadra/"+slug(name).replace("-","")+".html"))
    for alias in ALT_SLUGS.get(name,[]): tasks.append((name,"https://www.datasport.it/calcio/squadra/"+alias+".html"))
tasks.extend([
 ("special LME","https://www.datasport.it/calcio/squadra/lme.html"),
 ("Certosa V. Campagnano","https://www.tuttoseried.com/squadre/certosa-vigor-campagnano/"),
 ("official Lascaris","https://www.lascaris.it"),
 ("official Borgosesia","https://www.borgosesiacalcio.com"),
 ("2026 Serie D squads","https://www.tuttocampo.it/2026-27/Italia/SerieD/GironeH/Squadre"),
 ("sample Tuttocampo","https://www.tuttocampo.it/2023-24/Italia/SerieC/GironeA/Squadra/Alessandria/1009584/Scheda")
])
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    futures=list(pool.map(probe,tasks))
    results=futures
out=Path("docs/italian-clubs-2026-27/research")
out.mkdir(parents=True,exist_ok=True)
(out/"probe.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
for name in NAMES:
    matches=[r for r in results if r["name"]==name and r.get("status")==200]
    print(name, [(r["url"],r.get("title","")[:60],len(r.get("images",[]))) for r in matches])
print("complete",len(results))
