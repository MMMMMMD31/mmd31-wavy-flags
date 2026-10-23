#!/usr/bin/env python3
"""Complete Spanish D5 crest gaps with traceable club-owned and club-specific image sources."""
import json,requests,hashlib,io,re,time
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
from mmd31_es_v13_d5_real_crests import render
s=requests.Session();s.headers["User-Agent"]="MMD31 personal club flag archive / authentic club crests"
EXPLICIT={
 1884500100182:("https://futbolme.com/static/img/club/escudo14082.png","https://futbolme.com/resultados-directo/equipo/cd-lalin/271/calendario/"),
 1884500100185:("https://futbolme.com/static/img/club/escudo4572.png","https://futbolme.com/resultados-directo/equipo/portonovo-sd/540/clasificacion/"),
 1884500100191:("https://andescf.com/images/Escudos/andescf.png","https://andescf.com/ElClub/escudo.php"),
 1884500100235:("https://www.erandioclub.com/imagenes/miequipo/escudo.webp","https://www.erandioclub.com/"),
 1884500100393:("https://atleticosantacruz.es/wp-content/uploads/2026/05/Escudo-Santa-Cruz-2026.png","https://atleticosantacruz.es/"),
 1884500100416:("https://futbolme.com/static/img/club/escudo3258.png","https://futbolme.com/resultados-directo/equipo/ud-montijo/2243/calendario"),
}
LOOKUP={
 1884500100328:"https://futbolme.com/resultados-directo/equipo/malaga-juniors-fc/1034/clasificacion/",
 1884500100321:"https://futbolme.com/resultados-directo/equipo/atletico-de-marbella-balompie/38387/calendario/",
}
def scrape(page):
 r=s.get(page,timeout=35);r.raise_for_status()
 html=BeautifulSoup(r.content,"html.parser")
 for img in html.find_all("img"):
  alt=(img.get("alt","") or "").lower()
  url=requests.compat.urljoin(page,img.get("src") or img.get("data-src") or "")
  if ("escudo" in alt or "escudo" in url) and "static/img/club/escudo" in url:
   return url,page
 raise ValueError("No club-specific crest image, page "+page)
for id_,page in LOOKUP.items():
 try:
  src=scrape(page);EXPLICIT[id_]=src
  print("SOURCE",id_,src,flush=True)
 except Exception as ex:print("NO SOURCE",id_,repr(ex),flush=True)
for id_,(url,page) in EXPLICIT.items():
 g=(id_-1884500100173)//18+1
 p=Path(f"data/mmd31_es_v13_d5_g{g:02d}.json")
 obj=json.loads(p.read_text(encoding="utf-8"))
 row=next(v for v in obj["items"] if v["id"]==id_)
 if row.get("status","").startswith("SOURCE_IMAGE") and (Path("docs/spanish-clubs-2026-27/v13")/(str(id_)+".png")).is_file():
  print("KEEP",id_,row["name"],flush=True);continue
 try:
  r=s.get(url,timeout=35);r.raise_for_status()
  if len(r.content)<400:raise ValueError("source image unexpectedly tiny")
  badge,color=render(r.content)
  out=Path("docs/spanish-clubs-2026-27/v13")/(str(id_)+".png")
  out.parent.mkdir(parents=True,exist_ok=True)
  badge.save(out,"PNG",optimize=True)
  assert Image.open(out).size==(120,96)
  row.update(status="SOURCE_IMAGE_À_VALIDER_VISUELLEMENT",source_image=url,source_team_page=page,
      source_club=row["name"],source_sha256=hashlib.sha256(r.content).hexdigest(),
      background_rgb=color,file_path=out.as_posix(),
      image_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),match_score=100)
  row.pop("reason",None)
  print("CREATED",id_,row["name"],url,flush=True)
 except Exception as e:print("ERROR",id_,row["name"],repr(e),flush=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
