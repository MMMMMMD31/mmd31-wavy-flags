import requests,json,re,concurrent.futures
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import quote
names=["AFC Portchester","Bedfont Sports","Bognor Regis Town","Jersey Bulls","Bowers & Pitsea","Hendon","Guernsey","Newmarket Town","Fakenham Town","Baffins Milton Rovers","AFC Liverpool","AFC Wolverhampton City","AFC Varndeanians","Bracknell Town"]
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 sports history asset provenance research)"})
def check(name):
 res={"name":name}
 for article in [name+" F.C.",name+" A.F.C.",name]:
  url="https://en.wikipedia.org/wiki/"+quote(article.replace(" ","_"))
  try:
   r=s.get(url,timeout=20)
   soup=BeautifulSoup(r.text,"html.parser")
   img=soup.select("table.infobox img")
   res.setdefault("tries",[]).append({"url":url,"status":r.status_code,"length":len(r.content),"title":soup.title.get_text(" ",strip=True) if soup.title else None,"first_images":[{"src":x.get("src"),"alt":x.get("alt")} for x in img[:3]]})
   if r.status_code==200 and img:break
  except Exception as e:res.setdefault("errors",[]).append(str(e)[:120])
 return res
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: out=list(ex.map(check,names))
p=Path("docs/english-v13");p.mkdir(parents=True,exist_ok=True)
(p/"wikipedia_pilot.json").write_text(json.dumps(out,indent=2,ensure_ascii=False))
print(json.dumps(out,ensure_ascii=False)[:10000])
