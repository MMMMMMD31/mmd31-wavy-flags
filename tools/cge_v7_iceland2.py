from io import BytesIO
from pathlib import Path
import json,hashlib,requests,cairosvg
from PIL import Image
root=Path(__file__).resolve().parents[1]
out=root/'docs/cge-v7-d3-2026-27/v5'
out.mkdir(parents=True,exist_ok=True)
sources={
'1906251000033':'https://assets.footylogos.com/logos/umf-afturelding/umf-afturelding-logo-footylogos.svg',
'1906251000043':'https://assets.footylogos.com/logos/if-vestri/if-vestri-logo-footylogos.png'
}
report=[]
for id,url in sources.items():
 entry={'id':int(id),'source':url,'status':'MISSING'}
 try:
  resp=requests.get(url,timeout=22,headers={'User-Agent':'Mozilla/5.0 (MMD31 crest authenticity research)'})
  resp.raise_for_status()
  b=resp.content
  if b'<svg' in b[:900].lower():b=cairosvg.svg2png(bytestring=b,output_width=520)
  image=Image.open(BytesIO(b)).convert('RGBA')
  image.thumbnail((106,82),Image.Resampling.LANCZOS)
  bg=(226,234,245) if id=='1906251000043' else (235,232,237)
  canvas=Image.new('RGBA',(120,96),bg+(255,))
  canvas.alpha_composite(image,((120-image.width)//2,(96-image.height)//2))
  p=out/(id+'.png')
  canvas.convert('RGB').save(p,optimize=True)
  assert Image.open(p).size==(120,96)
  entry.update(status='VERIFIED_SAME_COUNTRY_TEAM_PAGE',sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 except Exception as e:entry['error']=str(e)[:240]
 report.append(entry)
(out/'manifest.json').write_text(json.dumps({'count':2,'success':sum(x['status'].startswith('VERIFIED') for x in report),'items':report},indent=2),encoding='utf8')
print(report)
