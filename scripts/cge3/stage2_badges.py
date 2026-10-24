#!/usr/bin/env python3
"""CGE3 stage 2: real badge source collection. Never substitute an unrelated crest.
Sources catalogued; unsuccessfully matched crests are marked MISSING, not fabricated.
"""
import requests,re,io,json,hashlib,collections,unicodedata
from PIL import Image
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
ses=requests.Session();ses.headers.update({'User-Agent':'Mozilla/5.0 MMD31 Football Crest Verification'})
ROOT=Path('flags/clubs/standard/cge3-europe-2026-27')
A=Path('audit/cge3-europe-2026-27');A.mkdir(parents=True,exist_ok=True)
K={
'CH':('https://escudosfc.com.br/swit.htm',[
('2026102401101','FC Aarau',['aarau']),
('2026102401102','FC Wil 1900',['wil']),
('2026102401103','FC Winterthur',['winterthur']),
('2026102401104','Neuchâtel Xamax FCS',['neuchatel','xamax']),
('2026102401105','FC Rapperswil-Jona',['rapperswil']),
('2026102401106','SC Kriens',['kriens']),
('2026102401107','FC Stade-Lausanne-Ouchy',['stade lausanne','ouchy']),
('2026102401108','FC Stade Nyonnais',['nyonnais','nyon']),
('2026102401109','Yverdon Sport FC',['yverdon']),
('2026102401110','Étoile Carouge FC',['etoile carouge','carouge'])]),
'AT':('https://escudosfc.com.br/aut.htm',[
('2026102402101','FC Admira Wacker Mödling',['admira']),
('2026102402102','SKU Amstetten',['amstetten']),
('2026102402103','FC Blau-Weiß Linz',['blau-weiss linz','blau-weiss']),
('2026102402104','Floridsdorfer AC',['floridsdorfer','fac wien']),
('2026102402105','FC Wacker Innsbruck',['wacker innsbruck']),
('2026102402106','FC Liefering',['liefering']),
('2026102402107','First Vienna FC 1894',['first vienna']),
('2026102402108','Kapfenberger SV 1919',['kapfenberg']),
('2026102402109','SK Rapid Wien II',['rapid vienna','rapid wien']),
('2026102402110','SKN St. Pölten',['st. polten','st. pölten','polten']),
('2026102402111','SK Sturm Graz II',['sturm graz']),
('2026102402112','SW Bregenz',['bregenz']),
('2026102402113','SV Austria Salzburg',['austria salzburg']),
('2026102402114','FC Hertha Wels',['hertha wels']),
('2026102402115','Young Violets Austria Wien',['austria vienna','austria wien']),
('2026102402116','ASK Voitsberg',['voitsberg'])]),
'LI':('https://escudosfc.com.br/lie.htm',[
('2026102404101','FC Balzers',['balzers']),
('2026102404102','USV Eschen/Mauren',['eschen','mauren']),
('2026102404103','FC Ruggell',['ruggell']),
('2026102404104','FC Schaan',['schaan']),
('2026102404105','FC Triesen',['triesen']),
('2026102404106','FC Triesenberg',['triesenberg'])])
}
ALT={'CH':['https://football-logos.cc/switzerland/','https://www.footylogos.com/dls/league/swiss-challenge-league'],
'AT':['https://football-logos.cc/austria/'],
'LI':['https://football-logos.cc/liechtenstein/']}
def normal(s):
 return ''.join(x for x in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(x)).replace('-',' ').replace('_',' ')
def get(u):
 r=ses.get(u,timeout=25);r.raise_for_status()
 assert len(r.content)<8_000_000
 return r
def convert(blob):
 im=Image.open(io.BytesIO(blob));im.load();im=im.convert('RGBA')
 assert min(im.size)>=35,im.size
 if all(all(c>242 for c in im.getpixel((x,y))[:3]) for x,y in ((0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1))):
  pix=[]
  for r,g,b,a in im.getdata():pix.append((r,g,b,0 if min(r,g,b)>247 else a))
  im.putdata(pix)
 bbox=im.getchannel('A').getbbox()
 if bbox:im=im.crop(bbox)
 pix=collections.Counter((r//25,g//25,b//25) for r,g,b,a in im.getdata() if a>130 and max(r,g,b)-min(r,g,b)>37)
 k=pix.most_common(1)[0][0] if pix else (5,5,5)
 back=tuple(int(.48*(x*25+12)+.52*255) for x in k)
 cv=Image.new('RGBA',(120,96),back+(255,))
 im.thumbnail((104,84),Image.Resampling.LANCZOS)
 cv.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 out=io.BytesIO();cv.convert('RGB').save(out,'PNG',optimize=True)
 assert len(out.getvalue())>600
 return out.getvalue()
catalogs={}
for country,(url,clubs) in K.items():
 imgs=[]
 for page in [url]+ALT.get(country,[]):
  try:
   h=BeautifulSoup(get(page).content,'html.parser')
   items=[]
   for img in h.find_all('img'):
    u=img.get('src') or img.get('data-src')
    if not u or u.startswith('data:'):continue
    alt=' '.join(filter(None,[img.get('alt'),img.get('title')]))
    items.append((normal(alt),urljoin(page,u),page))
   imgs+=items
  except Exception as e:print('PAGE_FAILED',page,str(e)[:120])
 catalogs[country]=imgs
 print('INDEX',country,len(imgs),flush=True)
status=[]
for country,(url,clubs) in K.items():
 for tid,name,terms in clubs:
  dst=ROOT/(tid+'.png')
  assert not dst.exists()
  cand=[]
  for alt,src,page in catalogs[country]:
   hits=[t for t in terms if normal(t) in alt]
   if not hits:continue
   # Refuse a national team logo when looking for a club, and generic site badges.
   if 'federation' in alt or 'national' in alt:continue
   cand.append((len(max(hits,key=len)),alt,src,page))
  cand.sort(reverse=True)
  record={'country':country,'teamId':tid,'name':name,'status':'MISSING','candidates':len(cand)}
  errors=[]
  for _,alt,src,page in cand[:12]:
   try:
    b=convert(get(src).content)
    dst.write_bytes(b)
    record.update(status='PUBLISHED',source_url=src,source_page=page,source_alt=alt,sha256=hashlib.sha256(b).hexdigest(),size=len(b))
    break
   except Exception as e:errors.append(str(e)[:110])
  if errors:record['failed_candidates']=errors[:4]
  status.append(record)
  print('RESULT',country,tid,name,record['status'],record.get('source_alt',''),flush=True)
A.joinpath('stage2_new_club_badges.json').write_text(json.dumps({'total':len(status),'published':sum(x['status']=='PUBLISHED' for x in status),'clubs':status},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
