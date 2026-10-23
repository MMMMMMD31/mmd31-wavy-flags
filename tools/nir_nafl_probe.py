import requests,bs4,json,re
from pathlib import Path
ROOT=Path("docs/nir-clubs-2026-27/v1")
ROOT.mkdir(parents=True,exist_ok=True)
results=[]
for page in ["https://www.thenafl.co.uk/fixtures","https://www.thenafl.co.uk/tables","https://www.thenafl.co.uk/results","https://midulsterfootballleague.co.uk/clubdetails-b/"]:
  item={"page":page}
  try:
    r=requests.get(page,timeout=25,headers={"User-Agent":"Mozilla/5.0"})
    item["status"]=r.status_code
    item["length"]=len(r.content)
    s=bs4.BeautifulSoup(r.text,"html.parser")
    item["imgs"]=[{"alt":i.get("alt",""),"src":i.get("src"),"data_src":i.get("data-src")} for i in s.select("img")][:250]
    item["scripts"]=[x.get("src") for x in s.select("script[src]")][-15:]
    item["snippets"]=[re.sub(r"\s+"," ",r.text[max(0,m.start()-220):m.end()+280]) for m in list(re.finditer("Dunmurry|Portstewart|Aquinas|Abbey Villa",r.text,re.I))[:4]]
  except Exception as e:item["error"]=str(e)[:200]
  results.append(item)
for url in ["https://www.thenafl.co.uk/script.js","https://www.thenafl.co.uk/division-themes.js","https://www.thenafl.co.uk/components/navbar.js"]:
    item={"page":url}
    try:
        r=requests.get(url,timeout=25,headers={"User-Agent":"Mozilla/5.0"})
        item["status"]=r.status_code;item["length"]=len(r.content)
        txt=r.text
        item["strings"]=[x for x in re.findall(r"""['"]([^'"\n]{1,180})['"]""",txt) if any(z in x.lower() for z in ("api/","json","badge","logo","/assets","/media","/uploads","teams","clubs","fixtures","/img/"))][:120]
        item["src"]=[txt[max(0,m.start()-250):m.end()+270] for m in list(re.finditer("badge|logo|\\.json|api/|team_image",txt,re.I))[:50]]
    except Exception as e:item["error"]=str(e)[:200]
    results.append(item)
for url in ["https://www.thenafl.co.uk/data/tables.json","https://www.thenafl.co.uk/data/clubs-dev.json","https://www.thenafl.co.uk/data/fixtures.json"]:
    item={"page":url}
    try:
        r=requests.get(url,timeout=25,headers={"User-Agent":"Mozilla/5.0"})
        item["status"]=r.status_code;item["length"]=len(r.content)
        obj=r.json()
        item["shape"]=str(obj)[:4500]
        item["keys"]=list(obj.keys()) if isinstance(obj,dict) else None
        if isinstance(obj,dict):
            for key,val in obj.items():
                item.setdefault("examples",[]).append({"key":key,"type":type(val).__name__,"len":len(val) if hasattr(val,"__len__") else None,"head":str(val)[:400]})
    except Exception as e:item["error"]=str(e)[:200]
    results.append(item)
for url in ["https://www.europlan-online.de/index.php?id=2675&s=liga","https://www.europlan-online.de/index.php?land=54&s=fehlendebilder","https://bpfl.leaguerepublic.com/index.html"]:
    item={"page":url}
    try:
        r=requests.get(url,timeout=22,headers={"User-Agent":"Mozilla/5.0"})
        item["status"]=r.status_code;item["length"]=len(r.content)
        soup=bs4.BeautifulSoup(r.text,"html.parser")
        tags=soup.select("img")
        item["imgs"]=[{"alt":i.get("alt",""),"src":i.get("src"),"data_src":i.get("data-src"),"parent":i.parent.parent.get_text(" ",strip=True)[:150] if i.parent and i.parent.parent else ""} for i in tags if i.get("alt") or i.get("src")][:140]
    except Exception as e:item["error"]=str(e)[:180]
    results.append(item)
for url in ["https://www.pitchero.com/clubs/trojansyouthcommunitygroup","https://www.teamstats.net/team/football/trojans-ycg-derry","https://www.juniorgrassrootshub.com/clubs/trojans-ycg-colts-u11-d-and-d","https://38trojansycg.co.uk"]:
    item={"page":url}
    try:
        r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0"})
        item["status"]=r.status_code;item["length"]=len(r.content)
        soup=bs4.BeautifulSoup(r.text,"html.parser")
        item["meta"]=[{"key":m.get("property") or m.get("name"),"value":m.get("content","")[:240]} for m in soup.select("meta") if any(w in str(m).lower() for w in ("image","logo","twitter:"))][:18]
        item["imgs"]=[{"alt":i.get("alt",""),"src":i.get("src"),"data_src":i.get("data-src"),"srcset":(i.get("srcset") or "")[:150]} for i in soup.select("img")][:50]
    except Exception as e:item["error"]=str(e)[:180]
    results.append(item)
for url in ["https://tamhi.org/sports-club/st-patricks-ym-fc/"]:
    item={"page":url}
    try:
        r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0"})
        item["status"]=r.status_code;item["length"]=len(r.content)
        soup=bs4.BeautifulSoup(r.text,"html.parser")
        item["imgs"]=[{"alt":i.get("alt",""),"src":i.get("src"),"data_src":i.get("data-src"),"parent":i.parent.get_text(" ",strip=True)[:60] if i.parent else ""} for i in soup.select("img")][:200]
        item["meta"]=[{"key":m.get("property") or m.get("name"),"value":m.get("content","")} for m in soup.select("meta") if "image" in str(m).lower()][:20]
    except Exception as e:item["error"]=str(e)[:160]
    results.append(item)
out=ROOT/"nafl_probe.json"
out.write_text(json.dumps(results,ensure_ascii=False,indent=2))
for x in results:print(x["page"],x.get("status"),x.get("length"),len(x.get("imgs",[])),x.get("error",""))
