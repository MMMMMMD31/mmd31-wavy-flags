#!/usr/bin/env python3
"""MMD31 final overseas badge recovery: original badge sources only, no invented flags."""
import csv, io, re, json, hashlib, collections, unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote,urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image
import imagehash
ROOT=Path("flags/clubs/standard/outremer-2026-27")
AUD=Path("audit/outremer-2026-27")
roster=list(csv.DictReader((AUD/"roster_326.csv").open(encoding="utf8")))
assert len(roster)==326
missing=[r for r in roster if not (ROOT/(r["team_id"]+".png")).exists()]
assert len(missing)==66,len(missing)
ALIASES={
"1990262000064":["US Bénédictine"],
"1990262000283":["AS Saint Pierraise","Association Sportive Saint Pierraise"],
"1990262000284":["AS Ilienne Amateurs","ASIA"],
"1990262000292":["AS Arue"],
"1990262000294":["AS Vénus","AS Venus"],
"1990262000297":["AS Manu Ura"],
"1990262000318":["AS Gaïca"],
"1990262000320":["AS Lössi"],
"1990262000322":["AS Kunié"],
"1990262000323":["SC Ne Drehu"],
"1990262000326":["AS Mont-Dore","Mont-Dore"],
}
SPECIAL={
"1990262000283":["https://assaintpierraise.fr/qui-sommes-nous","https://www.sportcorico.com/clubs/as-st-pierraise"],
"1990262000284":["https://www.sportcorico.com/clubs/as-ilienne-amateurs"],
"1990262000064":["https://footdelile974.re/club/us-benedictine/"],
"1990262000292":["https://www.theclubindex.com/clubes-emblemas/clube/as-arue-pf"],
"1990262000320":["https://www.footballlogosandkits.com/M%26LOGOS%2BNEW%20CALEDONIA"],
"1990262000326":["https://www.footballlogosandkits.com/M%26LOGOS%2BNEW%20CALEDONIA","https://www.bibliotecariodelfutbol.com/team/mont-dore"],
}
RIGHTS_BLOCK={"1990262000029"} # Golden Lion publication not authorised per previous research
HEAD={"User-Agent":"Mozilla/5.0 MMD31/1.0 ClubCrestResearch"}
def norm(x):
 x=unicodedata.normalize("NFKD",x or "")
 x="".join(a for a in x if not unicodedata.combining(a))
 return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ",x.lower())).strip()
def match(a,b):
 if not norm(a) or not norm(b):return 0
 return SequenceMatcher(None,norm(a),norm(b)).ratio()
def urls(r):
 tid=r["team_id"];n=r["name"];t=r["territory"]
 names=[n]+ALIASES.get(tid,[])
 slugs=list(dict.fromkeys(norm(s).replace(" ","-") for s in names))
 out=list(SPECIAL.get(tid,[]))
 for slug in slugs[:3]:
  out.append("https://www.sportcorico.com/clubs/"+slug)
  if t=="La Réunion":out.append("https://footdelile974.re/club/"+slug+"/")
  if t=="Polynésie française":out.append("https://www.theclubindex.com/clubes-emblemas/clube/"+slug+"-pf")
  if t=="Nouvelle-Calédonie":out.append("https://www.bibliotecariodelfutbol.com/team/"+slug)
 if t=="Nouvelle-Calédonie":out.append("https://www.footballlogosandkits.com/M%26LOGOS%2BNEW%20CALEDONIA")
 if t in ("Polynésie française","Nouvelle-Calédonie","Saint-Pierre-et-Miquelon"):
  for n in names[:2]:
   out += ["https://"+lang+".wikipedia.org/wiki/"+quote(n.replace(" ","_")) for lang in ("en","fr")]
 return list(dict.fromkeys(out))[:14]
def load(url):
 r=requests.get(url,headers=HEAD,timeout=12)
 r.raise_for_status()
 if len(r.content)>4000000:raise ValueError("too large")
 return r
BAD=[]
for p in (AUD/"quarantine").glob("*.png"):
 try: BAD.append(imagehash.phash(Image.open(p).convert("RGB")))
 except Exception:pass
