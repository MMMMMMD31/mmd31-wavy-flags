#!/usr/bin/env python3
"""Capture 18 x 18 2026–27 Tercera Federación participant names."""
import requests,re,json
from bs4 import BeautifulSoup
from pathlib import Path
URL="https://en.wikipedia.org/wiki/2026%E2%80%9327_Tercera_Federaci%C3%B3n"
soup=BeautifulSoup(requests.get(URL,headers={"User-Agent":"MMD31 roster verification / noncommercial"},timeout=60).text,"html.parser")
groups={}
for table in soup.find_all("table"):
    prev=table.find_previous("h3")
    if prev is None:continue
    m=re.search(r"Group\s+(\d+)\s*[–-]",prev.get_text(" ",strip=True),re.I)
    if not m:continue
    number=int(m.group(1))
    headings=[r.get_text(" ",strip=True).lower() for r in table.find_all("tr",limit=1)]
    if not headings or not re.search(r"\bteam\b",headings[0]) or not re.search(r"\bcity\b",headings[0]):
        continue
    names=[]
    for tr in table.find_all("tr")[1:]:
        cells=tr.find_all(["th","td"],recursive=False)
        if len(cells)<2:continue
        name=cells[0].get_text(" ",strip=True)
        name=re.sub(r"\[\d+\]","",name).strip()
        if name:names.append(name)
    if number not in groups or len(names)>len(groups[number]):
        groups[number]=names
for k in sorted(groups): print(k,len(groups[k]),groups[k][:3],flush=True)
assert set(groups)==set(range(1,19)),f"missing groups {set(range(1,19))-set(groups)}"
assert all(len(z)==18 for z in groups.values()), {k:len(z) for k,z in groups.items()}
assert len({n.casefold() for z in groups.values() for n in z})==324
file=Path("data/spanish_d5_2026_27_roster.json")
file.parent.mkdir(exist_ok=True)
file.write_text(json.dumps({"source":URL,"season":"2026-27","groups":{str(k):v for k,v in sorted(groups.items())}},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("OK: 324 verified named entries",flush=True)
