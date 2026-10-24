import requests,bs4,json
url="https://escudosfc.com.br/kos.htm"
r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=45)
s=bs4.BeautifulSoup(r.content,"html.parser")
out=[]
for im in s.find_all("img"):
 parent=im.find_parent("td") or im.parent
 parent2=parent.find_parent("tr") if parent else None
 out.append({"alt":im.get("alt"),"title":im.get("title"),"src":im.get("src"),"parent_text":parent.get_text(" ",strip=True)[:140] if parent else "","row_text":parent2.get_text(" ",strip=True)[:180] if parent2 else "","around":str(parent)[:220] if parent else ""})
from pathlib import Path
f=Path("docs/balkans-d2-2026/v1/kosovo_image_discovery.json");f.parent.mkdir(parents=True,exist_ok=True)
f.write_text(json.dumps({"url":url,"status":r.status_code,"images":out},indent=2,ensure_ascii=False))
print(r.status_code,len(out),flush=True)
