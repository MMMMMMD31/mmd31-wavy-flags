import requests,json,os,re,collections
s=requests.Session()
url='https://matchdayinsights.com/rankings_table.json'
r=s.get(url,timeout=45,headers={"User-Agent":"Mozilla/5.0"});print('DATA',r.status_code,len(r.content),r.url,flush=True);r.raise_for_status()
data=r.json()
def snap(x):
 if isinstance(x,dict):return {"type":"dict","keys":list(x)[:40],"sample":{k:(v[0] if isinstance(v,list) and v else (str(v)[:220] if not isinstance(v,(dict,list)) else ("list:"+str(len(v)) if isinstance(v,list) else list(v)[:10]))) for k,v in list(x.items())[:10]}}
 if isinstance(x,list):return {"type":"list","count":len(x),"samples":x[:5]}
 return {"type":type(x).__name__,"sample":str(x)[:200]}
res={"rankings":snap(data)}
for url in ["https://clubelo.com/","https://matchdayinsights.com/index.html"]:
 try:
  resp=s.get(url,timeout=30);res[url]={"status":resp.status_code,"length":len(resp.content)}
  if 'matchday' in url:
   html=resp.text
   for phrase in ['rankings_table.json','CLUBS = ','res.json','res.json','fetch(']:
    idx=html.find(phrase);res[url][phrase]=html[max(0,idx-300):idx+400]
 except Exception as e:res[url]={"error":str(e)}
os.makedirs("docs/cge-v11-source-audit",exist_ok=True)
open("docs/cge-v11-source-audit/ranking-schema.json","w").write(json.dumps(res,ensure_ascii=False,indent=2)[:32000])
# subset full ranking in compact CSV for externally verified source and later calibration
import csv
rows=data if isinstance(data,list) else next((v for v in data.values() if isinstance(v,list) and len(v)>30),[])
with open("docs/cge-v11-source-audit/matchday-rankings.json","w") as f:json.dump(rows,f,ensure_ascii=False,separators=(",",":"))
print("ROWS",len(rows),"HEAD",str(rows[:2])[:1000],flush=True)
