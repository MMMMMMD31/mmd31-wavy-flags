#!/usr/bin/env python3
"""Produce D2 club badge flags only from identifiable crests, never generic placeholders."""
import json,requests,time,io,hashlib,concurrent.futures,collections,re,unicodedata
from urllib.parse import quote
from pathlib import Path
from PIL import Image
import cairosvg
rows=json.loads(Path("tools/cge-v16-d2-logo-sources.json").read_text(encoding="utf-8"))
dest=Path("docs/cge-v16-d2-cups-20261024")
dest.mkdir(parents=True,exist_ok=True)
def norm(x):
 return re.sub(r"[^a-z0-9]+","",unicodedata.normalize("NFKD",x).encode("ascii","ignore").decode().lower())
def lookup(name,country):
 try:
  p=requests.get("https://www.thesportsdb.com/api/v1/json/3/searchteams.php",params={"t":name},timeout=13,headers={"User-Agent":"Mozilla/5.0"})
  if p.status_code!=200:return None,"API unavailable"
  teams=(p.json().get("teams") or [])
  for t in teams:
   a=t.get("strTeam") or ""
   if norm(a)==norm(name) and (t.get("strBadge") or "").startswith("https://"):
    return t["strBadge"],"TheSportsDB exact team name"
  return None,"No exact club crest match at TheSportsDB"
 except Exception as e:return None,str(e)[:100]
def load_image(url):
 err=None
 for attempt in range(2):
  try:
   r=requests.get(url,timeout=(12,24),headers={"User-Agent":"Mozilla/5.0 (club provenance images)"})
   r.raise_for_status()
   if not(130<len(r.content)<7_000_000):raise ValueError("image size invalid")
   content=r.content
   if b"<svg" in content[:1800].lower() or ".svg" in url.split("?")[0].lower():
    content=cairosvg.svg2png(bytestring=content,output_width=500)
   im=Image.open(io.BytesIO(content)).convert("RGBA");im.load()
   if min(im.size)<24:raise ValueError("Too small")
   return im,hashlib.sha256(r.content).hexdigest()
  except Exception as e:err=e;time.sleep(.25*(attempt+1))
 raise ValueError(str(err)[:130])
def crop(im):
 if max(im.size)>650:im.thumbnail((650,650),Image.Resampling.LANCZOS)
 if im.getchannel("A").getbbox():
  im=im.crop(im.getchannel("A").getbbox())
 return im
def bg(im):
 v=im.copy();v.thumbnail((100,100));cc=collections.Counter()
 for r,g,b,a in v.getdata():
  if a<160 or max(r,g,b)-min(r,g,b)<40 or max(r,g,b)<70:continue
  cc[(r//24,g//24,b//24)]+=1
 if not cc:return (255,255,255)
 k=cc.most_common(1)[0][0];v=tuple(min(255,j*24+12) for j in k)
 k=.35 if sum(v)<330 else .20
 return tuple(round(p*(1-k)+248*k) for p in v)
def work(row):
 name=row["name"];country=row["country"]
 url=row.get("source")
 basis="existing sourced parent emblem" if row["parent_crest_allowed"] else "identified first-team emblem"
 err=[]
 if url:
  try:im,digest=load_image(url)
  except Exception as e:err.append("original "+str(e));url=None
 if not url:
  url,method=lookup(name,country)
  if url:
   try:im,digest=load_image(url);basis=method
   except Exception as e:err.append("exact match "+str(e));url=None
  else:err.append(method)
 if not url:return {**row,"status":"MISSING_NO_VERIFIED_CRESt","error":"; ".join(err)}
 try:
  im=crop(im);color=bg(im)
  im.thumbnail((102,84),Image.Resampling.LANCZOS)
  output=Image.new("RGBA",(120,96),color+(255,))
  output.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  file=dest/(str(row["id"])+".png");output.convert("RGB").save(file,format="PNG",optimize=True)
  with Image.open(file) as image:
   assert image.size==(120,96)
  return {**row,"source":url,"status":"PUBLISHED_SOURCE_NAMED_VISUAL_AUDIT_PENDING","source_basis":basis,"source_sha256":digest,"background":color,
          "flagUrl":"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-cge-v16-d2-cups-20261024-test/"+str(file),
          "png_sha256":hashlib.sha256(file.read_bytes()).hexdigest()}
 except Exception as e:return {**row,"status":"MISSING_RENDER_ERROR","error":str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as p:
 output=list(p.map(work,rows))
manifest={"generated":"2026-10-24","number":len(rows),"published":sum(x["status"].startswith("PUBLISHED") for x in output),"missing":sum(not x["status"].startswith("PUBLISHED") for x in output),"items":output}
(dest/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("Crests published",manifest["published"],"/",manifest["number"],flush=True)
for x in output:
 if not x["status"].startswith("PUBLISHED"):print("Missing",x["country"],x["name"],x.get("error"),flush=True)