def logo_candidates(soup,url,r):
 tid=r["team_id"];names=[r["name"]]+ALIASES.get(tid,[])
 h=soup.select_one("h1")
 title=h.get_text(" ",strip=True) if h else ""
 gallery="footballlogosandkits.com" in url
 if not gallery and max(match(title,n) for n in names)<0.53:return []
 territory={"Guyane":"guyane","Martinique":"martinique","La Réunion":"reunion","Mayotte":"mayotte","Saint-Pierre-et-Miquelon":"pierre","Polynésie française":"tahiti","Nouvelle-Calédonie":"caledon"}[r["territory"]]
 body=norm(soup.get_text(" ",strip=True)[:15000])
 if not gallery and territory not in body and not any(z in body for z in ["polynes","moorea","noumea","miquelon","reunion","calédon"]) and "wikipedia" not in url:return []
 images=[]
 for im in soup.find_all("img"):
  alt=im.get("alt","").strip();src=next((im.get(a) for a in ("data-src","data-original","src") if im.get(a) and not im.get(a).startswith("data:")),None)
  if not src:continue
  low=(alt+" "+src).lower()
  if any(z in low for z in ["mascotte","site-logo","placeholder","default","unknown","no-image","avatar","maillot","player","/icons/","federation","fédération"]):continue
  label=re.sub(r"^(logo|crest|emblem|badge|écusson)\s*(of|de|du|—|:)?\s*","",alt,flags=re.I)
  score=max(match(label,n) for n in names)
  if gallery and score<0.78:continue
  if "sportcorico" in url and (not alt.lower().startswith("logo ") or score<0.73):continue
  if "footdelile974" in url and (not ("club logo" in alt.lower() or score>.8)):continue
  if "theclubindex" in url and score<0.68:continue
  if "bibliotecariodelfutbol" in url and score<0.68:continue
  if "wikipedia" in url:
   if not im.find_parent("table",class_=re.compile("infobox")):continue
   if not any(x in low for x in ("logo","crest","club","emblem","badge")):continue
  if "assaintpierraise" in url and not any(x in low for x in ("logo","blason","assp")):continue
  if not gallery and "footdelile974" not in url and "assaintpierraise" not in url and score<0.68:continue
  u=urljoin(url,src)
  if not u.startswith("https://") or ".svg" in u:continue
  images.append((score,u,alt))
 return sorted(images,reverse=True)[:3]
def render(raw):
 im=Image.open(io.BytesIO(raw));im.verify()
 im=Image.open(io.BytesIO(raw)).convert("RGBA")
 if min(im.size)<30 or max(im.size)/min(im.size)>4:raise ValueError("bad image")
 crop=im.getchannel("A").getbbox()
 if not crop:raise ValueError("empty image")
 im=im.crop(crop)
 colors=collections.Counter()
 small=im.copy();small.thumbnail((85,85))
 for red,green,blue,alpha in small.getdata():
  if alpha>100 and max(red,green,blue)-min(red,green,blue)>35:colors[(red//32,green//32,blue//32)]+=1
 key=colors.most_common(1)[0][0] if colors else (6,6,6)
 bg=tuple(int(.65*(v*32+16)+.35*255) for v in key)
 canvas=Image.new("RGBA",(120,96),bg+(255,))
 im.thumbnail((102,84),Image.Resampling.LANCZOS)
 canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return canvas.convert("RGB")
def process(r):
 tid=r["team_id"];name=r["name"]
 row={"team_id":tid,"club":name,"territory":r["territory"],"status":"not_verified","source":"","image_url":"","reason":""}
 if tid in RIGHTS_BLOCK:
  row["status"]="rights_not_cleared";return row
 errors=[]
 for url in urls(r):
  try:
   page=load(url)
   for score,imgurl,alt in logo_candidates(BeautifulSoup(page.text,"html.parser"),page.url,r):
    try:
     raw=load(imgurl).content
     if len(raw)<700:raise ValueError("small download")
     img=render(raw)
     if any(imagehash.phash(img)-h<=6 for h in BAD):raise ValueError("quarantined generic")
     blob=io.BytesIO();img.save(blob,format="PNG",optimize=True)
     if len(blob.getvalue())<950:raise ValueError("flat or blank")
     (ROOT/(tid+".png")).write_bytes(blob.getvalue())
     row.update(status="published",source=page.url,image_url=imgurl,reason=f"logo_alt={alt};confidence={score:.2f}",sha256=hashlib.sha256(blob.getvalue()).hexdigest())
     return row
    except Exception as e:errors.append(str(e)[:45])
  except Exception as e:errors.append(type(e).__name__)
 row["reason"]=";".join(dict.fromkeys(errors))[:160]
 return row
with ThreadPoolExecutor(max_workers=12) as pool:
 rows=list(pool.map(process,missing))
for r in rows:print(r["team_id"],r["club"],r["status"],flush=True)
seen={}
for r in rows:
 if r["status"]!="published":continue
 h=r["sha256"]
 if h in seen:
  (ROOT/(r["team_id"]+".png")).unlink(missing_ok=True)
  r.update(status="duplicate_unverified",reason="duplicate of "+seen[h])
 else:seen[h]=r["team_id"]
with (AUD/"lot7_remaining66_audit.csv").open("w",encoding="utf8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["team_id","club","territory","status","source","image_url","reason","sha256"],extrasaction="ignore");w.writeheader();w.writerows(rows)
stats=collections.Counter(r["status"] for r in rows)
summary={"initial_published":260,"initial_remaining":66,"new_published":stats["published"],"still_missing":66-stats["published"],"total_published":260+stats["published"],"statuses":dict(stats),"source":"automated identity-aware collection; visual review not exhaustive"}
(AUD/"lot7_remaining66_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("LOT7_RESULT "+json.dumps(summary,ensure_ascii=False),flush=True)
