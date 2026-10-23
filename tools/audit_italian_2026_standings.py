#!/usr/bin/env python3
import requests,bs4,json,time,re
from pathlib import Path
DOMAINS={"A":"matera","B":"aosta","C":"napoli","D":"roma","E":"www","F":"roma","G":"www","H":"potenza","I":"bat"}
results={}
for i,g in enumerate("ABCDEFGHI",start=20):
  candidates=[f"https://{DOMAINS[g]}.iamcalcio.it/classifiche/{i}/serie-d-girone-{g.lower()}/2026-2027.html",
              f"https://www.iamcalcio.it/classifiche/{i}/serie-d-girone-{g.lower()}/2026-2027.html",
              f"https://roma.iamcalcio.it/classifiche/{i}/serie-d-girone-{g.lower()}/2026-2027.html"]
  reports=[]
  for url in dict.fromkeys(candidates):
    try:
      r=requests.get(url,timeout=23,headers={"User-Agent":"Mozilla/5.0 MMD31-2026-Italy-audit"});r.raise_for_status()
      page=bs4.BeautifulSoup(r.text,"html.parser")
      tables=[]
      for tb in page.find_all("table"):
        rows=[[cell.get_text(" ",strip=True) for cell in tr.find_all(["td","th"])] for tr in tb.find_all("tr")]
        rows=[row for row in rows if row]
        summary=" ".join(" ".join(row) for row in rows[:2]).lower()
        if len(rows)>=18 and (("gf" in summary and "gs" in summary) or ("gol fatti" in summary and "gol subiti" in summary)):
          tables.append(rows[:27])
      reports.append({"url":url,"status":r.status_code,"title":page.title.get_text(" ",strip=True) if page.title else "","tables":tables})
      if tables and any(len(x)>=19 for x in tables):break
    except Exception as e:reports.append({"url":url,"error":str(e)[:160]})
  results[g]=reports
  print(g,[(x.get("status"),len(x.get("tables",[])),[len(y) for y in x.get("tables",[])],x.get("url")) for x in reports],flush=True)
target=Path("docs/italian-clubs-2026-27/research")
target.mkdir(parents=True,exist_ok=True)
(target/"rating-standings-2026-10-23.json").write_text(json.dumps(results,ensure_ascii=False,indent=1)+"\n")
assert sum(1 for g in results if any(x.get("tables") for x in results[g]))>=7
