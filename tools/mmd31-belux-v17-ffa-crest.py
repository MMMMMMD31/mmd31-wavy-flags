#!/usr/bin/env python3
"""Selected FFA crests from identified image pages; do not substitute fictional badges."""
import json,hashlib,requests,io
from PIL import Image
from pathlib import Path
ROOT=Path('docs/belgian-d4-d5-2026-27/v17')
sources=[
 (1900262703033,'R Aywaille FC','https://vectorportal.com/storage/royal_aywaille_fc.jpg',(226,220,246)),
 (1900262703037,'FC Ganshoren','https://images.seeklogo.com/logo-png/38/1/fc-ganshoren-logo-png_seeklogo-387821.png',(212,235,208)),
 (1900262703038,'Union Hutoise','https://www.voetbalinbelgie.be/images/club_logo_van_voetbalvereniging_union-hutoise-r_uit_huy.png?v=20250716095358',(249,227,187)),
 (1900262703048,'UR Namur','https://cdn.freebiesupply.com/logos/large/2x/union-royale-namur-logo-png-transparent.png',(250,236,161))]
out=[]
for id,name,url,col in sources:
 z={'id':id,'name':name,'source':url,'status':'UNVERIFIED'}
 try:
  r=requests.get(url,timeout=20,headers={'User-Agent':'Mozilla/5.0'});r.raise_for_status()
  img=Image.open(io.BytesIO(r.content)).convert('RGBA')
  assert min(img.size)>100
  bbox=img.getchannel('A').getbbox()
  if bbox:img=img.crop(bbox)
  img.thumbnail((98,81),Image.Resampling.LANCZOS)
  base=Image.new('RGBA',(120,96),(*col,255))
  base.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
  fn=ROOT/f'{id}.png';base.convert('RGB').save(fn,optimize=True)
  assert fn.stat().st_size>1200
  z.update(status='SOURCE_LINKED_PUBLISHED_CANDIDATE',size=[120,96],sha256=hashlib.sha256(fn.read_bytes()).hexdigest(),
           url='https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-d4-d5-v17-crests-fast/'+fn.as_posix())
 except Exception as e:z['status']='FAILED';z['error']=str(e)[:120]
 out.append(z);print(name,z['status'],z.get('error',''),flush=True)
(ROOT/'ffa_crest_status.json').write_text(json.dumps({'assets':out},indent=2,ensure_ascii=False))
