#!/usr/bin/env python3
"""CGE3 FRANCE - publish only club-identical crests missing from 326-team roster."""
import io, csv, json, hashlib, collections
from pathlib import Path
from PIL import Image, ImageOps
import requests
ROOT=Path("flags/clubs/standard/outremer-2026-27")
AUD=Path("audit/outremer-2026-27")
SOURCES=[
 {"id":"1990262000153","name":"JCV Saint-Pierre","url":"https://www.saintpierre.re/sites/default/files/2024-12/JCV%20Club%20Foot%20accede%202e%20division.jpg",
  "provenance":"https://www.saintpierre.re/sport-et-loisirs/foot-la-jcv-saint-pierre-monte-en-deuxieme-division"},
 {"id":"1990262000220","name":"ASJ Moinatrindri","url":"https://images.seeklogo.com/logo-png/63/1/association-sportive-des-jeunes-de-moinatrindri-logo-png_seeklogo-638187.png",
  "provenance":"https://seeklogo.com/vector-logo/638187/association-sportive-des-jeunes-de-moinatrindri"},
 {"id":"1990262000284","name":"AS Ilienne Amateurs","url":"https://images.seeklogo.com/logo-png/62/1/association-sportive-ilienne-amateurs-logo-png_seeklogo-626069.png",
  "provenance":"https://seeklogo.com/vector-logo/626069/association-sportive-ilienne-amateurs"}
]
roster={r["team_id"]:r for r in csv.DictReader((AUD/"roster_326.csv").open(encoding="utf-8"))}
assert len(roster)==326
assert len({x["id"] for x in SOURCES})==3
def render(im):
 im=im.convert("RGBA")
 box=im.getchannel("A").getbbox()
 if not box:raise ValueError("No crest pixels")
 im=im.crop(box)
 if im.width<70 or im.height<70:raise ValueError("Insufficient source resolution")
 if max(im.width,im.height)/min(im.width,im.height)>3.5:raise ValueError("Wrong badge aspect ratio")
 # Find a prominent saturated logo color (avoid surrounding white/black).
 freq=collections.Counter()
 reduced=im.copy();reduced.thumbnail((110,110))
 for r,g,b,a in reduced.getdata():
  if a>=120 and max(r,g,b)-min(r,g,b)>40 and 40<max(r,g,b)<253:
   freq[(r//25,g//25,b//25)]+=1
 if freq:
  top=freq.most_common(1)[0][0]
  bg=tuple(min(255,int((x*25+12)*.45+255*.55)) for x in top)
 else: bg=(228,228,228)
 canvas=Image.new("RGBA",(120,96),bg+(255,))
 im.thumbnail((102,84),Image.Resampling.LANCZOS)
 canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return canvas.convert("RGB")
results=[]
for item in SOURCES:
 tid=item["id"];dst=ROOT/(tid+".png")
 assert tid in roster,(tid,"not an enrolled team")
 assert not dst.exists(),("refuse to overwrite existing flag",tid)
 r=requests.get(item["url"],timeout=35,headers={"User-Agent":"MMD31 authentic club insignia collector 2026"})
 r.raise_for_status()
 raw=r.content
 if len(raw)<1500 or len(raw)>6_000_000:raise ValueError("Suspicious image size "+tid)
 src=Image.open(io.BytesIO(raw));src.verify()
 src=Image.open(io.BytesIO(raw))
 badge=render(src)
 data=io.BytesIO();badge.save(data,format="PNG",optimize=True)
 blob=data.getvalue()
 assert len(blob)>1250
 dst.write_bytes(blob)
 confirm=Image.open(dst)
 assert confirm.size==(120,96) and confirm.format=="PNG"
 record={"team_id":tid,"club":roster[tid]["name"],"file":dst.as_posix(),
         "source":item["url"],"provenance":item["provenance"],
         "sha256":hashlib.sha256(blob).hexdigest(),"bytes":len(blob)}
 results.append(record)
 print("PUBLISHED "+json.dumps(record,ensure_ascii=False),flush=True)
out=AUD/"lot8_three_public_badges.json"
out.write_text(json.dumps({"count":len(results),"assets":results,"validation":"club-identical external pages; no generic FFF placeholders"},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("COMPLETE",len(results),flush=True)
