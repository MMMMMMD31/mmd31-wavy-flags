#!/usr/bin/env python3
"""Snapshot 2026/27 observed P, points, GF, GA from publicly visible FWP league tables.
No speculation or unpublished API; keep branch-isolated study output, fail soft on missing groups."""
import json, re, unicodedata, difflib, time, requests
from pathlib import Path
from collections import defaultdict,Counter
from bs4 import BeautifulSoup

def normalize(s):
 s=unicodedata.normalize("NFKD",s).lower().replace("’","'").replace("&"," and ")
 s=re.sub(r"\\b(f\\.?c\\.?|a\\.?f\\.?c\\.?|football club)\\b","",s)
 s=re.sub(r"[^a-z0-9]+","",s)
 return s

def readcat(path):
 return json.loads(Path(path).read_text(encoding="utf8"))

all_clubs=[]
five=readcat("tools/english_clubs_2026_27_sources.json")
labels5=["Premier League"]*20+["EFL Championship"]*24+["EFL League One"]*24+["EFL League Two"]*24+["National League"]*24
assert len(five)==len(labels5)==116
for row,group in zip(five,labels5):all_clubs.append({"id":row["id"],"name":row["name"],"division":group})
seven=readcat("tools/english_clubs_d6_d7_2026_27_sources.json")
labels7=["National League North"]*24+["National League South"]*24+["Northern Premier League Premier Division"]*22+["Southern League Premier Central"]*22+["Southern League Premier South"]*22+["Isthmian League Premier Division"]*22
assert len(seven)==len(labels7)==136
for row,group in zip(seven,labels7):all_clubs.append({"id":row["id"],"name":row["name"],"division":group})
last=readcat("tools/english_clubs_d8_d9_2026_27_sources.json")
assert len(last)==498
for row in last:all_clubs.append({"id":row["id"],"name":row["name"],"division":row["division"]})
assert len(all_clubs)==750
divisions=list(dict.fromkeys(c["division"] for c in all_clubs))
assert len(divisions)==35, len(divisions)

# FWP public site categories; some Step 5 comps not listed.
d_alias={
"Premier League":"premier league","EFL Championship":"championship","EFL League One":"league one","EFL League Two":"league two",
"National League":"national league","National League North":"national league north","National League South":"national league south",
"Northern Premier League Premier Division":"northern premier league premier",
"Southern League Premier Central":"southern league premier central",
"Southern League Premier South":"southern league premier south",
"Isthmian League Premier Division":"isthmian league premier",
"Northern Premier League Division One East":"northern premier league east",
"Northern Premier League Division One Midlands":"northern premier league midlands",
"Northern Premier League Division One West":"northern premier league west",
"Isthmian League Division One North":"isthmian league north",
"Isthmian League Division One South Central":"isthmian league south central",
"Isthmian League Division One South East":"isthmian league south east",
"Southern League Division One Central":"southern league central",
"Southern League Division One South":"southern league south",
"Combined Counties League Premier Division North":"combined counties premier north",
"Combined Counties League Premier Division South":"combined counties premier south",
"Eastern Counties League Premier Division":"eastern counties premier division",
"Essex Senior League Premier Division":"essex senior league",
"Hellenic League Premier Division":"hellenic league premier",
"Northern Counties East League Premier Division":"n counties east premier",
"Northern League Division One":"northern league division one",
"Southern Counties East League Premier Division":"s counties east premier",
"Spartan South Midlands League Premier Division":"spartan s midlands premier",
"United Counties League Premier Division North":"united counties premier north",
"United Counties League Premier Division South":"united counties premier south",
}
# FWP display text from the site navigation (avoid accidentally using wrong league).
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (compatible; personal non-commercial football mod data research)"})
root="https://www.footballwebpages.co.uk/"
home=session.get(root+"national-league-north/league-table",timeout=30)
home.raise_for_status()
soup=BeautifulSoup(home.text,"html.parser")
nav=[]
for a in soup.select("a[href]"):
 href=a.get("href") or ""
 label=a.get_text(" ",strip=True)
 if not label or not href or href.startswith(("#","mailto:")):continue
 if not re.fullmatch(r"[a-z0-9-]+",href):continue
 nav.append((label,href))
nav=list(dict.fromkeys(nav))
def key(s):
 s=s.lower().replace("&"," and ")
 return re.sub(r"[^a-z0-9]+"," ",s).strip()

