#!/usr/bin/env python3
import csv,json,time,re,io,hashlib,unicodedata,concurrent.futures
from pathlib import Path
from urllib.parse import quote
import requests,cairosvg
from PIL import Image
ROOT=Path("docs/german-clubs-2026-27/missing-20261024");ROOT.mkdir(parents=True,exist_ok=True)
ROWS=list(csv.DictReader(open("tools/mmd31_remaining_germany_692.csv",encoding="utf-8")))
assert len(ROWS)==692
UA={"User-Agent":"MMD31-GermanCrests/1.0 (source https://github.com/MMMMMMD31/mmd31-wavy-flags)"}
def get(url,p=None):
 for k in range(3):
  try:
   r=requests.get(url,params=p,headers=UA,timeout=23)
   if r.status_code in (429,500,502,503,504):time.sleep(k+2);continue
   r.raise_for_status();return r
  except Exception:
   time.sleep(k+1)
 return None
def norm(s):
 s=unicodedata.normalize("NFKD",s.lower()).replace("ß","ss")
 s="".join(c for c in s if not unicodedata.combining(c))
 return re.sub(" +"," ",re.sub("[^a-z0-9]+"," ",s)).strip()
CURATED={"1898200000223":"FC_Gundelfingen.svg","1898200000199":"FSV_1926_Fernwald.svg","1898200000101":"SSVg_Velbert_02.svg","1898200000241":"1._FC_Passau.svg","1898200000513":"Dresdner_SC.svg"}
def jose():
 r=get("https://api.github.com/repos/JoseArroyave/football-logos/git/trees/main",{"recursive":1})
 if r is None:return {},set()
 files=[x["path"].split("/")[-1] for x in r.json()["tree"] if x["path"].startswith("logos/germany/") and x["path"].endswith(".svg")]
 return {norm(x[:-4]):x for x in files},set(files)
def wiki(row):
 name=row["club"];query=re.sub(r" (II|III)$","",name)
 r=get("https://www.wikidata.org/w/api.php",{"action":"wbsearchentities","search":query,"language":"de","limit":6,"format":"json"})
 if r is None:return None
 candidates=[]
 for x in r.json().get("search",[]):
  desc=x.get("description","").lower()
  if norm(x.get("label",""))!=norm(query):continue
  if not any(w in desc for w in ["fußball","fussball","football","sportverein"]):continue
  candidates.append(x["id"])
 if not candidates:return None
 t=get("https://www.wikidata.org/w/api.php",{"action":"wbgetentities","ids":"|".join(candidates[:4]),"props":"claims","format":"json"})
 if t is None:return None
 found=[]
 for q,e in t.json().get("entities",{}).items():
  c=e.get("claims",{})
  if not c.get("P154"):continue
  if c.get("P17"):
   countries=[s.get("mainsnak",{}).get("datavalue",{}).get("value",{}).get("id") for s in c["P17"]]
   if "Q183" not in countries:continue
  file=c["P154"][0].get("mainsnak",{}).get("datavalue",{}).get("value")
  if isinstance(file,str):found.append((q,file))
 if len(found)!=1:return None
 q,filename=found[0]
 info=get("https://commons.wikimedia.org/w/api.php",{"action":"query","titles":"File:"+filename,"prop":"imageinfo","iiprop":"url|mime","format":"json"})
 if info is None:return None
 try:
  page=next(iter(info.json()["query"]["pages"].values()))
  asset=page["imageinfo"][0]
  url=asset["url"]
  if not url.startswith("https://upload.wikimedia.org/") or not asset.get("mime","").startswith("image/"):return None
  return {"teamId":row["teamId"],"club":name,"source":url,"wikidata":q,"source_type":"wikidata_verified"}
 except Exception:return None
def paint(raw,url):
 if b"<svg" in raw[:20000].lower():raw=cairosvg.svg2png(bytestring=raw,output_width=480)
 pic=Image.open(io.BytesIO(raw)).convert("RGBA");box=pic.getchannel("A").getbbox()
 if not box:raise ValueError("empty image")
 pic=pic.crop(box);pic.thumbnail((104,84),Image.Resampling.LANCZOS)
 bg=Image.new("RGBA",(120,96),(88,118,152,255));bg.alpha_composite(pic,((120-pic.width)//2,(96-pic.height)//2))
 return bg.convert("RGB")
if __name__=="__main__":
 names,exists=jose();verified={}
 for row in ROWS:
  sid=row["teamId"];filename=CURATED.get(sid)
  if filename and filename in exists:pass
  else:
   possible=[names.get(norm(row["club"])),names.get(norm(re.sub(r" (II|III)$","",row["club"])))]
   possible={x for x in possible if x}
   filename=next(iter(possible)) if len(possible)==1 else None
  if filename:
   verified[sid]={"teamId":sid,"club":row["club"],"source_type":"jose_verified","source":"https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/germany/"+quote(filename)}
 print("Verified upstream:",len(verified),flush=True)
 todo=[r for r in ROWS if r["teamId"] not in verified]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  for i,item in enumerate(pool.map(wiki,todo),1):
   if item:verified[item["teamId"]]=item
   if i%100==0:print("Wikidata",i,"/",len(todo),"found",len(verified),flush=True)
 done=[];errors=[]
 for item in verified.values():
  try:
   r=get(item["source"])
   if r is None or len(r.content)>8_000_000:raise ValueError("unavailable or oversized")
   pic=paint(r.content,item["source"]);path=ROOT/(item["teamId"]+".png");pic.save(path,optimize=True)
   item["png_path"]=str(path);item["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest();done.append(item)
  except Exception as e:errors.append({"club":item["club"],"problem":str(e)[:100]})
 (ROOT/"manifest.json").write_text(json.dumps(done,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 (ROOT/"status.json").write_text(json.dumps({"published":len(done),"original_missing":len(ROWS),"remaining":len(ROWS)-len(done),"errors":errors},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("PUBLISHED",len(done),"REMAINING",len(ROWS)-len(done),flush=True)
