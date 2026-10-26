import requests,bs4,html,os,re
u="https://api.thesportsdb.com/season/4914-azerbaijan-first-division/2026-2027"
h={"User-Agent":"Mozilla/5.0 (compatible; MMD31-badge-loader/1.0)"}
try:
 r=requests.get(u,headers=h,timeout=25)
 print("HTTP",r.status_code,"CONTENT",len(r.content),r.url)
 soup=bs4.BeautifulSoup(r.text,"html.parser")
 lines=[]
 for img in soup.find_all("img",src=re.compile("team/badge|thesportsdb"))[:18]:
  par=img
  for _ in range(2):
   if par.parent:par=par.parent
  lines.append("IMAGE:"+str(img)[:280]+"\nPARENT:"+str(par)[:1200])
 os.makedirs("docs/cge-v7-authentic-badges-20261026",exist_ok=True)
 open("docs/cge-v7-authentic-badges-20261026/debug_html.txt","w").write("HTTP "+str(r.status_code)+"\n"+"\n---\n".join(lines)[:15000])
except Exception as e:
 open("docs/cge-v7-authentic-badges-20261026/debug_html.txt","w").write("ERROR "+repr(e))
