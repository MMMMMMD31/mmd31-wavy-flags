import requests,json,re
from bs4 import BeautifulSoup
from pathlib import Path
urls={
"nonleagueranking_club":"https://www.nonleagueranking.com/clubpage.php?Club=485",
"nonleagueranking_home":"https://www.nonleagueranking.com/",
"nonleagueranking_clubs":"https://www.nonleagueranking.com/ranking.php",
"tsdb_fakenham":"https://www.thesportsdb.com/api/v1/json/123/searchteams.php?t=Fakenham%20Town",
"tsdb_winsford":"https://www.thesportsdb.com/api/v1/json/123/searchteams.php?t=Winsford%20United",
"footballwebpages":"https://www.footballwebpages.co.uk/combined-counties-league-premier-division-north/league-table",
"globalsports":"https://globalsportsarchive.com/en/soccer/team/windsor--eton-fc/70752/"
}
out={}
for name,url in urls.items():
 try:
  r=requests.get(url,timeout=25,headers={"User-Agent":"Mozilla/5.0 (compatible; MMD31 club badge history research)"})
  soup=BeautifulSoup(r.text,"html.parser")
  imgs=soup.select("img")
  links=soup.select("a[href]")
  out[name]={"url":url,"status":r.status_code,"length":len(r.content),"title":soup.title.get_text(" ",strip=True) if soup.title else None,"images":[{"alt":x.get("alt"),"src":x.get("src"),"data-src":x.get("data-src"),"class":x.get("class")} for x in imgs[:35]],"club_links":[{"name":a.get_text(" ",strip=True),"href":a.get("href")} for a in links if any(v in (a.get("href") or "").lower() for v in ("clubpage","team"))][:30],"sample":r.text[:350] if name.startswith("tsdb") else ""}
 except Exception as e:out[name]={"error":str(e)}
p=Path("docs/english-v13");p.mkdir(exist_ok=True,parents=True)
(p/"alternate_image_sources.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False)[:11000])
