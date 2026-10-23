import io,json,re,unicodedata,hashlib,difflib
from pathlib import Path
from urllib.parse import urljoin
from collections import Counter
import requests
from bs4 import BeautifulSoup
from PIL import Image
ROOT=Path('docs/german-clubs-2026-27/v13-d6');ROOT.mkdir(parents=True,exist_ok=True)
manifest=json.loads(Path('tools/german_v13_d6_129_source_clubs.json').read_text())
sites={'Landesliga Schleswig':'728','Landesliga Holstein':'726','Landesliga Niedersachsen Braunschweig':'706','Landesliga Niedersachsen Hannover':'712','Landesliga Niedersachsen Lüneburg':'714','Landesliga Niedersachsen Weser-Ems':'708','Landesliga Bremen':'692'}
suffix={'728':'Ergebnisse-Landesliga-Schleswig-Fussball-2026-2027','726':'Ergebnisse-Landesliga-Holstein-Fussball-2026-2027','706':'Ergebnisse-Landesliga-Niedersachsen-Braunschweig-Fussball-2026-2027','712':'Ergebnisse-Landesliga-Niedersachsen-Hannover-Fussball-2026-2027','714':'Ergebnisse-Landesliga-Niedersachsen-Lueneburg-Fussball-2026-2027','708':'Ergebnisse-Landesliga-Niedersachsen-Weser-Ems-2026-2027','692':'Ergebnisse-Landesliga-Bremen-Fussball-2026-2027'}
s=requests.Session();s.headers.update({'User-Agent':'Mozilla/5.0 (MMD31 club crest validation)'})
def clean(v):
 v=unicodedata.normalize('NFKD',v).casefold().replace('ß','ss')
 return ' '.join(''.join(c if c.isalnum() else ' ' for c in v).split())
def images(group):
 n=sites[group];url='https://www.ndr.de/sport/ergebnisse/'+suffix[n]+',fussballmaenner-'+n+'.html'
 r=s.get(url,timeout=30);r.raise_for_status();soup=BeautifulSoup(r.text,'html.parser');found=[]
 for im in soup.find_all('img'):
  alt=im.get('alt','')
  if 'wappen' not in alt.lower():continue
  src=im.get('src') or im.get('data-src') or im.get('data-original')
  if not src:continue
  td=im.find_parent('td')
  label=alt.replace('Wappen','').strip()
  text=td.get_text(' ',strip=True) if td else ''
  found.append({'alt':label,'text':text,'src':urljoin(url,src)})
 return found
ignore={'fc','sv','sc','tsv','ii','iii','1','08','sg','spvgg','tus','vfb','vfl','ssv'}
def score(name,im):
 a,b,c=clean(name),clean(im['alt']),clean(im['text'])
 ta=set(a.split())-ignore;tb=set(b.split())-ignore
 if not ta.intersection(tb):return 0
 return max(difflib.SequenceMatcher(None,a,b).ratio(),.8*difflib.SequenceMatcher(None,a,c).ratio(),.55*len(ta&tb)/max(1,len(ta))+.35*difflib.SequenceMatcher(None,a,b).ratio())
def render(raw):
 im=Image.open(io.BytesIO(raw)).convert('RGBA')
 box=im.getchannel('A').getbbox()
 if box:im=im.crop(box)
 if min(im.size)<18:raise ValueError('small image')
 im.thumbnail((104,84),Image.Resampling.LANCZOS)
 pix=Counter((r//40,g//40,b//40) for r,g,b,a in im.getdata() if a>90 and max(r,g,b)-min(r,g,b)>36)
 if pix:
  p=pix.most_common(1)[0][0];bg=tuple(int(.82*min(255,x*40+20)+.18*255) for x in p)
 else:bg=(212,218,225)
 out=Image.new('RGBA',(120,96),bg+(255,));out.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return out.convert('RGB'),bg
pages={}
for group in sites:
 try:
  pages[group]=images(group);print('SOURCE',group,len(pages[group]),[x['alt'] for x in pages[group][:3]],flush=True)
 except Exception as e:pages[group]=[];print('ERROR',group,e,flush=True)
assets=[];skipped=[]
for row in manifest:
 group=row['group'];name=row['name'];tid=row['id']
 if group not in sites:
  skipped.append({'id':tid,'name':name,'reason':'no NDR source'});continue
 ranks=sorted(((score(name,x),x) for x in pages[group]),key=lambda x:x[0],reverse=True)
 if not ranks:skipped.append({'id':tid,'name':name,'reason':'no image found'});continue
 value,x=ranks[0]
 if value<.75 or (len(ranks)>1 and ranks[1][0]>value-.06 and ranks[1][1]['src']!=x['src']):
  skipped.append({'id':tid,'name':name,'reason':'ambiguous','best':x['alt'],'score':round(value,3)});continue
 try:
  r=s.get(x['src'],timeout=27);r.raise_for_status();pic,bg=render(r.content)
  path=ROOT/(str(tid)+'.png');pic.save(path,format='PNG',optimize=True)
  assets.append({'id':tid,'name':name,'source_url':x['src'],'source_alt':x['alt'],'match_score':round(value,3),'background_rgb':bg,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 except Exception as e:skipped.append({'id':tid,'name':name,'reason':str(e)})
print('CREATED',len(assets),'SKIPPED',len(skipped),flush=True)
(ROOT/'status.json').write_text(json.dumps({'created_count':len(assets),'status':'SOURCE_CANDIDATE_NEEDS_IDENTITY_REVIEW','assets':assets,'skipped':skipped},ensure_ascii=False,indent=2)+'\n')
if not assets:raise ValueError('No authentic crest images identified')
