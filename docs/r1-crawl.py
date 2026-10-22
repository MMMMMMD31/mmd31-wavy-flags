#!/usr/bin/env python3
import requests,bs4,json,re,concurrent.futures,unicodedata,collections,time
ROOT="https://statfootballclubfrance.fr/"
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (MMD31 football rosters research)"})
def pull_region(idx):
 u=ROOT+f"identifiant-championnat.php?id={idx}&type=regional"
 try:
  r=session.get(u,timeout=18)
  if r.status_code!=200:return {"index":idx,"status":r.status_code}
  s=bs4.BeautifulSoup(r.text,"html.parser")
  title=s.title.get_text(" ",strip=True) if s.title else ""
  hdr=[h.get_text(" ",strip=True) for h in s.select("h1,h2")[:5]]
  cand=[]
  for link in s.select("a[href]"):
   if "2026-2027"!=link.get_text(" ",strip=True):continue
   href=link.get("href")
   if "championnat.php" not in href:continue
   cand.append(href)
  if not cand:return {"index":idx,"title":title,"headers":hdr,"candidates":[]}
  u2=requests.compat.urljoin(ROOT,cand[0]);r2=session.get(u2,timeout=22)
  s2=bs4.BeautifulSoup(r2.text,"html.parser")
  rtitle=s2.title.get_text(" ",strip=True) if s2.title else ""
  g=[]
  for i,table in enumerate(s2.select("table")):
   teams=[]
   for tr in table.select("tr"):
    cols=[e.get_text(" ",strip=True) for e in tr.select("td,th")]
    if len(cols)<7 or not re.fullmatch(r"\d+",cols[0]):continue
    if not cols[1] or cols[1].lower().startswith("equipe"):continue
    def toint(s):
     try:return int(s.replace("\u2212","-").replace("+","").replace(" ",""))
     except:return None
    pts,j,w,d,l,gf,ga=(toint(v) for v in cols[2:9])
    teams.append({"rank":toint(cols[0]),"name":cols[1],"pts":pts,"played":j,"w":w,"d":d,"l":l,"gf":gf,"ga":ga})
   if teams:g.append({"group":chr(65+i) if len(s2.select("table"))>1 else "A","teams":teams})
  return {"index":idx,"title":title,"headers":hdr,"candidates":cand[:4],"url":u2,"urlTitle":rtitle,"status":r2.status_code,"groups":g}
 except Exception as ex:return {"index":idx,"error":str(ex)[:250]}
all_rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for out in pool.map(pull_region,range(1,30)):
  all_rows.append(out)
regions=[x for x in all_rows if x.get("groups")]
res={"date":"2026-10-22","source":"statfootballclubfrance.fr 2026-27 regional league results","regions":regions,"probes":all_rows,
"summary":{"regions":len(regions),"groups":sum(len(x["groups"]) for x in regions),
"positions":sum(len(group["teams"]) for x in regions for group in x["groups"])}}
with open("docs/r1-2026-27-roster.json","w",encoding="utf-8") as f:json.dump(res,f,ensure_ascii=False,indent=2)
print("R1",res["summary"])
for x in regions:print(x["index"],x["title"],x["urlTitle"],len(x["groups"]),[len(y["teams"]) for y in x["groups"]])
