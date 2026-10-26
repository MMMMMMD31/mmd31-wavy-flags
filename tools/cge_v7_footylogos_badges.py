#!/usr/bin/env python3
"""Download verified crest assets from FootyLogos country collections (with attribution).
Only exact or unambiguous high-confidence name matches from same-country catalog.
"""
import json,re,time,unicodedata,hashlib,colorsys
from pathlib import Path
from io import BytesIO
from urllib.parse import urljoin
from difflib import SequenceMatcher
import requests,bs4,cairosvg
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/cge-v7-d3-2026-27/v3'
OUT.mkdir(parents=True,exist_ok=True)
HEAD={'User-Agent':'MMD31-CGE-Logos/1.0 (attribution: FootyLogos.com; github.com/MMMMMMD31/mmd31-wavy-flags)'}
s=requests.Session();s.headers.update(HEAD)
countries={'Wales':'wales','Norway':'norway','Iceland':'iceland','Faroe Islands':'faroe-islands','Czechia':'czechia','Poland':'poland','Turkey':'turkey','Armenia':'armenia','Azerbaijan':'azerbaijan','Israel':'israel','Kazakhstan':'kazakhstan'}
skipwords={'fk','sk','fc','il','if','cf','af','sc','bk','football','club','fotball','footballclub','ii','b','team'}
def norm(x):
 x=unicodedata.normalize('NFKD',x.casefold())
 x=''.join(c for c in x if not unicodedata.combining(c))
 return re.sub(r'[^a-z0-9]','',x)
def words(x):
 x=unicodedata.normalize('NFKD',x.casefold())
 x=''.join(c for c in x if not unicodedata.combining(c))
 return [w for w in re.findall('[a-z0-9]+',x) if w not in skipwords]
def sim(a,b):
 wa=words(a);wb=words(b)
 if norm(a)==norm(b):return 1.0
 shared=set(wa)&set(wb)
 score=.45*SequenceMatcher(None,norm(a),norm(b)).ratio()+.55*(len(shared)/max(len(set(wa)),len(set(wb)),1))
 return score
def download(url):
 r=s.get(url,timeout=22,allow_redirects=True);r.raise_for_status()
 if len(r.content)>4_000_000:raise ValueError('Too many image bytes')
 if r.content.lstrip().lower().startswith(b'<!doctype'):raise ValueError('Received HTML not image')
 return r.content,r.headers.get('content-type','')
