#!/usr/bin/env python3
"""Collect the REAL district D1-D8 hierarchy and D1 2026/27 rosters.
Do not invent missing divisions/groups/clubs. GitHub artifact ONLY.
"""
from __future__ import annotations
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
import concurrent.futures
import datetime
import os
import json
import re
import requests
import time
from urllib.parse import parse_qs, urljoin, urlparse
from pathlib import Path
ROOT="https://thefootdata.com"
UA={"User-Agent":"Mozilla/5.0 (MMD31 source-linked football database audit)"}
OUT=Path("district-research")
OUT.mkdir(exist_ok=True)

def get(url):
    error=None
    for i in range(3):
        try:
            r=requests.get(url,headers=UA,timeout=35);r.raise_for_status()
            return BeautifulSoup(r.text,"html.parser")
        except Exception as e:
            error=e;time.sleep((i+1)*.5)
    raise error

def catalog(level):
    url=f"{ROOT}/competitions/departemental-{level}?saison=2026"
    soup=get(url)
    data=[]
    for a in soup.select("a[href]"):
        h=urljoin(url,a["href"]);p=urlparse(h);args=parse_qs(p.query)
        if p.path!=f"/competitions/departemental-{level}":continue
        if not args.get("organisme"):continue
        if args.get("poule"):continue
        name=a.get_text(" ",strip=True)
        matched=re.search(r"(?P<n>\d+)\s*poules?",name,re.I)
        if not matched:continue
        region_tag=a.find_previous("h3")
        region=region_tag.get_text(" ",strip=True) if region_tag else None
        district_name=name[:matched.start()].strip()
        data.append({"district":district_name,"district_slug":args["organisme"][0],
                    "region":region,"declared_group_count":int(matched["n"]),"url":h})
    dedup={x["district_slug"]:x for x in data}
    print(f"CATALOG D{level}: {len(dedup)} districts, {sum(v['declared_group_count'] for v in dedup.values())} groups",flush=True)
    return {"level":level,"url":url,"districts":list(dedup.values())}

def district_groups(args):
    level, district=args
    url=district["url"]
    soup=get(url)
    groups=[]
    for a in soup.select("a[href]"):
        href=urljoin(url,a["href"]);p=urlparse(href);q=parse_qs(p.query)
        if p.path!=f"/competitions/departemental-{level}":continue
        if q.get("organisme",[None])[0]!=district["district_slug"]:continue
        if not q.get("poule"):continue
        label=a.get_text(" ",strip=True)
        if not label.lower().startswith(("poule","groupe")):continue
        groups.append((q["poule"][0], label,href))
    groups=list({k:(k,title,href) for k,title,href in groups}.values())
    if groups and len(groups)!=district["declared_group_count"]:
        print("NAVIGATION COUNT DIFF",district["district_slug"],
            district["declared_group_count"],len(groups),flush=True)
    if not groups:
        if district["declared_group_count"]!=1:
            raise ValueError(f"missing group links for {district}")
        groups=[("single",None,url)]
    out=[]
    for key,title,href in groups:
        out.append({"level":level,"district":district["district"],"district_slug":district["district_slug"],
            "region_source":district["region"],"group_id":key,
            "group":title if len(groups)>1 else None,
            "group_url":href})
    return out

def parse_group(group):
    page=get(group["group_url"])
    found=[]
    for table in page.select("table"):
        thead=table.find("thead")
        headers=thead.get_text(" ",strip=True).lower() if thead else ""
        if "pts" not in headers or not ("équipe" in headers or "equipe" in headers):
            continue
        for row in table.find_all("tr"):
            tds=row.find_all("td",recursive=False)
            if len(tds)<9:continue
            rank=tds[0].get_text(" ",strip=True)
            if not rank.isdigit():continue
            a=tds[1].find("a",href=True)
            if a is None:continue
            u=urljoin(ROOT,a["href"])
            key=parse_qs(urlparse(u).query).get("equipe",[None])[0]
            if not key:continue
            def num(i):
                try:return int(tds[i].get_text(" ",strip=True).replace("−","-").replace("+",""))
                except:return None
            found.append({"source_name":a.get_text(" ",strip=True),
                "source_team_key":key,"club_url":u,
                "rank":int(rank),"pts":num(2),"played":num(3),
                "won":num(4),"draw":num(5),"lost":num(6),
                "gf":num(7),"ga":num(8)})
        if found:break
    return {**group,"teams":found}

