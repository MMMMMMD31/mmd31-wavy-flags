import requests,re,bs4,os,json
sites={
"aegir":"https://aegirfc.is/",
"grindavik":"https://football-logos.cc/iceland/grindavik/",
"grotta":"https://football-logos.cc/iceland/grotta/",
"leiknir":"https://football-logos.cc/iceland/leiknir-reykjavik/",
"njardvik":"https://umfn.is/ny-asynd-njardvikur/",
"throttur":"https://trottur.is/history/",
"batyr":"https://kpl.kz/club/ekibastuz/",
}
rows=[]
for name,url in sites.items():
 try:
  r=requests.get(url,timeout=25,headers={"User-Agent":"Mozilla/5.0 (CGE badges audit)"});sp=bs4.BeautifulSoup(r.text,"html.parser")
  rows.append("SITE "+name+" http="+str(r.status_code)+" url="+r.url+" bytes="+str(len(r.content)))
  rows += ["META "+str(x)[:450] for x in sp.select('meta[property*="image"], meta[name*="image"]')[:5]]
  rows += ["IMG "+str(x)[:450] for x in sp.select('img')[:30]]
  rows+=["CAND "+str(x)[:450] for x in sp.find_all(["a","link"],href=re.compile(r"\.(?:png|svg|webp)",re.I))[:12]]
 except Exception as e:rows.append("ERROR "+name+" "+str(e)[:250])
 rows.append("-----")
os.makedirs("docs/cge-v7-authentic-badges-20261026",exist_ok=True)
open("docs/cge-v7-authentic-badges-20261026/debug_last7.txt","w",encoding="utf8").write("\n".join(rows)[:60000])
print("SOURCE_SCAN_DONE",len(rows),flush=True)
