#!/usr/bin/env python3
"""Find verifiable football crest logos via linked Wikipedia club articles and Wikimedia Commons.
Uses club Wikidata QID -> exact Wikipedia article, then linked File: logos.
Never accepts stadium / player photos. All failures stay unassigned.
"""
from pathlib import Path
from urllib.parse import quote
from io import BytesIO
import json,re,time,hashlib,unicodedata,colorsys
import requests,cairosvg
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/cge-v7-d3-2026-27/v4'
OUT.mkdir(parents=True,exist_ok=True)
HEAD={'User-Agent':'MMD31-CGEBadgeBot/1.2 (Wikimedia club article logo verification, github.com/MMMMMMD31/mmd31-wavy-flags)'}
sess=requests.Session();sess.headers.update(HEAD)
LOCAL={'Czechia':['cswiki','enwiki'],'Poland':['plwiki','enwiki'],'Norway':['nowiki','enwiki'],'Iceland':['iswiki','enwiki'],'Faroe Islands':['fowiki','dawiki','enwiki'],'Armenia':['hywiki','enwiki'],'Azerbaijan':['azwiki','enwiki'],'Israel':['hewiki','enwiki'],'Kazakhstan':['ruwiki','kkwiki','enwiki'],'Turkey':['trwiki','enwiki'],'Wales':['enwiki']}
LOCO=['logo','crest','emblem','znak','herb','logotyp','wappen','symbol','insigne','badge','escudo','merki','skjold','vapen','loki','logó','emblema','klubbmerke','klubblogo','armoir']
NOT=['commons-logo','commonslogo','wikimedia','wikipedia-logo','flag_of','map_','kit_body','kit_left','kit_right','football_icon','icon_','sponsor','stadion','stadium','jersey','shirt']
def api(url,params):
 r=sess.get(url,params=params,timeout=14);r.raise_for_status();return r.json()
def norm(t):
 t=unicodedata.normalize('NFKD',t.lower())
 return re.sub('[^a-z0-9]','', ''.join(c for c in t if not unicodedata.combining(c)))
def common(x,y):
 x=norm(x);y=norm(y)
 # match distinctive substring of canonical club name
 return (x in y or y in x) and len(x)>=5
def logo_score(filename,name):
 f=norm(filename);n=norm(name)
 if any(norm(b) in f for b in NOT):return 0
 if not any(norm(w) in f for w in LOCO):return 0
 if f.endswith('svg') or f.endswith('png') or f.endswith('jpg'): pass
 tokens=[norm(t) for t in re.split('[\\s\\-/_]+',name) if len(norm(t))>=5 and norm(t) not in ('football','futebol','futbol','sport','club','fotball','united','athletic','tor shavn'.replace(' ',''))]
 matched=sum(1 for t in tokens if t in f)
 if matched: return 3+matched
 # Could be generically named crest in this club's own Wikipedia article, limited to one.
 return 1
def fetch_qid(qid):
 x=api('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':qid,'props':'sitelinks','format':'json'})
 return x.get('entities',{}).get(qid,{}).get('sitelinks',{})
def article_images(country,sitelinks):
 for k in LOCAL.get(country,['enwiki']):
  if k not in sitelinks:continue
  title=sitelinks[k]['title'];lang=k[:-4]
  url=f'https://{lang}.wikipedia.org/w/api.php'
  try:
   x=api(url,{'action':'query','titles':title,'prop':'images','imlimit':'max','format':'json'})
   pages=x.get('query',{}).get('pages',{})
   for page in pages.values():
    titles=[r['title'][5:] for r in page.get('images',[]) if r.get('title','').startswith('File:')]
    if titles:yield lang,title,titles
  except Exception:continue