def get_affiliation(row):
    out=dict(row)
    try:
        soup=get(row["club_url"])
        text=soup.get_text(" ",strip=True)
        m=re.search(r"\bAffiliation\s+(\d{6,7})\b",text,re.I)
        if not m: raise ValueError("No FFF affiliation number in club page")
        out["fff_affiliation"]=m.group(1)
        out["source_logo"]=f"https://cdn-transverse.azureedge.net/phlogos/BC{m.group(1)}.jpg"
    except Exception as e:
        out["identity_issue"]=str(e)[:160]
    return out

def main():
    level=int(os.environ.get("MMD31_DIVISION","3"))
    assert level in (3,4,5)
    cat=catalog(level)
    catalog_meta={"season":"2026-2027","captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "source":"TheFootData","catalog":cat}
    (OUT/f"MMD31_D{level}_2026_2027_CATALOG.json").write_text(json.dumps(catalog_meta,ensure_ascii=False,indent=2),encoding="utf-8")
    groups=[]
    jobs=[(level,d) for d in cat["districts"]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=18) as pool:
        futures={pool.submit(district_groups,j):j for j in jobs}
        for fut in concurrent.futures.as_completed(futures):
            try:groups.extend(fut.result())
            except Exception as e:print("GROUP_DISCOVERY_ERROR",futures[fut][1]["district"],str(e),flush=True)
    print("GROUP_COUNT",level,len(groups),"catalog announced",sum(d["declared_group_count"] for d in cat["districts"]),flush=True)
    # Some catalog entries may be duplicated, but never add a group without source evidence.
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
        futures={pool.submit(parse_group,g):g for g in groups}
        expanded=[];errors=[]
        for fut in concurrent.futures.as_completed(futures):
            try: expanded.append(fut.result())
            except Exception as e: errors.append({"group":futures[fut],"error":str(e)})
    expanded.sort(key=lambda g:(g["district_slug"],g["group_id"]))
    all_teams=[t for g in expanded for t in g["teams"]]
    print("PARTICIPATIONS",level,len(all_teams),"errors",len(errors),flush=True)
    if len(all_teams)<400:raise SystemExit("too few participants, source likely broken")
    # Club affiliation identity fetched per club URL, cache by URL; squad keys stay distinct.
    byurl={t["club_url"]:t for t in all_teams}
    print("UNIQUE CLUB PAGE URLS",len(byurl),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=28) as pool:
        futures={pool.submit(get_affiliation,t):url for url,t in byurl.items()}
        filled={}
        for idx,fut in enumerate(concurrent.futures.as_completed(futures)):
            filled[futures[fut]]=fut.result()
            if (idx+1)%700==0:print("AFFILIATION",level,idx+1,len(byurl),flush=True)
    for g in expanded:
        g["teams"]=[filled[t["club_url"]] for t in g["teams"]]
    enriched=[t for g in expanded for t in g["teams"]]
    keys=Counter(x["source_team_key"] for x in enriched)
    report={"division":level,"districts":len(cat["districts"]),"catalog_groups":sum(x["declared_group_count"] for x in cat["districts"]),
        "discovered_groups":len(expanded),"participants":len(enriched),"unique_team_keys":len(keys),
        "affiliation_found":sum("fff_affiliation" in x for x in enriched),
        "missing_affiliation":sum("fff_affiliation" not in x for x in enriched),
        "duplicates":{k:n for k,n in keys.items() if n>1},
        "undersized_or_empty_groups":[{"district":g["district"],"group":g["group"],"url":g["group_url"],"team_count":len(g["teams"])} for g in expanded if not 6<=len(g["teams"])<=20],
        "fetch_errors":errors,"group_sizes":dict(Counter(len(g["teams"]) for g in expanded))}
    research={"season":"2026-2027","source":"TheFootData / linked FFF affiliations",
              "captured_at":catalog_meta["captured_at"],"stats":report,"groups":expanded}
    (OUT/f"MMD31_D{level}_2026_2027_PARTICIPANTS_SOURCE.json").write_text(json.dumps(research,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT/f"MMD31_D{level}_2026_2027_AUDIT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("FINAL AUDIT",level,json.dumps(report,ensure_ascii=False)[:4000],flush=True)

if __name__=="__main__":
    main()
