#!/usr/bin/env python3
"""Official Sportnet/Futbalnet verified club-logo extraction, five Slovakia D2 clubs."""
import io,json,time,hashlib
from pathlib import Path
import requests
from PIL import Image
ROOT=Path('docs/central-europe-d2-2026-27/verified');ROOT.mkdir(parents=True,exist_ok=True)
HOST='https://api.sportnet.online/data/ppo/'
DATA=[
(1971262100104,'FC TATRAN Prešov','https://sportnet.sme.sk/futbalnet/k/fc-tatran-presov/',HOST+'1-fc-tatran-presov.futbalnet.sk/79ac55b7-f844-4c4e-9555-d7a62dc4e4d5.jpeg',(231,247,233)),
(1971262100105,'FC ViOn Zlaté Moravce - Vráble','https://sportnet.sme.sk/futbalnet/k/fc-vion-zlate-moravce-vrable/',HOST+'fc-vion-zlate-moravce.futbalnet.sk/eb54b5b9-8ef1-4c5e-b09d-1e2774bcb34e.png',(243,236,251)),
(1971262100107,'FK Humenné','https://sportnet.sme.sk/futbalnet/k/futbalovy-klub-humenne-s-r-o/',HOST+'issf_club_12879/79cdedc6-e148-47ae-bfce-d317969e7f0a.jpeg',(235,241,247)),
(1971262100111,'MFK Tatran Liptovský Mikuláš','https://sportnet.sme.sk/futbalnet/k/mfk-tatran-liptovsky-mikulas/',HOST+'mfk-tatran-liptovsky-mikulas.futbalnet.sk/134865ac-e5b7-4ef7-80c7-e6fdaf87cc91.png',(224,239,250)),
(1971262100115,'OFK Malženice','https://sportnet.sme.sk/futbalnet/k/ofk-dynamo-malzenice/',HOST+'issf_club_12850/1fa6a97b-aec9-4b11-b7f6-34c9c42970d9.jpeg',(248,240,224))]
s=requests.Session();s.headers['User-Agent']='MMD31-verified-club-badge/1.0'
results=[]
for tid,name,page_url,img_url,bg in DATA:
 rec={'id':tid,'name':name,'official_profile':page_url,'source_logo':img_url,'status':'NOT_FOUND'}
 try:
  page=s.get(page_url,timeout=(4,15))
  if page.status_code!=200:rec['status']='CLUB_PAGE_UNAVAILABLE';results.append(rec);continue
  # The source profile is an official club association roster, badge is its own crest.
  img=s.get(img_url,timeout=(4,15))
  if img.status_code!=200:rec['status']='IMAGE_UNAVAILABLE';results.append(rec);continue
  src=Image.open(io.BytesIO(img.content)).convert('RGBA')
  if src.width<40 or src.height<40:rec['status']='IMAGE_TOO_SMALL';results.append(rec);continue
  src.thumbnail((98,82),Image.Resampling.LANCZOS)
  final=Image.new('RGBA',(120,96),bg+(255,));final.alpha_composite(src,((120-src.width)//2,(96-src.height)//2))
  file=ROOT/(str(tid)+'.png');final.convert('RGB').save(file,format='PNG',optimize=True)
  rec.update(status='VERIFIED_CREST',sha256=hashlib.sha256(file.read_bytes()).hexdigest(),width=120,height=96,flagUrl=f'https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-central-europe-d2-20261025/docs/central-europe-d2-2026-27/verified/{tid}.png')
 except Exception as e:rec.update(status='ERROR',error=str(e)[:200])
 results.append(rec);print(tid,rec['status'],flush=True);time.sleep(.12)
Path('docs/central-europe-d2-2026-27/manifest-sportnet-SK.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('PUBLISHED',sum(x['status']=='VERIFIED_CREST' for x in results),'OF',len(results))
