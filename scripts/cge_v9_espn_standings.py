#!/usr/bin/env python3
"""Read-only 2026 country D1 standings evidence; do not infer unsupported outcomes."""
import csv,concurrent.futures,requests,time,os,collections,json
from pathlib import Path
LEAGUES={
"France D1-D3":"fra.1","Germany D1-D3":"ger.1","England D1-D4":"eng.1","Spain D1-D3":"esp.1",
"Italy D1-D3":"ita.1","Belgium D1-D3":"bel.1","Luxembourg D1-D2":"lux.1",
"Netherlands D1-D3":"ned.1","Andorra D1-D2":"and.1","Republic of Ireland D1-D3":"irl.1",
"Northern Ireland D1-D2":"nir.1","Scotland D1-D3":"sco.1","Portugal D1-D3":"por.1",
"Gibraltar D1":"gib.1","Switzerland D1-D2":"sui.1","Austria D1-D2":"aut.1","San Marino D1":"smr.1",
"Wales D1-D2":"wal.1","Iceland D1-D2":"isl.1","Faroe Islands D1-D2":"fro.1",
"Norway D1-D3":"nor.1","Greece D1-D2":"gre.1","Cyprus D1-D2":"cyp.1","Malta D1-D2":"mlt.1",
"Israel D1-D2":"isr.1","Slovenia D1-D2":"svn.1","Croatia D1-D2":"cro.1","Montenegro D1-D2":"mne.1",
"Albania D1-D2":"alb.1","Czechia D1-D3":"cze.1","Slovakia D1-D2":"svk.1",
"Hungary D1-D2":"hun.1","Denmark D1-D3":"den.1","Sweden D1-D2":"swe.1","Finland D1-D2":"fin.1",
"Estonia D1-D2":"est.1","Latvia D1-D2":"lat.1","Lithuania D1-D2":"ltu.1","Poland D1-D3":"pol.1",
"Bosnia and Herzegovina D1-D2":"bih.1","Serbia D1-D2":"ser.1","Kosovo D1-D2":"kos.1",
"North Macedonia D1-D2":"mkd.1","Bulgaria D1-D2":"bul.1","Romania D1-D2":"rou.1",
"Belarus D1-D2":"blr.1","Ukraine D1-D2":"ukr.1","Moldova D1-D2":"mda.1",
"Georgia D1-D2":"geo.1","Armenia D1-D2":"arm.1","Azerbaijan D1-D2":"aze.1",
"Kazakhstan D1-D2":"kaz.1","Turkey D1-D3":"tur.1"}
STATS={"gamesPlayed":["gamesPlayed","gamesplayed","games"],"points":["points","pts"],
"pointsFor":["pointsFor","goalsFor","goals"],"pointsAgainst":["pointsAgainst","goalsAgainst"],
"pointDifferential":["pointDifferential","goalDifference"],"wins":["wins"],"ties":["ties"],"losses":["losses"]}
OUT=Path("docs/cge-v9-espn-evidence");OUT.mkdir(exist_ok=True,parents=True)
def flat(node,group=""):
  results=[]
  if not isinstance(node,dict):return results
  if isinstance(node.get("standings"),dict):
    for entry in node["standings"].get("entries",[]) or []:
      t=entry.get("team") or {}; stats={}
      for s in entry.get("stats",[]) or []:
        k=s.get("name") or s.get("type")
        if k:stats[k]=s.get("value")
      vals={}
      for k,names in STATS.items():
        vals[k]=next((stats[n] for n in names if n in stats),None)
      results.append({"name":t.get("displayName") or t.get("name") or "","group":node.get("name") or group,"stats":vals})
  for child in node.get("children",[]) or []: results.extend(flat(child,group=node.get("name") or group))
  return results
def fetch(item):
  comp,code=item
  try:
    r=requests.get(f"https://site.api.espn.com/apis/v2/sports/soccer/{code}/standings",params={"season":2026},timeout=24,headers={"User-Agent":"Mozilla/5.0 (CGE football data consistency audit)"})
    r.raise_for_status();j=r.json();records=flat(j);season=j.get("season") or {}
    # No stale or incompatible season data: accept only exact 2026.
    year=season.get("year")
    if year is not None and str(year)!="2026":return (comp,code,"season_mismatch:"+str(year),[])
    if len(records)<8:return comp,code,"not_enough_entries:"+str(len(records)),[]
    good=sum(int(float(x["stats"].get("gamesPlayed") or 0))>=3 for x in records)
    return comp,code,("OK" if good>=8 else "no_played_games"),records
  except Exception as e:return comp,code,"ERROR:"+str(e)[:150],[]
def main():
  rows=[];statuses=[]
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for comp,code,status,records in pool.map(fetch,LEAGUES.items()):
      statuses.append({"competition":comp,"code":code,"status":status,"records":len(records)})
      if status=="OK":
        for rec in records:
          vals=rec["stats"]; rows.append({"competition":comp,"code":code,"club":rec["name"],"group":rec["group"],**vals})
      print(comp,code,status,len(records),flush=True)
  with (OUT/"standings.csv").open("w",encoding="utf8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["competition","code","club","group"]+list(STATS));w.writeheader();w.writerows(rows)
  with (OUT/"coverage.csv").open("w",encoding="utf8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["competition","code","status","records"]);w.writeheader();w.writerows(statuses)
  print("TOTAL",len(rows),dict(collections.Counter(s["status"] for s in statuses)),flush=True)
if __name__=="__main__":main()