def find_href(group):
 target=key(d_alias.get(group,group))
 # map precisely via display string synonyms and tolerant abbreviated labels.
 candidates=[]
 for label,href in nav:
  s=key(label).replace("sky bet ","").replace("enterprise ","").replace("isthmian football league ","isthmian league ").replace("southern football league ","southern league ")
  d=difflib.SequenceMatcher(None,target,s).ratio()
  if target==s:d=1
  candidates.append((d,label,href))
 candidates.sort(reverse=True)
 if not candidates or candidates[0][0] < .69:return None,candidates[:3]
 return candidates[0][2],candidates[:3]

def parse_table(html):
 soup=BeautifulSoup(html,"html.parser")
 matches=[]
 for table in soup.select("table.league-table"):
  parsed=[]
  for row in table.select("tr"):
   vals=[x.strip() for x in row.get_text(" | ",strip=True).split("|") if x.strip()]
   if len(vals)<12 or not vals[0].strip().isdigit():continue
   try:
    pos=int(vals[0]);name=vals[1].strip()
    played,w,d,l,gf,ga,gd,points=map(int,[v.replace("+","") for v in vals[-8:]])
    if played<=0 or abs(gf-ga-gd)>0 or played!=w+d+l:continue
    parsed.append({"name":name,"rank":pos,"played":played,"points":points,"gd":gd,"gf":gf,"ga":ga})
   except (ValueError,IndexError):continue
  matches.append(parsed)
 return sorted(matches,key=len,reverse=True)[0] if matches else []

def matched_club(row,table):
 q=normalize(row["name"])
 cand=[t for t in table if normalize(t["name"])==q]
 if len(cand)==1:return cand[0],"exact",1
 aliases={"wolverhamptonwanderers":"wolves","queensparkrangers":"qpr",
          "brightonandhovealbion":"brighton","tottenhamhotspur":"tottenham",
          "westhamunited":"westham","newcastleunited":"newcastle",
          "afcbournemouth":"bournemouth","fchalifaxtown":"halifax","miltonkeynesdons":"mkdons"}
 target=aliases.get(q,q)
 scores=sorted(((difflib.SequenceMatcher(None,target,normalize(t["name"])).ratio(),t) for t in table),reverse=True,key=lambda x:x[0])
 if scores and scores[0][0]>=.83 and (len(scores)==1 or scores[0][0]-scores[1][0]>.075):
  return scores[0][1],"fuzzy",round(scores[0][0],3)
 return None,"unmatched",round(scores[0][0],3) if scores else 0

records=[];sources=[];coverage=Counter()
for i,division in enumerate(divisions,1):
 href,possible=find_href(division)
 table=[];url=None;error=None
 if division in d_alias and href:
  url=root+href+"/league-table"
  try:
   r=session.get(url,timeout=23)
   if r.status_code!=200:raise ValueError(f"HTTP {r.status_code}")
   table=parse_table(r.text)
   if not table:raise ValueError("No valid league table rows parsed")
  except Exception as exc:error=str(exc)
 else:error="League not on FWP navigation"
 group_clubs=[c for c in all_clubs if c["division"]==division]
 used=set()
 matches=[]
 for club in group_clubs:
  chosen,method,confidence=matched_club(club,table)
  if chosen and chosen["name"] in used:
   chosen=None;method="duplicate_fuzzy_rejected"
  if chosen:used.add(chosen["name"]);coverage[division]+=1
  item={**club,"played":chosen["played"] if chosen else None,
        "points":chosen["points"] if chosen else None,
        "gf":chosen["gf"] if chosen else None,
        "ga":chosen["ga"] if chosen else None,
        "gd":chosen["gd"] if chosen else None,
        "source_team":chosen["name"] if chosen else None,
        "match_type":method if chosen else None}
  records.append(item)
  if not chosen:matches.append(club["name"])
 sources.append({"division":division,"url":url,"found":coverage[division],"expected":len(group_clubs),"table_rows":len(table),"error":error,"unmatched_clubs":matches,"candidates":possible[:1]})
 print(f"[{i:02d}/{len(divisions)}] {division}: {coverage[division]}/{len(group_clubs)} (source {url})",flush=True)
 time.sleep(.25)
assert len(records)==750
out=Path("docs/english-ratings-research");out.mkdir(parents=True,exist_ok=True)
data={"as_of":"2026-10-23","method":"FWP public web league tables, points and goals (not match-by-match Elo)","source_groups":sources,"records":records}
(out/"standings_2026_10_23.json").write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")))
summary={"all_clubs":750,"matched_clubs":sum(x["played"] is not None for x in records),"groups":len(divisions),"sources":sources}
(out/"coverage_2026_10_23.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print("FINISHED",summary["matched_clubs"],"/750",flush=True)
