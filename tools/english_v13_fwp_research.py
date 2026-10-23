import json,re,requests,concurrent.futures,unicodedata,threading
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pathlib import Path
missing=json.loads(Path('docs/english-clubs-2026-27/wiki-v13/manifest.json').read_text())
todo=[m for m in missing['files'] if not m['status'].startswith('PUBLISHED')]
assert len(todo)==55
url='https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-english-ratings-audit-2026-27/docs/english-ratings-research/coverage_2026_10_23.json'
r=requests.get(url,timeout=30);r.raise_for_status()
urls=[x['url'] for x in r.json()['sources'] if x.get('url','').startswith('https://www.footballwebpages.co.uk')]
assert len(urls)>20,len(urls)
aliases={'South Park (Reigate)':['South Park','South Park Reigate'],'Thackley Association':['Thackley'],'West Bridgford Colts':['West Bridgford'],'Windsor & Eton':['Windsor and Eton'],'Torpoint Athletic':['Torpoint'],'Bugbrooke St Michael':['Bugbrooke St Michaels'],'Pershore Town 88':['Pershore Town'],'East Cowes Victoria Athletic':['East Cowes Victoria'],'Larkfield & New Hythe':['Larkfield and New Hythe'],'Winsford United':['Winsford'],'Northwood':['Northwood'],'South Liverpool':['South Liverpool']}
def norm(x):
 x=unicodedata.normalize('NFKD',x).lower().replace('&','and')
 x=re.sub(r"(?i)\\bfootball club\\b|\\ba\\.?f\\.?c\\.?\\b|\\bf\\.?c\\.?\\b",'',x)
 return re.sub('[^a-z0-9]','',x)
def fetch(url):
 try:
  s=requests.Session();s.headers['User-Agent']='Mozilla/5.0 (compatible; MMD31 2026-27 nonleague football crest research)'
  res=s.get(url,timeout=25)
  if res.status_code!=200:return {'url':url,'status':res.status_code,'logos':[]}
  so=BeautifulSoup(res.text,'html.parser')
  logos=[]
  for t in so.select('img[alt]'):
   name=t.get('alt') or ''
   if not name.lower().endswith(' badge'):continue
   team=name[:-6].strip()
   src=urljoin(url,t.get('src') or '')
   if 'graphics/teams/' in src:
    logos.append({'name':team,'url':src})
  return {'url':url,'status':200,'logos':logos}
 except Exception as e:return {'url':url,'error':str(e)[:100],'logos':[]}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: pages=list(ex.map(fetch,urls))
lookup=[dict(x,league_url=p['url']) for p in pages for x in p['logos']]
records=[]
for m in todo:
 variants=[m['name']]+aliases.get(m['name'],[])
 target={norm(t) for t in variants}
 candidates=[l for l in lookup if norm(l['name']) in target]
 if len(set(q['url'] for q in candidates))>1:
  # Multiple sources for same club are okay; keep each league URL to verify.
  pass
 records.append({'id':m['id'],'name':m['name'],'matches':candidates})
output={'sources':len(urls),'pages_loaded':sum(p['status']==200 for p in pages if 'status' in p),'logos_seen':len(lookup),'matched_clubs':sum(bool(x['matches']) for x in records),'records':records,'source_pages':pages}
p=Path('docs/english-v13');p.mkdir(exist_ok=True,parents=True)
(p/'footballwebpages_missing_55_images.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
print('FWP MATCHED',output['matched_clubs'],'OF',len(records),flush=True)
print('UNMATCHED',[r['name'] for r in records if not r['matches']],flush=True)
