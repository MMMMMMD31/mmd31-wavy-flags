#!/usr/bin/env python3
from __future__ import annotations
import collections, concurrent.futures, datetime, json, os, re, time
from pathlib import Path
from urllib.parse import urlparse,parse_qs,urljoin
import requests
from bs4 import BeautifulSoup
L=int(os.environ.get("MMD31_DIVISION","6"))
assert L in (6,7,8)
ROOT="https://thefootdata.com"
OUT=Path("district-research");OUT.mkdir(exist_ok=True)
UA={"User-Agent":"Mozilla/5.0 (MMD31 amateur football simulator research)"}
def get(url):
    for i in range(3):
        try:
            r=requests.get(url,headers=UA,timeout=22);r.raise_for_status()
            return BeautifulSoup(r.text,"html.parser")
        except Exception as e:
            if i==2:raise
            time.sleep((i+1)*.5)
def links(soup,url,organisme=None,with_poule=True):
    result={}
    for a in soup.select("a[href]"):
        u=urljoin(url,a["href"]);p=urlparse(u);q=parse_qs(p.query)
        if p.path!=f"/competitions/departemental-{L}":continue
        if bool(q.get("poule"))!=with_poule:continue
        if not q.get("organisme"):continue
        if organisme is not None and q["organisme"][0]!=organisme:continue
        name=a.get_text(" ",strip=True)
        if with_poule and not name.lower().startswith(("poule","groupe")):continue
        result[(q["organisme"][0],q.get("poule",[None])[0])]=(name,u)
    return result
root_url=f"{ROOT}/competitions/departemental-{L}?saison=2026"
root=get(root_url)
districts=[]
if L==8:
    districts=[{"district":"Alsace","district_slug":"alsace","region_source":"Ligue du Grand Est de Football","count":17,"url":root_url}]
else:
    for (slug,_),(name,url) in links(root,root_url,with_poule=False).items():
        m=re.search(r"(\d+)\s+poules?",name,re.I)
        if not m:continue
        header=root.find("a",href=lambda h:h and slug in h)
        heading=header.find_previous("h3") if header else None
        districts.append({"district":name[:m.start()].strip(),"district_slug":slug,
                          "region_source":heading.get_text(" ",strip=True) if heading else None,
                          "count":int(m.group(1)),"url":url})
print("DISTRICTS",L,len(districts),districts,flush=True)
groups=[]
for d in districts:
    soup=root if L==8 else get(d["url"])
    found=links(soup,d["url"],organisme=d["district_slug"],with_poule=True)
    print("GROUP LINKS",L,d["district"],"expected",d["count"],"found",len(found),flush=True)
    for (slug,key),(name,url) in found.items():
        groups.append({**d,"level":L,"group":name,"group_id":key,"group_url":url})
if not groups:raise SystemExit("NO GROUP URLS")
def parse(g):
    result={**g,"teams":[]}
    try:
        soup=get(g["group_url"])
        for table in soup.select("table"):
            th=table.find("thead")
            head=th.get_text(" ",strip=True).lower() if th else ""
            if "pts" not in head or not ("équipe" in head or "equipe" in head):continue
            for tr in table.find_all("tr"):
                td=tr.find_all("td",recursive=False)
                if len(td)<9:continue
                rank=td[0].get_text(" ",strip=True)
                if not rank.isdigit():continue
                a=td[1].find("a",href=True)
                if not a:continue
                url=urljoin(ROOT,a["href"]);p=parse_qs(urlparse(url).query)
                key=p.get("equipe",[None])[0]
                if not key:continue
                def n(i):
                    try:return int(td[i].get_text(" ",strip=True).replace("−","-").replace("+",""))
                    except:return None
                result["teams"].append({"source_name":a.get_text(" ",strip=True),
                  "source_team_key":key,"club_url":url,"rank":int(rank),
                  "pts":n(2),"played":n(3),"won":n(4),"draw":n(5),
                  "lost":n(6),"gf":n(7),"ga":n(8)})
            if result["teams"]:break
    except Exception as e:result["fetch_error"]=str(e)
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
    result=list(pool.map(parse,groups))
all_t=[t for g in result for t in g["teams"]]
print("PARTICIPANTS",L,len(all_t),"GROUPS",len(result),"COUNTS",dict(collections.Counter(len(g["teams"]) for g in result)),flush=True)
def enrich(t):
    try:
        txt=get(t["club_url"]).get_text(" ",strip=True)
        m=re.search(r"\bAffiliation\s+(\d{6,7})\b",txt,re.I)
        if not m:raise ValueError("Missing FFF affiliation")
        return {"fff_affiliation":m.group(1),"source_logo":f"https://cdn-transverse.azureedge.net/phlogos/BC{m.group(1)}.jpg"}
    except Exception as e:return {"identity_error":str(e)}
urls={t["club_url"]:t for t in all_t}
with concurrent.futures.ThreadPoolExecutor(max_workers=17) as pool:
    data=list(pool.map(enrich,urls.values()))
mapping=dict(zip(urls.keys(),data))
for g in result:
    g["teams"]=[{**t,**mapping[t["club_url"]]} for t in g["teams"]]
counts=collections.Counter(x["source_team_key"] for x in all_t)
audit={"division":L,"districts":len(districts),"groups":len(result),
 "participants":len(all_t),"unique_team_keys":len(counts),
 "affiliations_found":sum("fff_affiliation" in mapping[t["club_url"]] for t in all_t),
 "duplicated_source_keys":{k:v for k,v in counts.items() if v>1},
 "problem_groups":[{"district":g["district"],"group":g.get("group"),"size":len(g["teams"]),"error":g.get("fetch_error")} for g in result if not 5<=len(g["teams"])<=20],
 "group_size_counts":dict(collections.Counter(len(g["teams"]) for g in result))}
data={"source":"TheFootData / FFF affiliation","season":"2026-2027","level":L,
 "timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "districts":districts,"stats":audit,"groups":result}
(OUT/f"MMD31_D{L}_2026_2027_PARTICIPANTS_SOURCE.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf8")
(OUT/f"MMD31_D{L}_2026_2027_AUDIT.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf8")
print("AUDIT",json.dumps(audit,ensure_ascii=False)[:3800],flush=True)
