import json,re,requests
from bs4 import BeautifulSoup
from pathlib import Path
urls={
"north":"https://www.footballwebpages.co.uk/national-league-north/league-table",
"east":"https://www.footballwebpages.co.uk/northern-premier-league-east-division/league-table",
"combined":"https://www.footballwebpages.co.uk/combined-counties-league-premier-division-north/league-table",
"istm":"https://www.footballwebpages.co.uk/isthmian-football-league-north-division/league-table",
"midland":"https://www.footballwebpages.co.uk/midland-football-league-premier-division/league-table"
}
results={}
for k,url in urls.items():
 try:
  r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0 (compatible; research for personal historical football simulations)"})
  soup=BeautifulSoup(r.text,"html.parser")
  tb=soup.select("table")
  items=[]
  for t in tb[:5]:
   tr=t.select("tr")
   items.append({"rows":len(tr),"attrs":dict(t.attrs),"sample":[row.get_text(" | ",strip=True)[:300] for row in tr[:3]]})
  h=soup.find(string=re.compile("League Table",re.I))
  links=[{"text":a.get_text(" ",strip=True),"href":a.get("href")} for a in soup.select("a[href]") if "premier" in a.get_text(" ",strip=True).lower()][:6]
  results[k]={"url":url,"status":r.status_code,"size":len(r.content),"title":soup.title.get_text(" ",strip=True) if soup.title else None,"tables":items,"links":links,"sample_text":soup.get_text(" ",strip=True)[-500:]}
 except Exception as e:results[k]={"error":str(e)}
p=Path("docs/english-ratings-research");p.mkdir(parents=True,exist_ok=True)
(p/"diagnostic.json").write_text(json.dumps(results,indent=2,ensure_ascii=False))
print(json.dumps(results,indent=2,ensure_ascii=False))