def download_file(filename,langs):
 for host in ['commons']+list(langs):
  url=f'https://{host}.wikimedia.org/wiki/Special:Redirect/file/'+quote(filename.replace(' ','_')) if host=='commons' else f'https://{host}.wikipedia.org/wiki/Special:Redirect/file/'+quote(filename.replace(' ','_'))
  try:
   r=sess.get(url,timeout=18);r.raise_for_status();data=r.content
   if len(data)>2_500_000 or data[:100].lower().find(b'html')>=0:continue
   if b'<svg' not in data[:900].lower():
    im=Image.open(BytesIO(data))
    if min(im.size)<60:continue
   return data,url
  except Exception:continue
 raise ValueError('Logo file not retrievable from matching article')
def render(data):
 if b'<svg' in data[:800].lower():data=cairosvg.svg2png(bytestring=data,output_width=500)
 im=Image.open(BytesIO(data)).convert('RGBA')
 im.thumbnail((104,82),Image.Resampling.LANCZOS)
 colors={}
 for i,(r,g,b,a) in enumerate(im.getdata()):
  if i%7 or a<150:continue
  h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
  if s>.37 and .16<v<.96:
   p=(r//24,g//24,b//24);colors[p]=colors.get(p,0)+1
 if colors:
  p=max(colors,key=colors.get);bg=tuple(int(255*.66+.34*(q*24+12)) for q in p)
 else:bg=(240,241,244)
 target=Image.new('RGBA',(120,96),bg+(255,))
 target.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return target.convert('RGB')
def readmanifest(n):
 return json.loads((ROOT/f'docs/cge-v7-d3-2026-27/{n}/manifest.json').read_text(encoding='utf8'))
prev2=readmanifest('v2'); prev3=readmanifest('v3')
candidates={x['id']:x for x in prev2['clubs']}
done={x['id'] for x in prev2['clubs'] if x['status']!='MISSING'}|{x['id'] for x in prev3['items'] if x['status']!='MISSING'}
out=[]
for i,(id,c) in enumerate(candidates.items()):
 name=c['name'];country=c['country']
 if id in done:
  out.append({'id':id,'name':name,'status':'ALREADY_PUBLISHED'})
  continue
 row={'id':id,'name':name,'country':country,'status':'MISSING','qids':[]}
 try:
  for cand in c.get('candidates',[])[:3]:
   qid=cand.get('id')
   if not qid:continue
   row['qids'].append(qid)
   sl=fetch_qid(qid)
   if not sl:continue
   for lang,title,names in article_images(country,sl):
    logos=sorted([(logo_score(x,name),x) for x in names if any(x.lower().endswith(e) for e in ('.svg','.png','.jpg','.jpeg','.webp'))],reverse=True)
    logos=[x for x in logos if x[0]>=1]
    if not logos:continue
    chosen=[p for p in logos if p[0]>=4] or ([logos[0]] if len(logos)==1 and logos[0][0]>=1 else [])
    if not chosen:continue
    for score,file in chosen[:3]:
     try:
      data,url=download_file(file,[lang])
      image=render(data)
      file_out=OUT/(str(id)+'.png')
      image.save(file_out,optimize=True)
      row.update(status='VERIFIED_WIKI_ARTICLE_LOGO',source=url,article=f'https://{lang}.wikipedia.org/wiki/{quote(title.replace(" ","_"))}',filename=file,score=score,wikidata_qid=qid,sha256=hashlib.sha256(file_out.read_bytes()).hexdigest())
      break
     except Exception as e:row['error']=str(e)[:220]
    if row['status']!='MISSING':break
   if row['status']!='MISSING':break
 except Exception as e:row['error']=str(e)[:250]
 out.append(row)
 if (i+1)%20==0:print('Scanned',i+1,'new',sum(x['status']=='VERIFIED_WIKI_ARTICLE_LOGO' for x in out),flush=True)
 time.sleep(.12)
(OUT/'manifest.json').write_text(json.dumps({'count':len(out),'success':sum(x['status']=='VERIFIED_WIKI_ARTICLE_LOGO' for x in out),'items':out},ensure_ascii=False,indent=2),encoding='utf8')
print('DONE',len(out),sum(x['status']=='VERIFIED_WIKI_ARTICLE_LOGO' for x in out))
