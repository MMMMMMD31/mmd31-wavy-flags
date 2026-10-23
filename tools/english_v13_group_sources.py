import json,requests,re
from bs4 import BeautifulSoup
from pathlib import Path
urls={
"southern_combination":"https://www.horshamymfc.co.uk/leaguetable/1131/113",
"north_west_counties":"https://nwcfl.com/",
"western":"https://en.wikipedia.org/wiki/2026%E2%80%9327_Western_Football_League",
"wessex":"https://en.wikipedia.org/wiki/2026%E2%80%9327_Wessex_Football_League",
"midland":"https://en.wikipedia.org/wiki/2026%E2%80%9327_Midland_Football_League",
}
data={}
for n,u in urls.items():
 try:
  r=requests.get(u,headers={"User-Agent":"Mozilla/5.0 MMD31 personal 2026/27 performance research"},timeout=32)
  soup=BeautifulSoup(r.text,"html.parser")
  tabs=[]
  for t in soup.select("table"):
   trs=t.select("tr")
   if len(trs)<12:continue
   rows=[[c.get_text(" ",strip=True) for c in tr.find_all(["th","td"],recursive=False)] for tr in trs[:50]]
   tabs.append({"rows":len(trs),"heading":t.find_previous(["h2","h3","h4"]).get_text(" ",strip=True) if t.find_previous(["h2","h3","h4"]) else "","preview":rows[:36]})
  data[n]={"url":u,"status":r.status_code,"title":soup.title.get_text(" ",strip=True) if soup.title else "","tables":tabs[:8]}
  print(n,r.status_code,"tables",len(tabs),flush=True)
 except Exception as e:data[n]={"url":u,"error":str(e)[:150]}
p=Path("docs/english-v13");p.mkdir(exist_ok=True,parents=True)
(p/"missing_group_tables.json").write_text(json.dumps(data,ensure_ascii=False,indent=2))
