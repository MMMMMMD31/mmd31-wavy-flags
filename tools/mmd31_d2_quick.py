#!/usr/bin/env python3
"""Fast targeted follow-up: FotMob official club entities and SofaScore identity registries."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests,io,json,hashlib,time
from PIL import Image
s=Path('tools/mmd31_central_europe_d2_badges.py').read_text()
ns={'__name__':'cge_badges_library'}
# Load only data and helpers; don't execute prior bulk jobs
head=s[:s.index('from concurrent.futures import ThreadPoolExecutor, as_completed')]
exec(compile(head,'source_part','exec'),ns)
data=ns['DATA'];alias_match=ns['acceptable'];backdrop=ns['backdrop'];valid=ns['valid_image']
ROOT=Path('docs/central-europe-d2-2026-27/quick')
ROOT.mkdir(parents=True,exist_ok=True)
sess=requests.Session();sess.headers.update({'User-Agent':'Mozilla/5.0 MMD31 badge verification'})
def req(url,params=None):
 try:
  r=sess.get(url,params=params,timeout=(3,6))
  return r if r.status_code==200 else None
 except Exception:return None
def query(ent):
 nation,tid,name,alias=ent
 result={'nation':nation,'teamId':tid,'name':name,'status':'NOT_FOUND','source':'','matched_name':'','image_url':'','png_url':''}
 for q in [alias,name]:
  for endpoint in ('https://www.fotmob.com/api/searchData','https://www.fotmob.com/api/data/search/suggest','https://api.sofascore.com/api/v1/search/all'):
   resp=req(endpoint,{'term':q,'hits':30,'lang':'en'} if 'suggest' in endpoint else ({'q':q} if 'sofascore' in endpoint else {'term':q}))
   if not resp:continue
   try:
    j=resp.json()
    arr=(j.get('team',[]) if isinstance(j,dict) else []) if endpoint.endswith('searchData') else ((j.get('teams',[]) if isinstance(j,dict) else []) if 'suggest' in endpoint else j.get('results',[]))
    if 'suggest' in endpoint and isinstance(j,list):arr=[x for b in j if isinstance(b,dict) for x in b.get('suggestions',[])]
    for item in arr:
     if not isinstance(item,dict):continue
     if 'type' in item and item['type']!='team':continue
     entity=item.get('entity',{}) if isinstance(item.get('entity'),dict) else item
     found=entity.get('name','')
     if not alias_match(name,alias,found):continue
     fid=entity.get('id')
     if not fid:continue
     url='https://api.sofascore.com/api/v1/team/'+str(fid)+'/image' if 'sofascore' in endpoint else 'https://images.fotmob.com/image_resources/logo/teamlogo/'+str(fid)+'.png'
     image=req(url)
     if not image:continue
     im=valid(image.content)
     if im is None:continue
     out=ROOT/(str(tid)+'.png')
     backdrop(im).save(out,'PNG',optimize=True)
     result.update(status='VERIFIED_PROVIDER_MATCH',source=endpoint,matched_name=found,image_url=url,png_url=f'https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-central-europe-d2-20261025/docs/central-europe-d2-2026-27/quick/{tid}.png',sha256=hashlib.sha256(out.read_bytes()).hexdigest(),width=120,height=96)
     return result
   except Exception:pass
 return result
with ThreadPoolExecutor(max_workers=12) as pool:
 a=list(pool.map(query,data))
Path('docs/central-europe-d2-2026-27/quick-manifest.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
print('Found',sum(x['status'].startswith('VERIFIED') for x in a),'of',len(a),flush=True)
