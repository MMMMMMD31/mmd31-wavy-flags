#!/usr/bin/env python3
"""CGE V9: auditable provisional recalibration of D1 clubs using 2026 ESPN league results.
Only exact/unique high-confidence participant matches are edited; others unchanged.
Formula: expected points against CGE league Elo opponents vs observed PPG,
strong shrinkage for low-game samples, max 38 Elo movement. Not an official Elo.
"""
import csv,io,os,re,json,unicodedata,math,time
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from difflib import SequenceMatcher
from pathlib import Path
import requests

ROOT=Path("docs/cge-v9-audit")
ROOT.mkdir(exist_ok=True,parents=True)
CODES={
"France":"fra.1","Germany":"ger.1","England":"eng.1","Spain":"esp.1","Italy":"ita.1",
"Belgium":"bel.1","Luxembourg":"lux.1","Netherlands":"ned.1","Andorra":"and.1",
"Republic of Ireland":"irl.1","Northern Ireland":"nir.1","Scotland":"sco.1",
"Portugal":"por.1","Gibraltar":"gib.1","Switzerland":"sui.1","Austria":"aut.1",
"San Marino":"smr.1","Wales":"wal.1","Iceland":"isl.1","Faroe Islands":"fro.1",
"Norway":"nor.1","Greece":"gre.1","Cyprus":"cyp.1","Malta":"mlt.1",
"Israel":"isr.1","Slovenia":"svn.1","Croatia":"cro.1","Montenegro":"mne.1",
"Albania":"alb.1","Czechia":"cze.1","Slovakia":"svk.1","Hungary":"hun.1",
"Denmark":"den.1","Sweden":"swe.1","Finland":"fin.1","Estonia":"est.1",
"Latvia":"lat.1","Lithuania":"lit.1","Poland":"pol.1",
"Bosnia and Herzegovina":"bih.1","Serbia":"srb.1","Kosovo":"kos.1",
"North Macedonia":"mkd.1","Bulgaria":"bul.1","Romania":"rou.1",
"Belarus":"blr.1","Ukraine":"ukr.1","Moldova":"mda.1","Georgia":"geo.1",
"Armenia":"arm.1","Azerbaijan":"aze.1","Kazakhstan":"kaz.1","Turkey":"tur.1",
}
REPLACEMENTS={
"Paris Saint-Germain":["Paris Saint-Germain","Paris SG","PSG"],
"Inter Milan":["Internazionale","Inter Milan","Internazionale Milano","Inter"],
"AC Milan":["AC Milan","Milan"],
"Manchester United":["Manchester United","Man United"],
"Manchester City":["Manchester City","Man City"],
"Tottenham Hotspur":["Tottenham Hotspur","Tottenham"],
"Wolverhampton Wanderers":["Wolverhampton Wanderers","Wolves"],
"Brighton & Hove Albion":["Brighton & Hove Albion","Brighton"],
"Newcastle United":["Newcastle United","Newcastle"],
"Nottingham Forest":["Nottingham Forest"],
"Leicester City":["Leicester City"],
"FC Bayern München":["Bayern Munich","Bayern München"],
"Borussia Dortmund":["Borussia Dortmund"],
"RB Leipzig":["RB Leipzig"],
"Sporting CP":["Sporting CP","Sporting Lisbon"],
"SL Benfica":["Benfica","SL Benfica"],
"FC Porto":["FC Porto","Porto"],
"VfB Stuttgart":["Stuttgart","VfB Stuttgart"],
"FC Barcelona":["Barcelona","FC Barcelona"],
"Real Madrid CF":["Real Madrid","Real Madrid CF"],
"Atlético de Madrid":["Atletico Madrid","Atlético Madrid","Atletico de Madrid"],
"RC Lens":["RC Lens","Lens"],
"LOSC Lille":["Lille","LOSC Lille"],
"AS Monaco":["Monaco","AS Monaco"],
"Olympique Lyonnais":["Lyon","Olympique Lyonnais"],
"Olympique de Marseille":["Marseille","Olympique de Marseille"],
"RC Strasbourg Alsace":["Strasbourg"],
"Stade Rennais FC":["Rennes","Stade Rennais"],
}
PREFIXES={"fk","fc","ac","sc","sk","mfc","mfk","cf","cd","ud","sd","rc","afc","ks","nk","if","ifk","afk","bsc","sv","vfl","vfb","as","stade","club"}

def norm(s):
 s=unicodedata.normalize("NFKD",(s or "").lower())
 s="".join(c for c in s if not unicodedata.combining(c))
 s=s.replace("ł","l").replace("ø","o").replace("æ","ae").replace("ð","d").replace("þ","th")
 return " ".join(re.findall("[a-z0-9]+",s))

def core(s):
 words=norm(s).split()
 while words and words[0] in PREFIXES:words.pop(0)
 return " ".join(words)

def similarity(a,b):
 na,nb=norm(a),norm(b)
 if na==nb:return 1.0
 ca,cb=core(a),core(b)
 if ca==cb and len(ca)>=6:return .98
 return max(SequenceMatcher(None,na,nb).ratio(),.94*SequenceMatcher(None,ca,cb).ratio())

def extract(entries):
 out=[]
 for item in entries:
  team=item.get("team",{})
  stats={s.get("name"):s.get("value") for s in item.get("stats",[]) if isinstance(s,dict)}
  gp=stats.get("gamesPlayed") or 0
  try:gp=int(gp)
  except: gp=0
  if gp<1:continue
  out.append({"team":team.get("displayName") or team.get("name"),"espnTeamId":team.get("id",""),
   "gp":gp,"wins":int(stats.get("wins") or 0),"draws":int(stats.get("ties") or 0),
   "losses":int(stats.get("losses") or 0),"gf":int(stats.get("pointsFor") or 0),
   "ga":int(stats.get("pointsAgainst") or 0),"points":int(stats.get("points") or 0)})
 return out

