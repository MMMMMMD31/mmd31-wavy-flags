#!/usr/bin/env python3
"""Correct verified 2025 Eendracht Aalst Lede crest; older Jong Lede crest is not current."""
from PIL import Image
from collections import deque
import requests,io,hashlib,json
from pathlib import Path
ROOT=Path('docs/belgian-d4-d5-2026-27/v17')
src='https://www.voetbalinbelgie.be/images/club_logo_van_voetbalvereniging_eendracht-aalst-lede_uit_aalst.png?v=20250626101013'
r=requests.get(src,timeout=25,headers={'User-Agent':'Mozilla/5.0'});r.raise_for_status()
im=Image.open(io.BytesIO(r.content)).convert('RGBA')
assert im.width>60 and im.height>60
im.thumbnail((98,80),Image.Resampling.LANCZOS)
can=Image.new('RGBA',(120,96),(225,225,225,255))
can.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
p=ROOT/'1900262703000.png'
can.convert('RGB').save(p,optimize=True)
assert p.stat().st_size>1500
entry={'id':1900262703000,'name':'Koninklijke Eendracht Aalst Lede','source':src,
       'source_verification':'Official club revealed a new black/white EA monogram in May 2025; reference voetbalinbelgie.be',
       'status':'PUBLISHED_CURRENT_CREST','size':[120,96],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
       'url':'https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-d4-d5-v17-crests-fast/'+p.as_posix()}
(ROOT/'verified_crest_corrections.json').write_text(json.dumps({'replacements':[entry],
 'rejected_old_logos':[1900262703001,1900262703012]},indent=2))
print(entry)
