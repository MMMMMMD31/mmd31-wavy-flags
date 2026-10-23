#!/usr/bin/env python3
import json,requests,io,hashlib
from PIL import Image,ImageOps
from pathlib import Path
P=Path("docs/belgian-d3-clubs-2026-27/v13");P.mkdir(parents=True,exist_ok=True)
items=[
(1900262702002,"Racing Club Harelbeke","https://logowik.com/content/uploads/images/krc-harelbeke8953.logowik.com.webp",[217,191,229]),
(1900262702010,"KFC Merelbeke","https://www.voetbalinbelgie.be/images/club_logo_van_voetbalvereniging_merelbeke-kfc_uit_merelbeke.png",[240,229,151]),
(1900262702013,"Belisia Bilzen","https://belisiasv.be/media/5j5ar0n4/belisia_logo_small.png",[219,236,251])
]
res=[]
for id,n,url,bg in items:
 row=dict(id=id,name=n,source=url,status="FAILED")
 try:
  r=requests.get(url,headers={'User-Agent':'Mozilla/5.0 (MMD31 club crest attribution)'},timeout=25);r.raise_for_status()
  im=Image.open(io.BytesIO(r.content)).convert('RGBA');im.thumbnail((96,82),Image.Resampling.LANCZOS)
  assert im.size[0]>40
  bg_im=Image.new('RGBA',(120,96),(*bg,255));bg_im.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  f=P/f"{id}.png";bg_im.convert("RGB").save(f,optimize=True)
  assert f.stat().st_size>1200
  row.update(status="SOURCE_IMAGE_PUBLISHED_IDENTITY_CANDIDATE",url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-v13-d3-assets/{f.as_posix()}",sha256=hashlib.sha256(f.read_bytes()).hexdigest())
 except Exception as e:row["error"]=str(e)
 res.append(row);print(n,row["status"],row.get("error",""),flush=True)
(P/"additional_fixes_status.json").write_text(json.dumps({"assets":res},ensure_ascii=False,indent=2))