def png(raw):
 if b'<svg' in raw[:600].lower():raw=cairosvg.svg2png(bytestring=raw,output_width=600)
 logo=Image.open(BytesIO(raw)).convert('RGBA')
 if min(logo.size)<40:raise ValueError('Low image dimensions')
 logo.thumbnail((106,82),Image.Resampling.LANCZOS)
 pal={}
 for i,(r,g,b,a) in enumerate(logo.getdata()):
  if i%6 or a<130:continue
  h,sv,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
  if sv>.4 and .14<v<.97:
   t=(r//24,g//24,b//24);pal[t]=pal.get(t,0)+1
 q=max(pal,key=pal.get) if pal else None
 bg=tuple(int(.65*255+.35*(min(255,v*24+12))) for v in q) if q else (241,241,244)
 img=Image.new('RGBA',(120,96),bg+(255,))
 img.alpha_composite(logo,((120-logo.width)//2,(96-logo.height)//2))
 return img.convert('RGB')
def get_catalog(country,slug):
 url=f'https://www.footylogos.com/country/{slug}'
 r=s.get(url,timeout=22)
 r.raise_for_status()
 soup=bs4.BeautifulSoup(r.content.decode('utf-8'),'html.parser')
 logos=[]
 for a in soup.select('a[href*="/logos/"]'):
  href=a.get('href','')
  if '/logos/' not in href or href.count('/logos/')!=1:continue
  raw=' '.join(a.stripped_strings)
  if 'club' not in raw.lower():continue
  raw=re.sub(r'^Club\s*[·•]\s*'+re.escape(country)+r'\s*','',raw,flags=re.I)
  raw=re.sub(r'\bPNG\s*SVG\b|\bPNG\b|\bSVG\b','',raw,flags=re.I)
  raw=re.sub(r'\b\d+\s*variants?\b','',raw,flags=re.I).strip()
  if not raw:continue
  logos.append({'name':raw,'url':urljoin(url,href)})
 seen={x['url']:x for x in logos}
 return list(seen.values())
def choose(candidates,name):
 ranks=sorted([(sim(name,c['name']),c) for c in candidates],key=lambda p:p[0],reverse=True)
 if not ranks:return None,[]
 best=ranks[0]
 # No accepting a geographic 'name prefix' for another distinct team.
 if best[0]<.84 or (len(ranks)>1 and best[0]-ranks[1][0]<.12):
  return None,ranks[:4]
 return best,ranks[:4]
def fetch_logo(landing,name):
 page=s.get(landing,timeout=20);page.raise_for_status()
 soup=bs4.BeautifulSoup(page.content.decode('utf-8'),'html.parser')
 # First try documented official transparent PNG download endpoint.
 dl=landing+'?download=png'
 try:
  raw,typ=download(dl)
  img=png(raw)
  return img,dl
 except Exception:
  pass
 # Fallback explicit image from main crest card, else OpenGraph image.
 links=[]
 for im in soup.find_all('img'):
  alt=im.get('alt','')
  if 'logo' in alt.lower() and sim(name,alt.replace('logo',''))>.7:
   src=im.get('src') or im.get('data-src')
   if src:links.append(urljoin(landing,src))
 for m in soup.select('meta[property="og:image"]'):
  if m.get('content'):links.append(urljoin(landing,m.get('content')))
 for l in dict.fromkeys(links):
  try:
   raw,typ=download(l)
   return png(raw),l
  except Exception:continue
 raise ValueError('No usable transparent PNG/image on verified team page')
targets=[]
for path in ['tools/cge_v7_badges_missing61.txt','tools/cge_v7_badges_missing80.txt']:
 for line in (ROOT/path).read_text(encoding='utf-8').splitlines():
  if not line.strip():continue
  tid,country,name=line.split('|',2);targets.append({'id':int(tid),'country':country,'name':name,'status':'MISSING'})
catalog={}
for country,slug in countries.items():
 try:catalog[country]=get_catalog(country,slug);print('Country',country,len(catalog[country]),flush=True)
 except Exception as e:catalog[country]=[];print('ERROR CATALOG',country,str(e)[:160],flush=True)
records=[]
for item in targets:
 tid,country,name=item['id'],item['country'],item['name']
 best,rank=choose(catalog[country],name)
 item['suggestions']=[{'score':round(v,3),'title':d['name'],'page':d['url']} for v,d in rank]
 if best:
  v,entry=best
  try:
   img,url=fetch_logo(entry['url'],name)
   file=OUT/(str(tid)+'.png');img.save(file,optimize=True)
   assert Image.open(file).size==(120,96)
   item.update(status='VERIFIED_SAME_COUNTRY_CATALOG',source_url=url,page=entry['url'],source_name=entry['name'],score=round(v,3),sha256=hashlib.sha256(file.read_bytes()).hexdigest())
  except Exception as e:
   item['error']=str(e)[:250]
 records.append(item)
 if len(records)%20==0:print('Processed',len(records),'accepted',sum(x['status'].startswith('VERIFIED') for x in records),flush=True)
 time.sleep(.06)
(OUT/'manifest.json').write_text(json.dumps({'count':len(records),'success':sum(x['status'].startswith('VERIFIED') for x in records),'items':records},ensure_ascii=False,indent=2),encoding='utf8')
print('DONE',len(records),'success',sum(x['status'].startswith('VERIFIED') for x in records))
