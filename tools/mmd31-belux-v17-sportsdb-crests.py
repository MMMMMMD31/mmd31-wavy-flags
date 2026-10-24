#!/usr/bin/env python3
"""Public club photo badges from TheSportsDB; exact-name confidence, no fabricated logos."""
import csv,concurrent.futures,io,json,re,unicodedata,hashlib
from pathlib import Path
from PIL import Image
import requests
ROOT=Path('docs/belgian-d4-d5-2026-27/v17')
S=requests.Session();S.headers.update({'User-Agent':'MMD31/2026 noncommercial club crest archival'})
rows=list(csv.DictReader((ROOT/'rosters.csv').open()))
def words(x):
 return set(re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',x.casefold()).encode('ascii','ignore').decode()).split())-{'fc','kfc','rfc','rcs','sv','r','k','royal','rus','vv'}
def search(row):
 if row['crestStatus']=='PARENT_REUSED':return {'id':int(row['id']),'status':'PARENT_REUSED_IN_JSON','name':row['name']}
 out={'id':int(row['id']),'name':row['name'],'status':'NOT_FOUND'}
 try:
  res=S.get('https://www.thesportsdb.com/api/v1/json/3/searchteams.php',params={'t':row['name']},timeout=8);res.raise_for_status();raw=res.json().get('teams')or[]
  matches=[]
  for x in raw:
   badge=x.get('strBadge') or x.get('strTeamBadge')
   if not badge:continue
   original=words(row['name']);other=words(x.get('strTeam')or'')
   if not original or len(original&other)<max(1,round(.6*len(original))):continue
   if not any(q in str(x.get('strSport','')).lower() for q in ['soccer']):continue
   matches.append((badge,x))
  if not matches:return out
  url,entry=matches[0]
  r=S.get(url,timeout=12);r.raise_for_status()
  im=Image.open(io.BytesIO(r.content)).convert('RGBA');assert 60<im.width<5000 and 60<im.height<5000
  bbox=im.getchannel('A').getbbox()
  if bbox:im=im.crop(bbox)
  im.thumbnail((97,82),Image.Resampling.LANCZOS)
  px=[p for p in im.resize((35,35)).getdata() if p[3]>200 and max(p[:3])-min(p[:3])>55]
  tint=max(px,key=lambda x:max(x[:3])-min(x[:3]))[:3] if px else (100,140,170)
  rgb=tuple(int(.15*v+.85*240) for v in tint)
  target=Image.new('RGBA',(120,96),(*rgb,255))
  target.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  f=ROOT/(str(row['id'])+'.png');target.convert('RGB').save(f,optimize=True)
  assert f.stat().st_size>1100
  out.update(status='SOURCE_CANDIDATE_PUBLISHED',source=url,provider='TheSportsDB',providerTeamName=entry['strTeam'],providerTeamId=entry['idTeam'],background=rgb,
             url='https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-d4-d5-v17-crests-fast/'+f.as_posix(),
             sha256=hashlib.sha256(f.read_bytes()).hexdigest())
 except Exception as e:out.update(error=str(e)[:140])
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:results=list(pool.map(search,rows))
for z in results:print(z['name'],z['status'],flush=True)
(ROOT/'sportsdb_crest_status.json').write_text(json.dumps({'assets':results,'sourced':sum(z['status']=='SOURCE_CANDIDATE_PUBLISHED' for z in results)},ensure_ascii=False,indent=2))
