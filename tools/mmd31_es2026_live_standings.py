#!/usr/bin/env python3
"""Snapshot standings for MMD31 Spain 2026/27, with match counts and goal data."""
from bs4 import BeautifulSoup
import json,requests,time,re
from pathlib import Path
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (MMD31 study / noncommercial sports statistics audit)"})
output=[]
errors=[]
for division,slug,count in [(3,"primera-rfef",2),(4,"segunda-rfef",5),(5,"tercera-rfef",18)]:
 for group in range(1,count+1):
  url=f"https://www.resultadosrfef.es/{slug}/grupo-{group}/clasificacion"
  try:
   response=session.get(url,timeout=35)
   response.raise_for_status()
   html=BeautifulSoup(response.text,"html.parser")
   choices=[]
   for table in html.find_all("table"):
    text=table.get_text(" ",strip=True)
    if not all(x in text for x in ("Pts","PJ","GF","GC")):continue
    rows=[]
    for tr in table.find_all("tr"):
     cells=tr.find_all(["td","th"],recursive=False)
     if len(cells)<9: continue
     values=[x.get_text(" ",strip=True) for x in cells]
     try:
      idx=int(re.search(r"\\d+",values[0]).group())
      name=values[1]
      nums=[int(re.search(r"-?\\d+",v.replace("−","-")).group()) for v in values[2:9]]
      if 1<=idx<=22 and len(name)>=2:
       rows.append({"rank":idx,"name":name,"pts":nums[0],"played":nums[1],"won":nums[2],"drawn":nums[3],"lost":nums[4],"gf":nums[5],"ga":nums[6]})
     except Exception:
      continue
    choices.append(rows)
   best=max(choices,key=len,default=[])
   if len(best)!=({3:20,4:18,5:18}[division]):raise ValueError(f"Expected full table, got sizes {[len(x) for x in choices]} table html {[(t.get_text(' ',strip=True)[:110]) for t in html.find_all('table')][:2]}")
   if len({r["name"] for r in best})!=len(best): raise ValueError("duplicate table names")
   output.append({"division":division,"group":group,"url":url,"rows":best})
   print(f"OK D{division} G{group}: {len(best)}",flush=True)
  except Exception as e:
   errors.append({"division":division,"group":group,"url":url,"error":str(e)})
   print(f"FAILED D{division} G{group}: {e}",flush=True)
  time.sleep(.12)
p=Path("data/mmd31_es2026_live_standings.json")
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps({"source":"resultadosrfef.es (unofficial match data)","snapshot_date":"2026-10-23","groups":output,"errors":errors},ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
assert not errors,f"Only {len(output)}/25 groups loaded"
print("SUCCESS: 25 full tables, 454 entries.",flush=True)
