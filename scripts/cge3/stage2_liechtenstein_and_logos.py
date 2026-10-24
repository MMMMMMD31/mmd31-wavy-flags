#!/usr/bin/env python3
import requests,io,hashlib,json,collections
from PIL import Image
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
s=requests.Session();s.headers.update({'User-Agent':'Mozilla/5.0 (MMD31 football research 2026)'})
R=Path('flags/clubs/standard/cge3-europe-2026-27');F=Path('flags/competition/cge3-europe-2026-27');A=Path('audit/cge3-europe-2026-27')
tasks=[
('2026102404101','FC Balzers','https://commons.wikimedia.org/wiki/Special:FilePath/FC%20Balzers.png'),
('2026102404103','FC Ruggell','https://www.footballlogosandkits.com/images_esc3/UEFA/LIECHTENSTEIN/plantillas/LOGO-FC%20RUGGELL-FR.png'),
('2026102404104','FC Schaan','https://commons.wikimedia.org/wiki/Special:FilePath/FC%20Schaan.png'),
('2026102404106','FC Triesenberg','https://www.footballlogosandkits.com/images_esc3/UEFA/LIECHTENSTEIN/plantillas/LOGO-FC%20TRIESENBERG-FR.png')]
def get(u):
 r=s.get(u,timeout=35);r.raise_for_status()
 assert 900<len(r.content)<7_000_000
 return r.content
def render(b):
 im=Image.open(io.BytesIO(b));im.load();im=im.convert('RGBA')
 if max(im.size)/min(im.size)>3:raise ValueError('Suspicious badge aspect ratio')
 bbox=im.getchannel('A').getbbox()
 if bbox:im=im.crop(bbox)
 colors=collections.Counter((r//30,g//30,bl//30) for r,g,bl,a in im.getdata() if a>120 and max(r,g,bl)-min(r,g,bl)>50)
 c=colors.most_common(1)[0][0] if colors else (5,5,5)
 bg=tuple(round(255*.50+(v*30+15)*.50) for v in c)
 out=Image.new('RGBA',(120,96),bg+(255,))
 im.thumbnail((104,84),Image.Resampling.LANCZOS)
 out.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 b=io.BytesIO();out.convert('RGB').save(b,'PNG',optimize=True);return b.getvalue()
records=[]
for tid,name,url in tasks:
 dst=R/(tid+'.png');rec={'id':tid,'name':name,'source':url,'status':'UNVERIFIED'}
 try:
  assert not dst.exists()
  output=render(get(url))
  dst.write_bytes(output);rec.update(status='PUBLISHED',sha256=hashlib.sha256(output).hexdigest())
 except Exception as e:rec['error']=str(e)[:160]
 records.append(rec);print('BADGE',name,rec['status'],rec.get('error',''),flush=True)
logo=[
('LI_federation.png','https://commons.wikimedia.org/wiki/Special:FilePath/Logo%20Liechtensteiner%20Fussballverband.jpg','LFV'),
('AT_cup_federation.png','https://www.oefb.at/assets/oefb3/images/menu-logo_2025.png','ÖFB')]
for name,url,label in logo:
 rec={'name':name,'source':url,'status':'MISSING','organisation':label}
 try:
  im=Image.open(io.BytesIO(get(url)));im.load()
  im.thumbnail((600,600),Image.Resampling.LANCZOS);im=im.convert('RGBA')
  dest=F/name;im.save(dest,'PNG',optimize=True)
  rec.update(status='PUBLISHED',sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),dimensions=list(im.size))
 except Exception as e:rec['error']=str(e)[:160]
 records.append(rec);print('LOGO',name,rec['status'],rec.get('error',''),flush=True)
# Switzerland federation logo from the actual federation crest library, not Swiss Football League sponsor.
rec={'name':'CH_cup_federation.png','source_page':'https://football-logos.cc/switzerland/swiss-football-association/','status':'MISSING','organisation':'Association Suisse de Football'}
try:
 page=s.get(rec['source_page'],timeout=25);page.raise_for_status()
 h=BeautifulSoup(page.content,'html.parser'); candidates=[]
 for im in h.find_all('img'):
  alt=(im.get('alt') or '').lower()
  if 'swiss football association' not in alt:continue
  u=im.get('src') or im.get('data-src')
  if u:candidates.append(urljoin(rec['source_page'],u))
 if not candidates:raise ValueError('No unique Swiss FA image detected')
 for u in candidates:
  try:
   im=Image.open(io.BytesIO(get(u)));im.load()
   if min(im.size)<48:continue
   im.thumbnail((600,600),Image.Resampling.LANCZOS)
   dst=F/rec['name'];im.convert('RGBA').save(dst,'PNG',optimize=True)
   rec.update(status='PUBLISHED',source_url=u,sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),dimensions=list(im.size));break
  except Exception as e:rec['error']=str(e)[:150]
except Exception as e:rec['error']=str(e)[:160]
records.append(rec);print('LOGO Swiss FA',rec['status'],rec.get('error',''))
A.joinpath('stage2_badge_and_federation_completion.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