def get_league(tup):
 country,code=tup
 url=f"https://site.api.espn.com/apis/v2/sports/soccer/{code}/standings?season=2026"
 try:
  response=requests.get(url,headers={"User-Agent":"Mozilla/5.0 (compatible; CGE Elo audit)","Accept":"application/json"},timeout=35)
  response.raise_for_status()
  d=response.json()
  rows=[]
  for ch in d.get("children",[]):
   entries=ch.get("standings",{}).get("entries",[])
   rows.extend(extract(entries))
  if not rows:return country,code,url,[],f"empty entries ({d.get('name','')})"
  # Take unique ESPN team ID for split leagues without duplication.
  unique={r["espnTeamId"]:r for r in rows}
  return country,code,url,list(unique.values()),f"OK {d.get('name','')}"
 except Exception as e:return country,code,url,[],"ERROR "+str(e)[:160]

def expected_points(elo, others):
 # Nominal probability with shared 26% draw fraction.
 vals=[]
 for opp in others:
  if opp==elo and len(others)==0:continue
  e=1/(1+10**((opp-elo)/400))
  vals.append(3*.74*e+.26)
 return sum(vals)/len(vals) if vals else 1.37

def main():
 primary=list(csv.DictReader((ROOT/"d1_719_cge_v8_clubs.csv").open(encoding="utf-8")))
 if len(primary)!=719:raise ValueError("D1 cohort must contain 719 clubs")
 stats={}
 with ThreadPoolExecutor(max_workers=9) as ex:
  future={ex.submit(get_league,item):item for item in CODES.items()}
  for f in as_completed(future):
   country,code,url,entries,status=f.result()
   stats[country]={"code":code,"url":url,"rows":entries,"status":status}
   print(country,status,len(entries),flush=True)
 with (ROOT/"espn_sources_2026.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.writer(f);w.writerow(["country","leagueCode","sourceURL","status","teamCount","club","espnTeamId","gp","points","gf","ga","wins","draws","losses"])
  for country in CODES:
   obj=stats[country]
   if not obj["rows"]:w.writerow([country,obj["code"],obj["url"],obj["status"],0]+[""]*9)
   for r in obj["rows"]:
    w.writerow([country,obj["code"],obj["url"],obj["status"],len(obj["rows"]),r["team"],r["espnTeamId"],r["gp"],r["points"],r["gf"],r["ga"],r["wins"],r["draws"],r["losses"]])
 props=[]
 for c in primary:
  country=c["country"]; name=c["team"];team_id=c["teamId"];elo=int(c["elo2030"])
  league=stats[country];entries=league["rows"]
  aliases=REPLACEMENTS.get(name,[name])
  scored=[]
  for r in entries:
   quality=max(similarity(a,r["team"]) for a in aliases)
   scored.append((quality,r))
  scored.sort(key=lambda x:x[0],reverse=True)
  status="NO_DATA";delta=0;match="";quality=0;gp=0;gf=0;ga=0;pts=0;expect=0
  if scored:
   quality,r=scored[0]
   second=scored[1][0] if len(scored)>1 else 0
   # Avoid confusing sibling clubs, reserves or entities with similar names.
   if quality>=.90 and quality-second>=.08:
    gp=r["gp"];gf=r["gf"];ga=r["ga"];pts=r["points"];match=r["team"]
    other=[int(x["elo2030"]) for x in primary if x["country"]==country and x["teamId"]!=team_id]
    expect=expected_points(elo,other)
    if gp>=5:
     obs=pts/gp
     evidence=gp/(gp+13)
     delta=round(max(-38,min(38,38*(obs-expect)*evidence)))
     new=min(2299,max(350,elo+delta))
     if norm(name)==norm("Paris Saint-Germain"):new=2300
     delta=new-elo
     status="PROXY_STANDINGS" if delta else "MATCHED_NO_CHANGE"
    else:status="LOW_MATCH_SAMPLE"
   else:status="AMBIGUOUS_IDENTITY"
  props.append({"teamId":team_id,"country":country,"team":name,"eloBefore":elo,"deltaElo":delta,"eloAfter":elo+delta,
  "status":status,"matchedTeam":match,"matchQuality":round(quality,3),"matches":gp,"points":pts,
  "gf":gf,"ga":ga,"expectedPpg":round(expect,3),"sourceURL":league["url"],"sourceStatus":league["status"],
  "method":"expected points from existing D1 Elo opponent ratings; observed PPG residual; shrink gp/(gp+13); coefficient 38; clamp +/-38"})
 with (ROOT/"elo_proposals_D1_719.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(props[0]));w.writeheader();w.writerows(props)
 compact=[(r["teamId"],r["deltaElo"]) for r in props if r["deltaElo"]]
 with (ROOT/"elo_updates_compact.tsv").open("w",encoding="utf-8") as f:
  for tid,d in compact:f.write(f"{tid}\t{d}\n")
 s=dict(Counter(r["status"] for r in props))
 with (ROOT/"espn_summary.json").open("w") as f:
  json.dump({"date":"2026-10-26","clubs":len(props),"updated":len(compact),"statuses":s,
   "leaguesWithData":{c:len(x["rows"]) for c,x in stats.items() if x["rows"]},"notes":"All estimates are provisional: ESPN 2026 standings are a snapshot, not a match-by-match ClubElo model. Sports evidence not available leaves ratings unchanged."},f,ensure_ascii=False,indent=2)
 print("FINAL",json.dumps(s,ensure_ascii=False),"updated",len(compact),flush=True)
if __name__=="__main__":main()
