#!/usr/bin/env python3
import requests,bs4,json,urllib.parse
PAGES={
 "FFK historical":"https://www.ffk-ks.com/superliga/",
 "FFK new":"https://ffk-kosova.com/garat/Albi-Mall-superliga",
 "Kosovo competition":"https://globalsportsarchive.com/en/soccer/competition/albi-mall-superliga-2026-2027/80425/",
 "Bosnia competition":"https://www.nfsbih.ba/vijesti/nogomet-m/wwin-liga-bih/wwin-liga-bosne-i-hercegovine-2026-27/",
 "FK BSK":"https://en.wikipedia.org/wiki/FK_BSK_Banja_Luka",
}
result={}
for name,url in PAGES.items():
 try:
  r=requests.get(url,timeout=30,headers={"User-Agent":"Mozilla/5.0"}); soup=bs4.BeautifulSoup(r.text,"html.parser")
  images=[]
  for tag in soup.find_all("img"):
   alt=(tag.get("alt") or tag.get("title") or "").strip()
   src=(tag.get("data-src") or tag.get("src") or "").strip()
   if src and not src.startswith("data:"):
    images.append({"alt":alt,"src":urllib.parse.urljoin(url,src),"class":" ".join(tag.get("class",[]))})
  result[name]={"status":r.status_code,"title":soup.title.get_text(" ",strip=True) if soup.title else "", "images":images[:320], "html_bytes":len(r.content)}
 except Exception as e:result[name]={"error":str(e)}
import pathlib
p=pathlib.Path("docs/balkans-d1-2026/v1");p.mkdir(parents=True,exist_ok=True)
(p/"discovery.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print({k:(v.get("status"),len(v.get("images",[])),v.get("error")) for k,v in result.items()})
