#!/usr/bin/env python3
"""Render authentic club-source crests 120x96 and federation emblems 512x512 in a dedicated test branch."""
import concurrent.futures,hashlib,io,json,requests,time,collections
from PIL import Image
from pathlib import Path
import cairosvg
data=json.loads(Path("tools/cge-v15-d1-manifest.json").read_text(encoding="utf-8"))
out=Path("docs/cge-v15-four-d1-20261024")
out.mkdir(parents=True,exist_ok=True)
def fetch(url):
  err=None
  for i in range(3):
    try:
      r=requests.get(url,timeout=(10,23),headers={"User-Agent":"Mozilla/5.0 (MMD31 logo provenance project)"});r.raise_for_status()
      body=r.content
      if len(body)<90 or len(body)>7_000_000:raise ValueError("source size invalid")
      if b"<svg" in body[:1000].lower() or url.lower().endswith(".svg"):
        body=cairosvg.svg2png(bytestring=body,output_width=650)
      im=Image.open(io.BytesIO(body)).convert("RGBA");im.load()
      if min(im.size)<35:raise ValueError("Source logo too small")
      return im,hashlib.sha256(r.content).hexdigest()
    except Exception as e:err=e;time.sleep(.4*(i+1))
  raise RuntimeError(str(err)[:180])
def trim(im):
  # Remove white edge-connected backdrop for raster logos without destroying white inner shield.
  from collections import deque
  if max(im.size)>800:im.thumbnail((800,800))
  w,h=im.size;px=im.load();seen=set();q=deque()
  for x in range(w):
    for y in (0,h-1):
      r,g,b,a=px[x,y]
      if a>240 and min(r,g,b)>248:seen.add((x,y));q.append((x,y))
  for y in range(h):
    for x in (0,w-1):
      r,g,b,a=px[x,y]
      if a>240 and min(r,g,b)>248:seen.add((x,y));q.append((x,y))
  while q and len(seen)<350000:
    x,y=q.popleft();r,g,b,a=px[x,y];px[x,y]=(r,g,b,0)
    for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
      xx,yy=x+dx,y+dy
      if 0<=xx<w and 0<=yy<h and (xx,yy) not in seen:
        r,g,b,a=px[xx,yy]
        if a>240 and min(r,g,b)>248:seen.add((xx,yy));q.append((xx,yy))
  bb=im.getchannel('A').getbbox()
  if not bb:raise ValueError("blank after border extraction")
  return im.crop(bb)
def background(im):
  sample=im.copy();sample.thumbnail((130,130))
  scores=collections.Counter()
  for r,g,b,a in sample.getdata():
    if a<160 or max(r,g,b)-min(r,g,b)<45 or max(r,g,b)<75:continue
    scores[(r//24,g//24,b//24)]+=1
  if not scores:return (216,220,224),"neutral due to monochrome source"
  k=scores.most_common(1)[0][0]
  col=tuple(min(255,x*24+12) for x in k)
  mix=.42 if sum(col)<350 else .22
  return tuple(int(v*(1-mix)+246*mix) for v in col),"dominant chromatic club crest color"
def make(entry,isfed=False):
  name=entry['country'] if isfed else entry['name'];slug=entry['country'] if isfed else str(entry['id'])
  try:
    im,sourcehash=fetch(entry['source'])
    im=trim(im)
    if isfed:
      bg=(255,255,255,255);dim=(512,512);fit=(460,460)
    else:
      col,orig=background(im);bg=col+(255,);dim=(120,96);fit=(102,84)
    img=Image.new("RGBA",dim,bg)
    im.thumbnail(fit,Image.Resampling.LANCZOS)
    img.alpha_composite(im,((dim[0]-im.width)//2,(dim[1]-im.height)//2))
    suffix="-federation" if isfed else ""
    p=out/(slug+suffix+".png")
    img.convert("RGB").save(p,format="PNG",optimize=True)
    with Image.open(p) as ck:
      assert ck.format=="PNG" and ck.size==dim and len(ck.getcolors(dim[0]*dim[1]) or [])>30
    return {"id":entry.get('id'),"name":name,"country":entry["country"],"source":entry["source"],"source_sha256":sourcehash,"flagUrl":"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-cge-v15-four-d1-20261024-test/"+p.as_posix(),"file":p.as_posix(),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"dimensions":dim,"status":"PUBLISHED; CLUB EMBLEM SOURCE MATCHED; visual review required","background":list(bg[:3]) if not isfed else [255,255,255]}
  except Exception as e:
    return {"id":entry.get('id'),"name":name,"country":entry["country"],"source":entry["source"],"status":"MISSING","error":str(e)[:220]}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  clubs=list(pool.map(make,data["clubs"]))
  feds=list(pool.map(lambda x:make(x,True),data["federations"]))
s={"clubs":clubs,"federations":feds,"clubs_ok":sum(z['status']!="MISSING" for z in clubs),"federations_ok":sum(z['status']!="MISSING" for z in feds),"clubs_expected":len(clubs),"federations_expected":len(feds)}
(out/"manifest.json").write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("CLUB BADGES",s["clubs_ok"],"/",s["clubs_expected"],"FEDERATION EMBLEMS",s["federations_ok"],"/",s["federations_expected"],flush=True)
for z in clubs+feds:
 if z["status"]=="MISSING":print("MISSING",z["country"],z["name"],z.get("error"),flush=True)
