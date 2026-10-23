#!/usr/bin/env python3
"""Find the *real* Ligue Corse Régionale 4 roster for 2026-27.
Technical research only; do not create fake clubs or logos if not source-confirmed."""
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse,parse_qs
import requests,json,re,concurrent.futures
from pathlib import Path
BASE="https://thefootdata.com"
U=f"{BASE}/competitions/regional-4?organisme=corse&saison=2026"
def soup(url):
 r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=25)
 r.raise_for_status()
 return BeautifulSoup(r.text,"html.parser")
root=soup(U)
poules={}
for a in root.select("a[href]"):
 u=urljoin(U,a["href"]);parsed=urlparse(u);q=parse_qs(parsed.query)
 if parsed.path!="/competitions/regional-4":continue
 if q.get("organisme",[None])[0]!="corse":continue
 if q.get("poule"):
  label=a.get_text(" ",strip=True)
  if label.lower().startswith(("poule","groupe")):
   poules[q["poule"][0]]=u
print("POULE LINKS",poules,flush=True)
if not poules:
 poules["1-1"]=f"{BASE}/competitions/regional-4?organisme=corse&poule=1-1&saison=2026"
groups=[]
for pk,u in poules.items():
 pg=soup(u)
 roster=[]
 for table in pg.select("table"):
  th=table.find("thead")
  hdr=th.get_text(" ",strip=True).lower() if th else ""
  if "pts" not in hdr or "équipe" not in hdr and "equipe" not in hdr:continue
  for tr in table.select("tr"):
   td=tr.find_all("td",recursive=False)
   if len(td)<9 or not td[0].get_text(" ",strip=True).isdigit():continue
   a=td[1].find("a",href=True)
   if not a:continue
   name=a.get_text(" ",strip=True)
   url=urljoin(BASE,a["href"])
   key=parse_qs(urlparse(url).query).get("equipe",[None])[0]
   if not key:continue
   def num(i):
    try:return int(td[i].get_text(" ",strip=True).replace("−","-"))
    except:return None
   roster.append({"name":name,"squad_key":key,"club_url":url,"rank":num(0),
      "pts":num(2),"played":num(3),"won":num(4),"draw":num(5),"lost":num(6),"gf":num(7),"ga":num(8)})
  if roster:break
 print("GROUP",pk,"TEAMS",len(roster),flush=True)
 if len(roster)<8:raise SystemExit(f"No credible Corsican R4 team roster in {u}")
 groups.append({"group_key":pk,"source_url":u,"teams":roster})
def aff(r):
 try:
  m=re.search(r"\bAffiliation\s+(\d{6,7})\b",soup(r["club_url"]).get_text(" ",strip=True),re.I)
  if not m:raise ValueError("missing FFF affiliation")
  return {"fff_affiliation":m.group(1),"crest_source":f"https://cdn-transverse.azureedge.net/phlogos/BC{m.group(1)}.jpg"}
 except Exception as e:return {"problem":str(e)}
entries=[x for g in groups for x in g["teams"]]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
 results=list(pool.map(aff,entries))
for r,detail in zip(entries,results):r.update(detail)
out={"season":"2026-2027","region":"Corse","division":"R4","groups":groups,
 "squads":len(entries),"unique_keys":len({x["squad_key"] for x in entries}),
 "identified_affiliations":sum("fff_affiliation" in x for x in entries)}
Path("mmd31_corse_r4_roster_source_2026_27.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("FINAL",out["squads"],out["unique_keys"],out["identified_affiliations"])
