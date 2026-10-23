import requests,bs4,re,json
from pathlib import Path
s=requests.Session();s.headers["User-Agent"]="Mozilla/5.0 MMD31 football imagery research"
urls={
"fa_vase_badges":"https://www.nonleaguehq.com/fa_vase_badges/",
"fa_cup_badges":"https://www.nonleaguehq.com/fa_cup_badges/",
"england_elo":"https://www.nonleaguehq.com/england-elo/",
"midland_league":"https://www.nonleaguehq.com/midland-premier/",
"thesportsdb":"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t=AFC%20Portchester",
"wikidata":"https://www.wikidata.org/w/api.php?action=wbsearchentities&search=AFC%20Portchester&language=en&format=json&limit=3",
}
out={}
for k,url in urls.items():
 try:
  r=s.get(url,timeout=25);h=bs4.BeautifulSoup(r.text,"html.parser")
  imgs=h.select("img");scripts=h.select("script");links=h.select("a[href]")
  out[k]={"status":r.status_code,"length":len(r.content),"title":h.title.get_text(" ",strip=True) if h.title else None,
          "img_count":len(imgs),"sample_imgs":[{"alt":x.get("alt"),"src":x.get("src"),"data-src":x.get("data-src")} for x in imgs[:25]],
          "text_tail":h.get_text(" ",strip=True)[-1400:],"scripts":[{"src":x.get("src"),"part":x.text[:1000]} for x in scripts if x.text and re.search("elo|club|team",x.text,re.I)][:4],
          "candidate_elo_links":[{"text":x.get_text(" ",strip=True),"url":x.get("href")} for x in links if "elo" in x.get_text(" ",strip=True).lower()][:8],
          "sample_json":r.text[:1500] if k in ("thesportsdb","wikidata") else ""}
 except Exception as e:out[k]={"error":str(e)}
import urllib.parse
try:
 rr=s.get("https://www.nonleaguehq.com/england-elo/",timeout=25)
 sc=bs4.BeautifulSoup(rr.text,"html.parser")
 fragments=[]
 for script in sc.find_all("script"):
  t=script.get_text(" ",strip=True)
  if "SUPABASE" not in t and "rest/v1" not in t and "elo" not in t.lower():continue
  # No auth keys in diagnostics.
  t=t.replace("apikey:","api_key_redacted:").replace("Authorization:","Authorization_Redacted:")
  lines=t.splitlines()
  for i,line in enumerate(lines):
   if any(word in line.lower() for word in ("elo","rest/v1","supabase","fetch(")):
    fragments.append("\\n".join(lines[max(0,i-1):min(len(lines),i+3)])[:850])
 out["elo_script_refs"]=fragments[:45]
except Exception as exc:out["elo_script_refs_error"]=str(exc)
p=Path("docs/english-v13");p.mkdir(parents=True,exist_ok=True)
(p/"diagnostic.json").write_text(json.dumps(out,indent=2,ensure_ascii=False))
print(json.dumps(out,ensure_ascii=False)[:12000])
