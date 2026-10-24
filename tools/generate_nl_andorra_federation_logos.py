#!/usr/bin/env python3
"""Federation emblem images for Netherlands and Andorra independent competitions."""
import io,json
from pathlib import Path
import requests,cairosvg
from PIL import Image
ROOT=Path('docs/nl-andorra-competition-logos/v1')
ROOT.mkdir(parents=True,exist_ok=True)
S=requests.Session();S.headers.update({'User-Agent':'MMD31FederationLogos/1.0'})
sources={
 'knvb': 'https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/netherlands/KNVB.svg',
 'faf': 'https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/andorra/Andorra_National_Team.svg'}
manifest={}
for key,url in sources.items():
 r=S.get(url,timeout=35);r.raise_for_status()
 svg=r.content
 assert b'<svg' in svg[:1000]
 raw=cairosvg.svg2png(bytestring=svg,output_width=650)
 img=Image.open(io.BytesIO(raw)).convert('RGBA')
 bbox=img.getchannel('A').getbbox()
 assert bbox
 img=img.crop(bbox)
 img.thumbnail((490,490),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',(512,512),(0,0,0,0))
 out.alpha_composite(img,((512-img.width)//2,(512-img.height)//2))
 dest=ROOT/(key+'.png')
 out.save(dest,format='PNG',optimize=True)
 assert Image.open(dest).size==(512,512)
 manifest[key]={'source':url,'source_width':img.width,'source_height':img.height,
 'published_path':dest.as_posix(),'resolution':[512,512],'result':'ok',
 'organization':'KNVB' if key=='knvb' else 'Federació Andorrana de Futbol (badge used for national team)'}
 print('done',key,dest,flush=True)
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
