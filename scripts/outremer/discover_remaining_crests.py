#!/usr/bin/env python3
"""Audit candidate official club pages without publishing unverified badges."""
import csv, json, re,requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
S={
"1990262000200":["https://ichpeyi-a.com/clubs/","https://www.sportcorico.com/clubs/js-le-marigot"],
"1990262000274":["https://fcligneparadis.footeo.com/","https://www.sportcorico.com/clubs/fc-ligne-paradis"],
"1990262000155":["https://as-montgaillard.footeo.com/","https://www.sportcorico.com/clubs/asc-de-montgaillard"],
"1990262000259":["https://www.sportcorico.com/clubs/as-du-plate"],
"1990262000093":["https://www.sportcorico.com/clubs/aom"],
"1990262000111":["https://www.sportcorico.com/clubs/la-familiale-de-fond-perez","https://lafamilialedefondperez.com/"],
"1990262000121":["https://www.sportcorico.com/clubs/entente-etoile-riveraine"],
"1990262000143":["https://www.sportcorico.com/clubs/us-bellemene-canots"],
"1990262000154":["https://www.sportcorico.com/clubs/as-red-star"],
"1990262000169":["https://www.sportcorico.com/clubs/as-poudriere"],
"1990262000179":["https://www.sportcorico.com/clubs/us-st-elie"],
"1990262000182":["https://www.sportcorico.com/clubs/loya-fc"],
"1990262000186":["https://www.sportcorico.com/clubs/celtic-sa"],
"1990262000203":["https://www.sportcorico.com/clubs/etincelle"],
"1990262000236":["https://www.sportcorico.com/clubs/js-bois-de-nefles"],
"1990262000239":["https://www.sportcorico.com/clubs/asc-labourdonnais"],
"1990262000241":["https://www.sportcorico.com/clubs/jsc-de-la-ravine-creuse"],
"1990262000252":["https://www.sportcorico.com/clubs/as-colimacons"],
"1990262000253":["https://www.sportcorico.com/clubs/ajs-bellemene"],
"1990262000260":["https://www.sportcorico.com/clubs/es-tamponnaise"],
"1990262000264":["https://www.sportcorico.com/clubs/asfc-palmiste"],
"1990262000265":["https://www.sportcorico.com/clubs/a-marmailles-terre-sainte"],
"1990262000276":["https://www.sportcorico.com/clubs/ef-st-pierre"],
"1990262000279":["https://www.sportcorico.com/clubs/fc-plaine-des-gregues"],
"1990262000282":["https://www.sportcorico.com/clubs/vaovao-sport-et-culture"],
"1990262000316":["https://www.commune-moorea.net/culture-loisirs/annuaire-des-associations/associations-sportives/","https://www.theclubindex.com/clubes-emblemas/clube/as-tohie-a-fc-pf"]
}
UA={"User-Agent":"Mozilla/5.0"}
def extract(id,url):
 try:
  r=requests.get(url,timeout=25,headers=UA);r.raise_for_status()
  h=BeautifulSoup(r.content,"html.parser")
  title=h.title.get_text(" ",strip=True)[:90] if h.title else ""
  imgs=[]
  for img in h.select("img"):
   x=next((img.get(n) for n in ("data-src","data-original","src") if img.get(n) and not str(img.get(n)).startswith("data:")),None)
   if not x:continue
   alt=img.get("alt","")
   if "footeo.com" in r.url or "ichpeyi" in r.url or re.search(r"logo|crest|écusson|blason",alt,re.I):
    imgs.append({"alt":alt[:90],"url":urljoin(r.url,x)[:370]})
  return {"id":id,"url":r.url,"status":r.status_code,"title":title,"count":len(imgs),"images":imgs[:40]}
 except Exception as e:return {"id":id,"url":url,"error":str(e)[:100]}
with ThreadPoolExecutor(max_workers=16) as ex:r=list(ex.map(lambda a:extract(*a),[(k,u) for k,urls in S.items() for u in urls]))
Path("audit/outremer-2026-27/lot10_page_images_audit.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
for a in r:print(a["id"],a.get("status",a.get("error")),a.get("title"),a.get("count"),flush=True)
