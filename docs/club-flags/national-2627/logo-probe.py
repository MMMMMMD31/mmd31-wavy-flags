import json,requests,re
from bs4 import BeautifulSoup
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0"})
urls=["https://football-logos.cc/france/","https://football-logos.cc/france/uslpv/","https://football-logos.cc/france/fc-bourgoin-jallieu/","https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t=Touraine"]
result={}
for url in urls:
 try:
  r=S.get(url,timeout=30);s=BeautifulSoup(r.text,"html.parser")
  result[url]={"status":r.status_code,"length":len(r.content),"title":s.title.get_text(' ',strip=True) if s.title else "","metas":[{"name":x.get("name"),"property":x.get("property"),"content":(x.get("content") or "")[:210]} for x in s.find_all("meta") if ("image" in str(x).lower())][:12],"images":[{"src":(x.get("src") or "")[:200],"data-src":(x.get("data-src") or "")[:200],"alt":(x.get("alt") or "")[:80]} for x in s.find_all("img")[:10]],"links":[{"href":x.get("href"),"text":x.get_text(" ",strip=True)[:90]} for x in s.find_all("a",href=True) if any(word in x.get_text(" ",strip=True).lower() for word in ["valois","chartres","bourgoin","touraine","alès"])][:20],"scripts":[x.get_text()[:400] for x in s.find_all("script",type="application/ld+json")[:3]]}
 except Exception as exc: result[url]={"error":str(exc)}
with open("docs/club-flags/national-2627/logo-probe.json","w",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
