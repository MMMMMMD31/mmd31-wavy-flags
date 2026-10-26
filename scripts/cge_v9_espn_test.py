import requests,json,os
url="https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings?season=2026"
try:
 r=requests.get(url,timeout=25,headers={"User-Agent":"Mozilla/5.0"});d=r.json()
 o={"http":r.status_code,"keys":list(d)[:20],"children":len(d.get("children",[]))}
 ss=d.get("children",[{}])[0]
 o["league"]=ss.get("name");o["standings_keys"]=list(ss.get("standings",{}).keys())
 o["example"]=ss.get("standings",{}).get("entries",[])[:2]
except Exception as e:o={"error":str(e)}
os.makedirs("docs/cge-v9-audit",exist_ok=True)
open("docs/cge-v9-audit/espn_test.json","w").write(json.dumps(o,ensure_ascii=False,indent=2)[:12000])