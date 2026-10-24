#!/usr/bin/env python3
"""MMD31 Belgian D4/D5 crest research; only source-backed crests are published.
No generic placeholders. Identified candidates are NOT automatically certified."""
import csv,io,json,time,hashlib,unicodedata,re,urllib.parse
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageStat
import cairosvg
ROOT=Path("docs/belgian-d4-d5-2026-27/v17")
ROSTER=list(csv.DictReader((ROOT/"rosters.csv").open()))
S=requests.Session()
S.headers.update({"User-Agent":"MMD31-club-crest-research/2026-10-24 (non-commercial source attribution)"})
def slug(x):
 return re.sub(r"[^a-z0-9]+"," ",unicodedata.normalize("NFKD",x.lower()).encode("ascii","ignore").decode()).strip()
def jget(url,params):
 for wait in (0,2,5):
  try:
   if wait:time.sleep(wait)
   r=S.get(url,params=params,timeout=18);r.raise_for_status()
   return r.json()
  except Exception as e: err=e
 raise err
def qid_logo(name):
 for v in [name,re.sub(r"\b(?:Royal|KFC|RFC|RCS|FC|KSV|RUS|KVK|KVC|VV)\b","",name).strip()]:
  if len(v)<5:continue
  try:
   data=jget("https://www.wikidata.org/w/api.php",{"action":"wbsearchentities","search":v,"language":"en","format":"json","limit":8})
  except Exception:continue
  for x in data.get("search",[]):
   label=x.get("label","");description=x.get("description","")
   lt=set(slug(label).split());nt=set(slug(name).split())
   if not lt or len(lt&nt)<max(1,round(len(nt)*0.42)):continue
   if not any(word in description.lower() for word in ("football","soccer","sport","belgian")):continue
   try:
    ent=jget("https://www.wikidata.org/wiki/Special:EntityData/"+x["id"]+".json",{})
    claims=ent["entities"][x["id"]]["claims"]
    if "P154" in claims:
     filename=claims["P154"][0]["mainsnak"]["datavalue"]["value"]
     return "https://commons.wikimedia.org/wiki/Special:Redirect/file/"+urllib.parse.quote(filename),{"wikidata":x["id"],"label":label,"description":description,"file":filename}
   except Exception:pass
 return None,{}
def commons_logo(name):
 phrase=slug(name)
 for query in ['"'+name+'" logo','"'+name+'" football crest']:
  try:
   data=jget("https://commons.wikimedia.org/w/api.php",{"action":"query","list":"search","srsearch":query,"srnamespace":6,"format":"json","srlimit":6})
   for item in data.get("query",{}).get("search",[]):
    title=item["title"]
    tokens=set(slug(title).split())
    words=set(phrase.split())
    if len(tokens&words)<max(1,round(len(words)*.45)):continue
    if not any(z in title.lower() for z in ("logo","badge","emblem","crest")):continue
    if not title.lower().endswith((".svg",".png",".jpeg",".jpg",".webp")):continue
    return "https://commons.wikimedia.org/wiki/Special:Redirect/file/"+urllib.parse.quote(title.split(":",1)[-1]),{"commons_file":title}
  except Exception:pass
 return None,{}
def retrieve(url):
 r=S.get(url,timeout=25,headers={"Referer":"https://commons.wikimedia.org/"},allow_redirects=True)
 r.raise_for_status()
 raw=r.content
 if raw.lstrip().startswith(b"<svg") or b"<svg" in raw[:1000]:
  raw=cairosvg.svg2png(bytestring=raw,output_width=500)
 im=Image.open(io.BytesIO(raw)).convert("RGBA")
 if max(im.size)<80 or im.width/im.height>3.5 or im.height/im.width>3.5:raise ValueError("non-logo dimensions")
 return im
def render(im,path):
 im.thumbnail((96,80),Image.Resampling.LANCZOS)
 box=im.getchannel("A").getbbox()
 if box:im=im.crop(box)
 im.thumbnail((96,80),Image.Resampling.LANCZOS)
 # Derive secondary tint by averaging sufficiently saturated logo pixels; NOT a club-color certification.
 pixels=im.resize((60,60)).getdata()
 hsv=[]
 for r,g,b,a in pixels:
  if a<190 or max(r,g,b)-min(r,g,b)<40:continue
  hsv.append((r,g,b))
 if hsv:
  r,g,b=max(hsv,key=lambda p:max(p)-min(p))
  bg=(int(r*.18+255*.82),int(g*.18+255*.82),int(b*.18+255*.82))
 else:bg=(236,236,236)
 out=Image.new("RGBA",(120,96),(*bg,255))
 out.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 out.convert("RGB").save(path,optimize=True)
 if path.stat().st_size<950:raise ValueError("too small for trusted crest")
 return bg
rows=[]
for idx,t in enumerate(ROSTER):
 id_,name=int(t["id"]),t["name"]
 out={"id":id_,"name":name,"status":"NON_SOURCE","source":None}
 if t["crestStatus"]=="PARENT_REUSED":
  out["status"]="PARENT_REUSED_IN_JSON";rows.append(out);continue
 url,source=qid_logo(name)
 if not url:url,source=commons_logo(name)
 if url:
  try:
   img=retrieve(url);p=ROOT/f"{id_}.png";bg=render(img,p)
   out.update(status="PUBLIC_SOURCE_CANDIDATE_PUBLISHED",source=url,source_metadata=source,background=bg,
              sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
              url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-d4-d5-v17-crests-test/{p.as_posix()}")
  except Exception as e:out.update(status="SOURCE_FETCH_FAILED",error=str(e)[:170],source=url)
 rows.append(out)
 print(idx+1,"/",len(ROSTER),name,out["status"],flush=True)
 if idx%15==14:
  (ROOT/"crest_status.json").write_text(json.dumps({"assets":rows,"complete":False},ensure_ascii=False,indent=2))
(ROOT/"crest_status.json").write_text(json.dumps({"assets":rows,"complete":True,"sourced":sum(x["status"]=="PUBLIC_SOURCE_CANDIDATE_PUBLISHED" for x in rows),"missing":sum(x["status"] not in ("PUBLIC_SOURCE_CANDIDATE_PUBLISHED","PARENT_REUSED_IN_JSON") for x in rows)},ensure_ascii=False,indent=2))
