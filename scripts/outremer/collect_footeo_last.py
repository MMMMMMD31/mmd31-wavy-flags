#!/usr/bin/env python3
"""Collect RC Saint-Pierre crest and carefully check AF Possession club-site crest."""
import requests,io,json,csv,re,hashlib,collections
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
ROOT=Path("flags/clubs/standard/outremer-2026-27");ROOT.mkdir(exist_ok=True,parents=True)
AUD=Path("audit/outremer-2026-27")
roster={x["team_id"]:x for x in csv.DictReader((AUD/"roster_326.csv").open(encoding="utf-8"))}
jobs=[
 {"id":"1990262000263","name":"Racing Club Saint Pierre","page":"https://rc-st-pierre.footeo.com/","url":"https://s3.static-footeo.com/uploads/rc-st-pierre/news/009__qnut8x.jpg","mode":"direct"},
 {"id":"1990262000163","name":"AF Possession","page":"https://afpossession.footeo.com/","mode":"footeo"},
]
s=requests.Session();s.headers.update({"User-Agent":"MMD31 2026 official Footeo logo recovery"})
def get(url):
 resp=s.get(url,timeout=28);resp.raise_for_status()
 assert len(resp.content)<6_000_000
 return resp.content
def build_png(raw):
 original=Image.open(io.BytesIO(raw));original.verify()
 im=Image.open(io.BytesIO(raw)).convert("RGBA")
 assert min(im.size)>=55 and max(im.size)/min(im.size)<4
 bbox=im.getchannel("A").getbbox()
 assert bbox
 im=im.crop(bbox)
 cnt=collections.Counter()
 thumb=im.copy();thumb.thumbnail((80,80))
 for r,g,b,a in thumb.getdata():
  if a>100 and 30<max(r,g,b)<250 and max(r,g,b)-min(r,g,b)>40:cnt[(r//25,g//25,b//25)]+=1
 k=cnt.most_common(1)[0][0] if cnt else (7,7,7)
 bg=tuple(int(0.5*(v*25+12)+0.5*255) for v in k)
 base=Image.new("RGBA",(120,96),bg+(255,))
 im.thumbnail((102,84),Image.Resampling.LANCZOS)
 base.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 buff=io.BytesIO();base.convert("RGB").save(buff,"PNG",optimize=True)
 assert len(buff.getvalue())>1200
 return buff.getvalue()
results=[]
for job in jobs:
 tid=job["id"];p=ROOT/(tid+".png")
 assert tid in roster
 if p.exists():continue
 row=dict(id=tid,name=roster[tid]["name"],source=job["page"],status="not_verified")
 try:
  if job["mode"]=="direct":url=job["url"]
  else:
   soup=BeautifulSoup(get(job["page"]),"html.parser")
   found=[]
   for im in soup.find_all("img"):
    alt=(im.get("alt") or "").lower()
    x=im.get("src") or im.get("data-src") or ""
    if re.search(r"logo du club|logo.*af possession",alt):
     if x.startswith("//"):x="https:"+x
     if x.startswith("/"):x="https://afpossession.footeo.com"+x
     if x.startswith("http") and not re.search("default|placeholder|footeo-logo|logo-footeo",x.lower()):
      found.append(x)
   # only a single unambiguous actual club logo accepted
   found=list(dict.fromkeys(found))
   logical=list(dict.fromkeys(re.sub(r"/(?:100|250|500|800)/uploads/", "/SIZE/uploads/", u.split("static-footeo.com",1)[-1]) for u in found))
   if len(logical)!=1:raise ValueError("Multiple unrelated images "+str(found[:10]))
   url=next((u for u in found if "/250/" in u),found[0])
  data=build_png(get(url))
  p.write_bytes(data)
  row.update(status="published",url=url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
 except Exception as e:row["error"]=str(e)[:400]
 results.append(row)
 print(row,flush=True)
(AUD/"lot9_rc_saint_pierre_af_possession.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
