import requests,re,json,html
from pathlib import Path
url="https://seeklogo.com/vector-logo/643259/associacao-de-futebol-de-ponta-delgada"
r=requests.get(url,timeout=22,headers={"User-Agent":"Mozilla/5.0"});body=html.unescape(r.text)
urls=re.findall(r'(?:(?:https?:)?//)[^\\s\\\"\\\'<>]+',body)
candidates=[u for u in urls if "seeklogo" in u and any(x in u.lower() for x in ["png","image","643259","ponta"])]
out={"status":r.status_code,"url":url,"candidates":list(dict.fromkeys(candidates))[:50],"matched_snippets":[]}
for term in ["643259","ponta-delgada-logo","association","associacao-de-futebol"]:
 m=re.search(re.escape(term),body,re.I)
 if m:out["matched_snippets"].append(body[max(0,m.start()-250):m.end()+700])
p=Path("docs/portugal-gibraltar-clubs-2026-27/competition-logos/probe-afpd.json");p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"status":out["status"],"urls":out["candidates"][:10]},ensure_ascii=False))
