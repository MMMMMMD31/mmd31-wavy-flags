#!/usr/bin/env python3
"""MMD31 collection ONLY. No saved game, images, or logos are sent to GitHub."""
import requests,concurrent.futures,datetime,json,re,time
from bs4 import BeautifulSoup
from urllib.parse import parse_qs,urlparse,urljoin
from pathlib import Path
COUNTS={
 "R2":{"auvergne-rhone-alpes":5,"bourgogne-franche-comte":4,"bretagne":6,"centre-val-de-loire":2,"corse":1,"grand-est":7,"hauts-de-france":4,"mediterranee":2,"normandie":4,"nouvelle-aquitaine":6,"occitanie":4,"pays-de-la-loire":4,"paris-ile-de-france":4},
 "R3":{"auvergne-rhone-alpes":10,"bourgogne-franche-comte":7,"bretagne":12,"centre-val-de-loire":4,"corse":1,"grand-est":14,"hauts-de-france":8,"mediterranee":2,"normandie":8,"nouvelle-aquitaine":12,"occitanie":8,"pays-de-la-loire":10,"paris-ile-de-france":4}}
REGIONS={"auvergne-rhone-alpes":"Auvergne-Rhône-Alpes","bourgogne-franche-comte":"Bourgogne-Franche-Comté","bretagne":"Bretagne","centre-val-de-loire":"Centre-Val de Loire","corse":"Corse","grand-est":"Grand Est","hauts-de-france":"Hauts-de-France","mediterranee":"Méditerranée","normandie":"Normandie","nouvelle-aquitaine":"Nouvelle-Aquitaine","occitanie":"Occitanie","pays-de-la-loire":"Pays de la Loire","paris-ile-de-france":"Île-de-France"}
UA={"User-Agent":"Mozilla/5.0 (MMD31 personal football simulation, no automated publishing)"}
ROOT="https://thefootdata.com"
jobs=[]
for div,regions in COUNTS.items():
 for slug,count in regions.items():
  for i in range(1,count+1):
   grp=None if count==1 else chr(64+i)
   url=f"{ROOT}/competitions/regional-{div[-1]}?organisme={slug}&poule=1-{i}&saison=2026"
   jobs.append({"division":div,"region":REGIONS[slug],"group":grp,"group_page_url":url})
assert len(jobs)==153
def get(url):
 for attempt in range(3):
  try:
   resp=requests.get(url,headers=UA,timeout=25);resp.raise_for_status()
   return resp.text
  except Exception:
   if attempt==2:raise
   time.sleep(1.1*(attempt+1))
def parse_group(g):
 out={**g,"teams":[]}
 try:
  soup=BeautifulSoup(get(g["group_page_url"]),"html.parser")
  for table in soup.select("table"):
   th=table.find("thead");heads=th.get_text(" ",strip=True).lower() if th else ""
   if "pts" not in heads or not ("équipe" in heads or "equipe" in heads):continue
   for tr in table.find_all("tr"):
    td=tr.find_all("td",recursive=False)
    if len(td)<9:continue
    rank=td[0].get_text(" ",strip=True)
    if not rank.isdigit():continue
    a=td[1].find("a",href=True)
    if not a:continue
    url=urljoin(ROOT,a["href"])
    key=parse_qs(urlparse(url).query).get("equipe",[None])[0]
    if not key:continue
    def numeric(k):
     try:return int(td[k].get_text(" ",strip=True).replace("−","-").replace("+",""))
     except:return None
    o={"name":a.get_text(" ",strip=True),"source_team_key":key,
       "club_url":url,"rank":int(rank),"pts":numeric(2),"played":numeric(3),
       "won":numeric(4),"draw":numeric(5),"lost":numeric(6),"gf":numeric(7),"ga":numeric(8)}
    out["teams"].append(o)
   if out["teams"]:break
 except Exception as e:out["error"]=str(e)[:250]
 return out
def enrich(p):
 try:
  soup=BeautifulSoup(get(p["club_url"]),"html.parser")
  h=soup.find("h1")
  title=h.get_text(" ",strip=True) if h else None
  m=re.search(r"\bAffiliation\s+(\d{6,7})\b",soup.get_text(" ",strip=True),re.I)
  if not m:raise ValueError("no affiliation in club page")
  p["fff_affiliation"]=m.group(1)
  p["source_short_name"]=p["name"]
  if title:p["name"]=title
  p["source_logo"]=f"https://cdn-transverse.azureedge.net/phlogos/BC{m.group(1)}.jpg"
 except Exception as exc:p["enrichment_error"]=str(exc)[:150]
 return p
print("Fetching",len(jobs),"group pages",flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 groups=list(pool.map(parse_group,jobs))
print("GROUP COUNTS:",len(groups),sum(len(g["teams"]) for g in groups),flush=True)
print("GROUP ERRORS:",[(g["division"],g["region"],g["group"],len(g["teams"]),g.get("error")) for g in groups if len(g["teams"])<8 or len(g["teams"])>18],flush=True)
all_teams=[t for g in groups for t in g["teams"]]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
 teams=list(pool.map(enrich,all_teams))
print("CLUB ENRICH:",sum("fff_affiliation" in p for p in teams),len(teams),flush=True)
from collections import Counter
keys=[p["source_team_key"] for p in teams]
print("DUPLICATE SQUAD KEYS:",[k for k,n in Counter(keys).items() if n>1][:50],flush=True)
data={"season":"2026-2027","source":"TheFootData 2026 group standings and club affiliation",
 "captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "groups":groups}
Path("MMD31_RECHERCHE_R2_R3_2026_2027.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
print("OUTPUT research fixture written",flush=True)
