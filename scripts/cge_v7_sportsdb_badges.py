#!/usr/bin/env python3
"""CGE V7: only exact country-and-club matched TheSportsDB crests are publishable."""
import csv, io, os, time, sys, json
from pathlib import Path
from difflib import SequenceMatcher
import requests
from PIL import Image

BASE=Path("docs/cge-v7-authentic-badges-20261026")
INPUT=BASE/"targets.csv"
OUTPUT=BASE/"sportsdb_source_audit.csv"
sys.path.insert(0,"scripts")
from cge_v7_wikidata_badges import norm,core

ALIASES={"Czech Republic":{"czech republic","czechia"},"Faroe Islands":{"faroe islands"}}
s=requests.Session()
s.headers.update({"User-Agent":"MMD31-CGE-badge-verifier/1.0","Accept":"application/json"})

def equal_club(a,b):
    aa,bb=norm(a),norm(b)
    if aa==bb:return True
    ac,bc=core(a),core(b)
    # Country/name identity must match rather than selecting a merely similar team.
    return len(ac)>=7 and ac==bc

def check_country(want,got):
    c=norm(got or "")
    return c in {norm(x) for x in ALIASES.get(want,{want})}

def process():
    table=list(csv.DictReader(INPUT.open(encoding="utf-8")))
    audit=[]
    for row in table:
        id_,name,country=int(row["teamId"]),row["clubName"],row["country"]
        dest=BASE/f"{id_}.png"
        if dest.exists():
            audit.append([id_,name,country,"already_published","",""])
            continue
        try:
            r=s.get("https://www.thesportsdb.com/api/v1/json/3/searchteams.php",params={"t":name},timeout=22)
            r.raise_for_status()
            candidates=r.json().get("teams") or []
            valid=[t for t in candidates if (t.get("strSport") in ("Soccer","Football")) and equal_club(name,t.get("strTeam") or "") and check_country(country,t.get("strCountry")) and t.get("strBadge")]
            if len(valid)!=1:
                audit.append([id_,name,country,"not_verified","",""])
                continue
            team=valid[0]
            url=team["strBadge"].split("?")[0]
            response=s.get(url,timeout=25);response.raise_for_status()
            im=Image.open(io.BytesIO(response.content)).convert("RGBA")
            if min(im.size)<80: raise ValueError("image too small")
            im.thumbnail((108,84),Image.Resampling.LANCZOS)
            dst=Image.new("RGBA",(120,96),(228,233,240,255))
            dst.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
            dst.convert("RGB").save(dest,format="PNG",optimize=True)
            audit.append([id_,name,country,"source_verified",team.get("idTeam",""),url])
            print("VERIFIED",name,url,flush=True)
        except Exception as e:
            print("ERROR",name,str(e)[:160],flush=True)
            audit.append([id_,name,country,"fetch_error","",str(e)[:160]])
        time.sleep(.12)
    with OUTPUT.open("w",encoding="utf8",newline="") as f:
        wr=csv.writer(f);wr.writerow(["teamId","clubName","country","status","providerId","sourceUrlOrError"]);wr.writerows(audit)
    print("COUNTS",json.dumps({a:sum(x[3]==a for x in audit) for a in set(x[3] for x in audit)}),flush=True)
if __name__=="__main__":process()
