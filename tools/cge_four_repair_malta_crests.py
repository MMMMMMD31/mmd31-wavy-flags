import json,requests,hashlib
from pathlib import Path
from PIL import Image
from cge_four_leagues_crests_2026 import render
p=Path('data/cge-four-first-divisions-2026-27-crests.json')
m=json.loads(p.read_text(encoding='utf-8'))
replacements={
 1884510000208:'https://www.birkirkarafc.com/crest.png',
 1884510000212:'https://bspfc.com/wp-content/uploads/2026/09/FULL-CLR-Copy-scaled.png'
}
for id,url in replacements.items():
 r=requests.get(url,timeout=40,headers={'User-Agent':'Mozilla/5.0'})
 r.raise_for_status()
 assert len(r.content)>1000
 img,bg=render(r.content)
 dest=Path(f'docs/cge-four-first-divisions-2026-27/{id}.png')
 img.save(dest,'PNG',optimize=True)
 assert Image.open(dest).size==(120,96)
 rec=next(x for x in m if x['id']==id)
 rec.update(source=url,validation='source_retrieved_120x96_visual_review_pending',
   file=str(dest),background=list(bg),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
   original_source='official_club_website')
 print('FIX',id,url,'saved',dest.stat().st_size)
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
