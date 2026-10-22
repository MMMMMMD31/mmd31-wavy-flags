import requests,bs4,json,re,concurrent.futures
urls=[
"https://statfootballclubfrance.fr/identifiant-championnat.php?id=11&type=regional",
"https://www.statfootballclubfrance.fr/championnat.php?id=4130",
"https://statfootballclubfrance.fr/championnat.php?id=4140",
"https://www.statfootballclubfrance.fr/championnat.php?id=4140"
]
sess=requests.Session();sess.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 2026-2027 regional football research)"})
out={}
for u in urls:
 try:
  r=sess.get(u,timeout=16)
  s=bs4.BeautifulSoup(r.text,"html.parser")
  trs=[]
  for tr in s.select("tr")[:12]:
   v=[x.get_text(" ",strip=True) for x in tr.select("td,th")]
   if v:trs.append(v)
  links=[(a.get_text(" ",strip=True),a.get("href")) for a in s.select("a[href]") if "2026" in a.get_text(" ",strip=True) or "Régional 1" in a.get_text(" ",strip=True)][:25]
  out[u]={"status":r.status_code,"url":r.url,"chars":len(r.text),"title":s.title.get_text(" ",strip=True) if s.title else None,"headings":[h.get_text(" ",strip=True) for h in s.select("h1,h2,h3")[:16]],"links":links,"tables":len(s.find_all("table")),"tableSamples":trs,"textSample":s.get_text(" ",strip=True)[:800]}
 except Exception as ex:out[u]={"error":str(ex)}
open("docs/r1-probe.json","w").write(json.dumps(out,ensure_ascii=False,indent=2))
