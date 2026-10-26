import requests,bs4,re,json,os
out=[]
for url in ["https://clubelo.com/","https://clubelo.com/Ranking","https://clubelo.com/ByCountry","https://clubelo.com/Liverpool","https://matchdayinsights.com/index.html","https://matchdayinsights.com/about.html"]:
 try:
  r=requests.get(url,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"},timeout=40)
  sp=bs4.BeautifulSoup(r.text,"html.parser")
  out.append({"url":url,"status":r.status_code,"final":r.url,"length":len(r.content),"head":r.text[:300],"scripts":[{"src":x.get("src"),"type":x.get("type"),"head":x.text[:110]} for x in sp.find_all("script")],"forms":[x.get("action") for x in sp.find_all("form")],"links":[a.get("href") for a in sp.select("a[href]")[:30]],"vegaPos":r.text.find("vegaJson"),"sampleVega":r.text[max(0,r.text.find("vegaJson")):r.text.find("vegaJson")+1000] if "vegaJson" in r.text else "","dataRefs":re.findall(r"""[^\s"'<>]+\.(?:json|csv)(?:\?[^\s"'<>]*)?""",r.text)[:50],"scriptSnip":[x.text[:750] for x in sp.find_all("script") if len(x.text)>1000][:5]})
 except Exception as e:out.append({"url":url,"error":str(e)[:300]})
os.makedirs("docs/cge-v11-source-audit",exist_ok=True)
open("docs/cge-v11-source-audit/probe.json","w").write(json.dumps(out,ensure_ascii=False,indent=2)[:120000])
print([(x["url"],x.get("status"),x.get("length"),x.get("error")) for x in out])
