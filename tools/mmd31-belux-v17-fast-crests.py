#!/usr/bin/env python3
"""Fast 2026-27 Belgian club badge search using documented public crest sources."""
import csv,concurrent.futures,io,json,re,unicodedata,time,hashlib,urllib.parse
from pathlib import Path
from PIL import Image
import requests,cairosvg
ROOT=Path('docs/belgian-d4-d5-2026-27/v17')
ROSTER=list(csv.DictReader((ROOT/'rosters.csv').open()))
S=requests.Session();S.headers.update({'User-Agent':'MMD31/2026 (football-logo-identity-research)'})
def norm(t):return re.sub('[^a-z0-9]+',' ',unicodedata.normalize('NFKD',t.casefold()).encode('ascii','ignore').decode()).strip()
def get(url,params=None):
 r=S.get(url,params=params,timeout=5);r.raise_for_status();return r
def locate(t):
 name=t['name'];out={'id':int(t['id']),'name':name,'status':'NO_AUTHENTIC_SOURCE'}
 if t['crestStatus']=='PARENT_REUSED':return {**out,'status':'PARENT_REUSED_IN_JSON'}
 try:
  res=get('https://www.wikidata.org/w/api.php',{'action':'wbsearchentities','search':name,'language':'en','format':'json','limit':6}).json()
  words=set(norm(name).split())
  for item in res.get('search',[]):
   lab=item.get('label','');ls=set(norm(lab).split())
   if len(words&ls)<max(1,round(len(words)*.6)):continue
   if 'football' not in item.get('description','').lower() and 'soccer' not in item.get('description','').lower():continue
   qid=item['id']
   ent=get('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json').json()
   claims=ent['entities'][qid]['claims']
   if 'P154' not in claims:continue
   filename=claims['P154'][0]['mainsnak']['datavalue']['value']
   src='https://commons.wikimedia.org/wiki/Special:Redirect/file/'+urllib.parse.quote(filename)
   return download(t,out,src,{'wikidata':qid,'file':filename})
 except Exception as exc:out['wikidata_error']=str(exc)[:90]
 try:
  res=get('https://commons.wikimedia.org/w/api.php',{'action':'query','list':'search','srsearch':'"'+name+'" football logo','srnamespace':'6','format':'json','srlimit':4}).json()
  for item in res.get('query',{}).get('search',[]):
   title=item['title'];ts=set(norm(title).split());ws=set(norm(name).split())
   if len(ts&ws)<max(1,round(len(ws)*.60)) or not any(x in title.lower() for x in ['logo','crest','emblem']):continue
   if not title.lower().endswith(('.png','.svg','.jpg','.jpeg','.webp')):continue
   src='https://commons.wikimedia.org/wiki/Special:Redirect/file/'+urllib.parse.quote(title.split(':',1)[-1])
   return download(t,out,src,{'commons_title':title})
 except Exception as exc:out['commons_error']=str(exc)[:90]
 return out
def download(t,out,url,source):
 try:
  r=get(url);raw=r.content
  if raw.lstrip().startswith(b'<svg') or b'<svg' in raw[:1000]:raw=cairosvg.svg2png(bytestring=raw,output_width=480)
  im=Image.open(io.BytesIO(raw)).convert('RGBA')
  if im.width<60 or im.height<60 or max(im.size)/min(im.size)>3:raise ValueError('bad logo aspect')
  bbox=im.getchannel('A').getbbox()
  if bbox:im=im.crop(bbox)
  im.thumbnail((96,80),Image.Resampling.LANCZOS)
  # muted background from real crest color to conform to colored flag aesthetic
  px=[p for p in im.resize((80,80)).getdata() if p[3]>200 and max(p[:3])-min(p[:3])>55]
  if px:
   color=max(px,key=lambda x:max(x[:3])-min(x[:3]))[:3]
   background=tuple(int(.23*x+.77*240) for x in color)
  else:background=(220,225,225)
  dest=ROOT/(str(t['id'])+'.png')
  bg=Image.new('RGBA',(120,96),(*background,255))
  bg.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  bg.convert('RGB').save(dest,optimize=True)
  assert dest.stat().st_size>900
  return {**out,'status':'SOURCED_LOGO_CANDIDATE','source':url,'sourceMetadata':source,
          'url':'https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-d4-d5-v17-crests-fast/'+dest.as_posix(),
          'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'size':[120,96]}
 except Exception as e:return {**out,'status':'FETCH_FAILED','source':url,'error':str(e)[:140]}
with concurrent.futures.ThreadPoolExecutor(max_workers=18) as pool:
 records=list(pool.map(locate,ROSTER))
for x in records:print(x['name'],x['status'],flush=True)
(ROOT/'fast_crest_status.json').write_text(json.dumps({'assets':records,'count_sourced':sum(x['status']=='SOURCED_LOGO_CANDIDATE' for x in records),'count_parent':sum(x['status']=='PARENT_REUSED_IN_JSON' for x in records)},ensure_ascii=False,indent=2))
