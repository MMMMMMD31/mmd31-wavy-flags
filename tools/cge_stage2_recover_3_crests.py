#!/usr/bin/env python3
"""Recover only unambiguous current club emblems with traced source pages."""
import requests,io,json,hashlib
from pathlib import Path
from PIL import Image
SOURCES={
1884520000202:('https://i0.wp.com/www.maltafootball.com/wp-content/uploads/2024/06/img_9402-1.jpg?fit=630%2C630&ssl=1','https://www.maltafootball.com/2024/06/13/naxxar-lions-unveil-new-logo/','Naxxar Lions'),
1884520000313:('https://images.one.co.il/images/msites/leagues/logos150/e3b11a5bc3edf1b5286cab6ad76a8978.png','https://www.one.co.il/Soccer/Team/14','Maccabi Herzliya')
}
rpath=Path('data/cge-four-second-divisions-2026-27-crests.json')
manifest=json.loads(rpath.read_text(encoding='utf-8'))
s=requests.Session()
for id_,(url,source,name) in SOURCES.items():
 response=s.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0'});response.raise_for_status()
 raw=response.content;img=Image.open(io.BytesIO(raw)).convert('RGBA')
 assert min(img.size)>=64
 # The palette uses one of the club's distinctive colors, and the actual badge is centered.
 bgcolors={1884520000202:(154,40,53),1884520000313:(247,233,116)}
 im=Image.new('RGBA',(120,96),bgcolors[id_]+(255,))
 img.thumbnail((95,85),Image.Resampling.LANCZOS)
 im.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
 dest=Path(f'docs/cge-four-second-divisions-2026-27/{id_}.png')
 dest.parent.mkdir(parents=True,exist_ok=True)
 im.convert('RGB').save(dest,'PNG',optimize=True)
 rec=next(x for x in manifest if x['id']==id_)
 rec.update(source=url,club=name,original_source=source,
    validation='source_retrieved_120x96_visual_review_pending',
    background=list(bgcolors[id_]),file=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
 print('RECOVERED',id_,name,flush=True)
rpath.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
