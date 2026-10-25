#!/usr/bin/env python3
"""Fetch exact-match V13 crests from checked FootyLogos pages, in small independent batches."""
import sys,json,io,hashlib,re,time,unicodedata
from pathlib import Path
import requests
from PIL import Image
batch=sys.argv[1] if len(sys.argv)>1 else 'CZ'
assert batch in {'CZ','HU'}
DATA={
 'CZ':[
 (1971262100005,'FC Vysočina Jihlava','fc-vysocina-jihlava',(223,234,251)),
 (1971262100008,'FK Třinec','fk-trinec',(251,232,232)),
 (1971262100009,'FK VIAGEM Ústí nad Labem','fk-viagem-usti-nad-labem',(220,235,248)),
 (1971262100011,'Fotbal Příbram','fotbal-pribram',(230,244,231)),
 (1971262100012,'MFK Karviná','mfk-karvina',(221,246,228)),
 (1971262100016,'Slezský FC Opava','slezsky-fc-opava',(249,244,212))],
 'HU':[
 (1971262100201,'FC Nagykanizsa','fc-nagykanizsa',(233,239,248)),
 (1971262100204,'HR-Rent Kozármisleny','hr-rent-kozarmisleny',(242,232,246)),
 (1971262100211,'Szentlőrinc SE','szentlorinc-se',(246,230,234)),
 (1971262100216,'Mezőkövesd Zsóry FC','mezokovesd-zsory-fc',(252,246,211))]}
BASE='https://www.footylogos.com'
OUT=Path('docs/central-europe-d2-2026-27/verified');OUT.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({'User-Agent':'MMD31-CGE-V13-crest-audit/1.0','Accept':'image/png,image/*,text/html'})
report=[]
for tid,name,slug,bg in DATA[batch]:
 result={'teamId':tid,'name':name,'page':f'{BASE}/logos/{slug}','status':'NOT_FOUND','source':'FootyLogos verified named club page','source_png':f'{BASE}/dls/logo/{slug}.png'}
 try:
  page=s.get(result['page'],timeout=(4,10))
  if page.status_code!=200 or unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower().split()[0] not in unicodedata.normalize('NFKD',page.text).encode('ascii','ignore').decode().lower():
   result.update(status='PAGE_NOT_VERIFIED',http_status=page.status_code);report.append(result);continue
  r=s.get(result['source_png'],timeout=(4,13))
  if r.status_code!=200 or not r.content.startswith(b'\x89PNG\r\n\x1a\n'):
   result.update(status='INVALID_IMAGE_RESPONSE',http_status=r.status_code);report.append(result);continue
  im=Image.open(io.BytesIO(r.content)).convert('RGBA')
  if im.width<80 or im.height<80:result['status']='IMAGE_TOO_SMALL';report.append(result);continue
  im.thumbnail((98,82),Image.Resampling.LANCZOS)
  canvas=Image.new('RGBA',(120,96),bg+(255,))
  canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  p=OUT/f'{tid}.png';canvas.convert('RGB').save(p,optimize=True)
  result.update(status='VERIFIED_CREST',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),width=120,height=96,flagUrl=f'https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-central-europe-d2-20261025/docs/central-europe-d2-2026-27/verified/{tid}.png',source_pixels=[r for r in [im.width,im.height]])
 except Exception as e:result.update(status='ERROR',error=str(e)[:220])
 report.append(result);print(tid,result['status'],flush=True)
 time.sleep(.15)
(Path('docs/central-europe-d2-2026-27')/f'manifest-footylogos-{batch}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('FOUND',sum(x['status']=='VERIFIED_CREST' for x in report),'OF',len(report))
