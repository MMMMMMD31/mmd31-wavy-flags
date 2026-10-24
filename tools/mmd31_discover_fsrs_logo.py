import requests,bs4,json,re
from pathlib import Path
url="https://fsrs.org/sr-BA/takmicenja-prva-liga.html"
r=requests.get(url,timeout=30,headers={"User-Agent":"Mozilla/5.0"})
s=bs4.BeautifulSoup(r.content,'html.parser')
res=[]
for el in s.find_all('img'):
 p=el.parent
 res.append({"src":el.get("src"),"alt":el.get("alt"),"parent":p.get_text(" ",strip=True)[:90] if p else "","outer":str(p)[:350] if p else ""})
srcs=re.findall(r'["\']([^"\']*(?:majevica|majев|мајев)[^"\']*\\.(?:png|jpg|svg|webp))["\']',r.text,re.I)
p=Path("docs/balkans-d2-2026/v1/fsrs_logo_discovery.json");p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps({"status":r.status_code,"images":res,"related_paths":srcs},ensure_ascii=False,indent=2))
print("STATUS",r.status_code,"IMAGES",len(res),"RELATED",srcs[:12],flush=True)
