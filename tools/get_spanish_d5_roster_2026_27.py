#!/usr/bin/env python3
"""Document verified Tercera Federación 2026–27 rosters (18x18) with source provenance."""
import requests, re, json
from bs4 import BeautifulSoup
from pathlib import Path
URL="https://en.wikipedia.org/wiki/2026%E2%80%9327_Tercera_Federaci%C3%B3n"
headers={"User-Agent":"MMD31ClubResearch/1.0 (noncommercial simulator; traceability)"}
r=requests.get(URL,headers=headers,timeout=60)
r.raise_for_status()
soup=BeautifulSoup(r.text,"html.parser")
groups={}
for h in soup.select("h3"):
    m=re.match(r"Group\s+(\d+)\s*[–-]",h.get_text(" ",strip=True),re.I)
    if not m:
        continue
    n=int(m.group(1))
    block=[]
    p=h.find_next_sibling()
    while p is not None and p.name not in ("h3","h2"):
        block.append(p)
        p=p.find_next_sibling()
    tables=[]
    for x in block:
        if x.name=="table":
            tables.append(x)
        tables.extend(x.find_all("table"))
    qualifying=[]
    for t in tables:
        header=" ".join(th.get_text(" ",strip=True) for th in t.select("tr:first-child th"))
        if not re.search(r"\bTeam\b",header,re.I) or not re.search(r"\bCity\b",header,re.I):continue
        rows=[]
        for tr in t.select("tr")[1:]:
            td=tr.find_all(["td","th"],recursive=False)
            if len(td)<2:continue
            team=td[0].get_text(" ",strip=True)
            team=re.sub(r"\[\d+\]","",team).strip()
            if team:rows.append(team)
        if len(rows)>=15: qualifying.append(rows)
    if len(qualifying)!=1:
        raise AssertionError(f"group {n}: expected one city/stadium table; got {[len(x) for x in qualifying]}")
    groups[n]=qualifying[0]
    print(f"group {n:02d}: {len(groups[n])}",flush=True)
assert set(groups)==set(range(1,19)),sorted(groups)
assert all(len(x)==18 for x in groups.values()), {k:len(x) for k,x in groups.items()}
assert len({x.casefold() for z in groups.values() for x in z})==324,"Duplicate names"
out=Path("data/spanish_d5_2026_27_roster.json")
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"source":URL,"season":"2026-27","source_type":"Wikipedia reproduced official regional league participant lists (cross-check federation sources)","groups":{str(k):v for k,v in groups.items()}},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("324/324 club names extracted",flush=True)
