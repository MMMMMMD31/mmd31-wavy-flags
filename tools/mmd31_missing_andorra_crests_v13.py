#!/usr/bin/env python3
"""Populate missing authentic FS La Massana/Pirineus United FC images from individually labelled club profiles."""
import io,json,base64
from pathlib import Path
from PIL import Image,ImageOps
import requests
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (MMD31 educational club crest archival indexing)'})
rows=[
 {'id':1895100000067,'club':'FS La Massana','profile':'https://es.besoccer.com/equipo/fs-la-massana',
 'urls':['https://cdn.resfu.com/img_data/escudos/medium/14020.jpg?size=480x','https://cdn.resfu.com/img_data/escudos/medium/14020.jpg?lossy=1&size=120x']},
 {'id':1895100000069,'club':'Pirineus United FC','profile':'https://es.besoccer.com/equipo/pirineus-united',
 'urls':['https://cdn.resfu.com/img_data/equipos/168397.png?size=480x','https://cdn.resfu.com/img_data/equipos/168397.png?lossy=1&size=120x']}
]
ROOT=Path('docs/nl-andorra-clubs-2026-27/v13/standard');ROOT.mkdir(parents=True,exist_ok=True)
status=[]
for r in rows:
 record={'id':r['id'],'club':r['club'],'profile':r['profile'],'result':'missing','errors':[]}
 for u in r['urls']:
  try:
   z=S.get(u,timeout=22);z.raise_for_status()
   im=Image.open(io.BytesIO(z.content)).convert('RGBA')
   if min(im.size)<28:raise ValueError('too small '+str(im.size))
   if max(im.size)>3000:raise ValueError('too large')
   bbox=im.getchannel('A').getbbox()
   if not bbox:raise ValueError('empty alpha')
   im=im.crop(bbox)
   # Background for genuine identified club emblem, not generated emblem.
   background=(225,232,228) if r['id']==1895100000069 else (230,218,199)
   canvas=Image.new('RGBA',(120,96),background+(255,))
   im.thumbnail((98,82),Image.Resampling.LANCZOS)
   canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
   canvas.save(ROOT/(str(r['id'])+'.png'),optimize=True)
   preview=canvas.copy();preview.thumbnail((100,80))
   buff=io.BytesIO();preview.save(buff,format='PNG')
   record.update({'result':'ok','source':u,'original_size':list(Image.open(io.BytesIO(z.content)).size),'dimensions':[120,96],'preview_base64':base64.b64encode(buff.getvalue()).decode('ascii'),'bg':background})
   break
  except Exception as e:
   record['errors'].append(f'{u}: {str(e)[:160]}')
 status.append(record)
 print(record['id'],record['result'],record.get('source'),flush=True)
ROOT.parent.joinpath('status.json').write_text(json.dumps({'expected':2,'published':sum(r['result']=='ok' for r in status),'assets':status},ensure_ascii=False,indent=2)+'\n')
