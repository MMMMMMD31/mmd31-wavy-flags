#!/usr/bin/env python3
"""CGE V7: conservative retrieval of authentic football badges from Wikidata P154.
Never generates fabricated crests; missing/ambiguous results stay missing."""
import csv, io, os, re, sys, time, json, unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import quote
import requests
from PIL import Image

ROOT = Path("docs/cge-v7-authentic-badges-20261026")
TARGETS = ROOT / "targets.csv"
REPORT = ROOT / "wikidata_source_audit.csv"
UA = "MMD31-CGE-verified-club-crests/1.0 (research project; GitHub Actions)"
HTTP = requests.Session()
HTTP.headers.update({"User-Agent":UA,"Accept":"application/json"})
WIKIDATA="https://www.wikidata.org/w/api.php"
COMMONS="https://commons.wikimedia.org/w/api.php"
LANGUAGES={"Czech Republic":"cs","Norway":"no","Poland":"pl","Iceland":"is","Faroe Islands":"fo","Azerbaijan":"az","Armenia":"hy","Israel":"he","Kazakhstan":"kk"}
COUNTRIES={"Czech Republic":"Q213","Norway":"Q20","Poland":"Q36","Iceland":"Q189","Faroe Islands":"Q4628","Azerbaijan":"Q227","Armenia":"Q399","Israel":"Q801","Kazakhstan":"Q232"}
COMMON_PREFIXES={"fk","sk","fc","f","c","mfk","sfc","sfc","tj","if","umf","csK","f.c"}

def norm(value):
    value=unicodedata.normalize("NFKD",value.casefold())
    value="".join(ch for ch in value if not unicodedata.combining(ch))
    value=value.replace("ł","l").replace("ø","o").replace("æ","ae").replace("ð","d").replace("þ","th").replace("ı","i")
    return " ".join(re.findall(r"[a-z0-9]+",value))

def core(value):
    words=norm(value).split()
    while words and words[0] in COMMON_PREFIXES: words.pop(0)
    return " ".join(words)

def score(query, label):
    a,b=norm(query),norm(label)
    if a==b: return 1.0
    ca,cb=core(query),core(label)
    if ca==cb and len(ca)>=5: return .96
    return max(SequenceMatcher(None,a,b).ratio(), .94*SequenceMatcher(None,ca,cb).ratio())

def api(url,params):
    r=HTTP.get(url,params=params,timeout=35)
    r.raise_for_status()
    return r.json()

def lookup(name,country):
    lang=LANGUAGES.get(country,"en")
    searches=[(name,"en")]
    if lang!="en": searches.append((name,lang))
    # Aliases only broaden when the exact name has no Wikidata crest.
    choices={}
    for title,locale in searches:
        try:
            results=api(WIKIDATA,{"action":"wbsearchentities","search":title,"language":locale,"format":"json","limit":8,"type":"item"}).get("search",[])
            for c in results: choices[c["id"]]=c
        except Exception as e: print("SEARCH_ERROR",name,str(e)[:150])
        time.sleep(.15)
    ranked=sorted(choices.values(),key=lambda x:max(score(name,x.get("label","")),score(name,x.get("match",{}).get("text",""))),reverse=True)
    for result in ranked:
        quality=max(score(name,result.get("label","")),score(name,result.get("match",{}).get("text","")))
        if quality<.87: continue
        try:
            entity=api(WIKIDATA,{"action":"wbgetentities","ids":result["id"],"props":"claims|labels|aliases","format":"json"}).get("entities",{}).get(result["id"],{})
            claims=entity.get("claims",{})
            countries=[x.get("mainsnak",{}).get("datavalue",{}).get("value",{}).get("id") for x in claims.get("P17",[])]
            expected=COUNTRIES.get(country)
            # Reject a stated different country; missing P17 is permitted.
            if countries and expected not in countries: continue
            logos=claims.get("P154",[])
            if not logos: continue
            filename=logos[0].get("mainsnak",{}).get("datavalue",{}).get("value")
            if not isinstance(filename,str): continue
            # For a short/generic name demand exact matching.
            if len(core(name))<7 and quality<.99: continue
            return result["id"], filename, quality
        except Exception as e: print("ENTITY_ERROR",name,str(e)[:150])
    return None,None,0

def image_url(filename):
    response=api(COMMONS,{"action":"query","prop":"imageinfo","iiprop":"url|size","iiurlwidth":650,"titles":"File:"+filename,"format":"json"})
    pages=response.get("query",{}).get("pages",{})
    for page in pages.values():
        info=page.get("imageinfo",[])
        if info:
            entry=info[0]
            return entry.get("thumburl") or entry.get("url")
    return None

def prepare(url,savepath):
    response=HTTP.get(url,timeout=45)
    response.raise_for_status()
    im=Image.open(io.BytesIO(response.content)).convert("RGBA")
    if min(im.size)<85: raise ValueError("source crest too small")
    # Preserve all official logo details: resize and backdrop only.
    # An opaque white rectangle isn't cut away blindly because some badges contain white.
    im.thumbnail((108,84),Image.Resampling.LANCZOS)
    # Pale blue-grey background gives the logo perimeter separation.
    canvas=Image.new("RGBA",(120,96),(224,232,241,255))
    canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
    canvas.convert("RGB").save(savepath,"PNG",optimize=True)

def main():
    source_rows=list(csv.DictReader(TARGETS.open(encoding="utf-8")))
    audit=[]
    for r in source_rows:
        team_id,name,country=int(r["teamId"]),r["clubName"],r["country"]
        target=ROOT/f"{team_id}.png"
        if target.exists():
            audit.append((team_id,name,country,"already_published","",""))
            continue
        qid,filename,confidence=lookup(name,country)
        if not filename:
            audit.append((team_id,name,country,"not_verified","",""))
            continue
        try:
            url=image_url(filename)
            if not url: raise ValueError("Commons file not found")
            prepare(url,target)
            audit.append((team_id,name,country,"source_verified",qid,url))
            print("VERIFIED",team_id,name,qid,url,flush=True)
        except Exception as e:
            audit.append((team_id,name,country,"download_error",qid,str(e)[:220]))
            print("FETCH_ERROR",team_id,name,str(e)[:220],flush=True)
        time.sleep(.1)
    with REPORT.open("w",encoding="utf-8",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(("teamId","clubName","country","status","wikidataId","sourceUrlOrError"))
        writer.writerows(audit)
    print("RESULT",json.dumps({s:sum(x[3]==s for x in audit) for s in set(x[3] for x in audit)},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
