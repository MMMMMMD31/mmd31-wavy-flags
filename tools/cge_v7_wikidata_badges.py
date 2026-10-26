#!/usr/bin/env python3
"""Discover *verifiable* authentic club logos from Wikidata / Wikimedia Commons.
Only write PNG when identity + logo filename meet strict verification rules.
All other suggestions are recorded for manual review, never assigned automatically.
"""
from __future__ import annotations
import json, re, time, unicodedata, csv, html, hashlib, colorsys
from pathlib import Path
from urllib.parse import quote
from io import BytesIO
from difflib import SequenceMatcher
import requests
from PIL import Image
import cairosvg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/cge-v7-d3-2026-27/v2"
OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/"tools/cge_v7_badges_missing61.txt",ROOT/"tools/cge_v7_badges_missing80.txt"]
HEAD={'User-Agent':'MMD31CGEClubCrestAudit/1.0 (club-crest authenticity; https://github.com/MMMMMMD31/mmd31-wavy-flags)'}
s=requests.Session();s.headers.update(HEAD)
SKIP={'fc','fk','sk','if','il','cf','af','sc','bk','fotball','football','club','de','the','town','sport','sports','futbol','futebol','ii','b','a'}
def norm(n):
    n=unicodedata.normalize("NFKD",n.casefold())
    n="".join(x for x in n if not unicodedata.combining(x))
    return re.sub(r'[^a-z0-9]','',n)
def words(n):
    n=unicodedata.normalize("NFKD",n.casefold())
    n="".join(x for x in n if not unicodedata.combining(x))
    return [w for w in re.findall(r'[a-z0-9]+',n) if w not in SKIP]
def score(a,b):
    w=words(a);q=words(b)
    core=[x for x in w if len(x)>3] or w
    shared=set(core).intersection(q)
    return round((.48*SequenceMatcher(None,norm(a),norm(b)).ratio()+.52*len(shared)/max(1,len(core))),4)
def get_json(url,params=None):
    r=s.get(url,params=params,timeout=18)
    r.raise_for_status()
    return r.json()
def get_binary(url):
    r=s.get(url,timeout=24);r.raise_for_status()
    if len(r.content)>3_000_000:raise ValueError("Oversized image")
    if r.content.lstrip().lower().startswith(b'<!doctype html'):raise ValueError("HTML not image")
    return r.content
def render(raw):
    if raw.lstrip()[:200].lower().find(b'<svg')>=0 or b'<svg' in raw[:350]:
        data=cairosvg.svg2png(bytestring=raw,output_width=600)
    else:data=raw
    logo=Image.open(BytesIO(data)).convert("RGBA")
    if logo.width<45 or logo.height<45:raise ValueError("Image too small")
    logo.thumbnail((108,84),Image.Resampling.LANCZOS)
    colors={}
    for i,(r,g,b,a) in enumerate(logo.getdata()):
        if i%7 or a<150:continue
        h,sa,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
        if sa>.35 and .17<v<.97:
            q=(r//25,g//25,b//25);colors[q]=colors.get(q,0)+1
    if colors:
        q=max(colors,key=colors.get);bg=tuple(int(.67*255+.33*min(255,v*25+12)) for v in q)
    else:bg=(235,239,244)
    image=Image.new("RGBA",(120,96),bg+(255,))
    image.alpha_composite(logo,((120-logo.width)//2,(96-logo.height)//2))
    return image.convert("RGB")
def wiki_entity(item):
    qid=item["id"]
    x=get_json('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':qid,'props':'claims|labels|descriptions','format':'json'})
    d=x.get('entities',{}).get(qid,{})
    claims=d.get('claims',{})
    val=claims.get('P154',[])
    logo=None
    for c in val:
        try:
            logo=c['mainsnak']['datavalue']['value'];break
        except (TypeError,KeyError):pass
    return logo
def find_candidates(name,country):
    opts=[name]
    stripped=re.sub(r'\b(II|I I|B)\b$','',name,flags=re.I).strip()
    if stripped!=name:opts.append(stripped)
    alt=re.sub(r'^(FK|FC|SK|BK|IL|IF|MFK|CF)\s+','',stripped,flags=re.I).strip()
    if alt not in opts:opts.append(alt)
    if country in ('Iceland','Faroe Islands'):opts += [name.replace('Tórshavn','Torshavn')]
    result=[]
    for q in list(dict.fromkeys(opts))[:3]:
        try:
            x=get_json('https://www.wikidata.org/w/api.php',{'action':'wbsearchentities','search':q,'language':'en','format':'json','limit':8})
            for item in x.get('search',[]):
                label=item.get('label','');desc=item.get('description','')
                sc=score(q,label)
                if country=='Norway' and 'swed' in desc.lower():continue
                if (country=='Wales' and 'england' in desc.lower() and 'wales' not in desc.lower()):continue
                if 'football' not in desc.lower() and 'soccer' not in desc.lower() and 'sports club' not in desc.lower() and 'association' not in desc.lower():continue
                if sc<.73:continue
                result.append({'id':item.get('id'),'label':label,'description':desc,'score':sc,'query':q})
        except Exception as exc:
            result.append({'error':str(exc)[:180]});break
        time.sleep(.15)
    return sorted({x.get('id',str(i)):x for i,x in enumerate(result)}.values(),key=lambda x:x.get('score',0),reverse=True)
def wikimedia_download(filename):
    url='https://commons.wikimedia.org/wiki/Special:Redirect/file/'+quote(filename.replace(' ','_'))
    return get_binary(url),url

manifest=[];errors=0
for path in sources:
    for line in path.read_text(encoding='utf8').splitlines():
        if not line.strip() or line.startswith('#'):continue
        tid,country,name=line.split('|',2)
        item={'id':int(tid),'country':country,'name':name,'status':'MISSING','candidates':[]}
        try:
            candidates=find_candidates(name,country)
            item['candidates']=candidates[:3]
            best=next((x for x in candidates if x.get('score',0)>=.92),None)
            if best:
                logo=wiki_entity(best)
                if logo:
                    raw,url=wikimedia_download(logo)
                    image=render(raw)
                    fp=OUT/(tid+'.png');image.save(fp,optimize=True)
                    assert Image.open(fp).size==(120,96)
                    item.update(status='VERIFIED_WIKIDATA_P154',qid=best['id'],source=url,file=logo,sha256=hashlib.sha256(fp.read_bytes()).hexdigest())
        except Exception as exc:
            item['error']=str(exc)[:350]
            errors+=1
        manifest.append(item)
        if len(manifest)%12==0:print('Scanned',len(manifest),'accepted',sum(x['status']!='MISSING' for x in manifest),flush=True)
        time.sleep(.1)
(OUT/'manifest.json').write_text(json.dumps({'count':len(manifest),'success':sum(x['status']!='MISSING' for x in manifest),'errors':errors,'clubs':manifest},indent=2,ensure_ascii=False),encoding='utf8')
print('FINAL',len(manifest),'success',sum(x['status']!='MISSING' for x in manifest),'errors',errors)
