#!/usr/bin/env python3
"""Source-linked 2026/27 Regional 1 league roster and early-season results."""
import requests,json,concurrent.futures,re,unicodedata
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse,parse_qs,urljoin
S=requests.Session();S.headers["User-Agent"]="Mozilla/5.0 (compatible; MMD31 research for personal simulation)"
BASE=Path(__file__).parent
root="https://thefootdata.com/competitions/regional-1"
base=S.get(root+"?organisme=nouvelle-aquitaine",timeout=30)
base.raise_for_status()
sou=BeautifulSoup(base.text,"html.parser")
leagues={}
for a in sou.find_all("a",href=True):
 url=urljoin(root,a["href"])
 p=parse_qs(urlparse(url).query)
 if not urlparse(url).path.endswith("/regional-1") or not p.get("organisme"):continue
 reg=p["organisme"][0]
 if "poule" not in p:leagues.setdefault(reg,{"name":a.get_text(" ",strip=True),"groups":[]})
print("leagues",len(leagues),list(leagues))
def getleague(kv):
 league,info=kv
 url=root+"?organisme="+league
 try:
  r=S.get(url,timeout=25);r.raise_for_status()
  soup=BeautifulSoup(r.text,"html.parser")
  found={}
  for a in soup.find_all("a",href=True):
   href=urljoin(url,a["href"])
   params=parse_qs(urlparse(href).query)
   if params.get("organisme",[None])[0]!=league:continue
   if "poule" not in params or "saison" not in params:continue
   title=a.get_text(" ",strip=True)
   if not title.lower().startswith(("poule","groupe")):continue
   found[params["poule"][0]]={"label":title,"url":href}
  return league,found,None
 except Exception as e:return league,{},str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 for league,groups,error in pool.map(getleague,leagues.items()):
  leagues[league]["links"]=groups
  if error:leagues[league]["error"]=error
print("groups",sum(len(x.get("links",{})) for x in leagues.values()))
def getgroup(kv):
 league,groupname,info=kv
 url=info["url"]
 try:
  r=S.get(url,timeout=30);r.raise_for_status()
  soup=BeautifulSoup(r.text,"html.parser")
  groups=soup.find_all("table")
  data=[]
  for table in groups:
   header=table.find("thead")
   cols=header.get_text(" ",strip=True).lower() if header else ""
   if not all(x in cols for x in ["pts","équipe"]):continue
   for tr in table.find_all("tr"):
    cells=tr.find_all("td",recursive=False)
    if len(cells)<9:continue
    nums=[]
    for col in cells[:11]:
     text=col.get_text(" ",strip=True)
     text=text.replace("−","-")
     nums.append(text)
    name=nums[1]
    if not name or not nums[0].strip().isdigit():continue
    try:stats={"rank":int(re.sub(r"\D","",nums[0])), "name":name,
           "pts":int(nums[2]),"played":int(nums[3]),"won":int(nums[4]),
           "drawn":int(nums[5]),"lost":int(nums[6]),"gf":int(nums[7]),
           "ga":int(nums[8])}
    except (ValueError,IndexError):continue
    data.append(stats)
   if data:break
  return {"league":league,"group":info["label"],"key":groupname,"url":url,"teams":data,"error":None}
 except Exception as ex:
  return {"league":league,"group":info["label"],"key":groupname,"url":url,"teams":[],"error":str(ex)}
jobs=[(lg,k,val) for lg,info in leagues.items() for k,val in info.get("links",{}).items()]
with concurrent.futures.ThreadPoolExecutor(max_workers=14) as pool:
 groups=list(pool.map(getgroup,jobs))
groups.sort(key=lambda x:(x["league"],x["key"]))
data={"source":root,"as_of":"2026-10-22","leagues":leagues,"groups":groups}
stats={"leagues":len(leagues),"groups":len(groups),"teams":sum(len(x["teams"]) for x in groups),
       "empty":[{"league":g["league"],"group":g["group"],"url":g["url"],"error":g.get("error")} for g in groups if not g["teams"]],
       "sizes":{g["league"]+" "+g["group"]:len(g["teams"]) for g in groups}}
data["stats"]=stats
(BASE/"r1_roster_2026_27.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
print(stats)
