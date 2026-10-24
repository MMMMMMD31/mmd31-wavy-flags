import requests,bs4,json,re
from pathlib import Path
url="https://fkmajevica.com/"
r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=30); soup=bs4.BeautifulSoup(r.text,"html.parser")
imgs=[dict(alt=x.get("alt"),src=x.get("src"),srcset=x.get("srcset"),data_src=x.get("data-src")) for x in soup.find_all("img")]
svgs=[dict(attrs=dict(x.attrs),preview=str(x)[:300]) for x in soup.find_all("svg")][:35]
meta=[dict(attrs=dict(x.attrs)) for x in soup.find_all("meta") if x.get("property","").startswith("og:") or x.get("name")=="twitter:image"]
urls=list(dict.fromkeys(re.findall(r'(?:src=|url\()[\'"]?([^\'" )]+\\.(?:svg|png|jpg|webp))',r.text,re.I)))[:80]
p=Path("docs/balkans-d2-2026/v1/majevica_discovery.json")
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps({"status":r.status_code,"html_size":len(r.content),"images":imgs,"svgs":svgs,"meta":meta,"url_candidates":urls},ensure_ascii=False,indent=2))
print("status",r.status_code,"imgs",len(imgs),"svgs",len(svgs),"meta",len(meta))
