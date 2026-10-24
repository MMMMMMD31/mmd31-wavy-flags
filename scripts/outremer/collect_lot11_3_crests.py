#!/usr/bin/env python3
"""Publish named authentic images from team-run Footeo sites and Martinique youth organizer."""
import io, json, hashlib, collections, colorsys
from pathlib import Path
import requests
from PIL import Image
DEST=Path("flags/clubs/standard/outremer-2026-27")
AUD=Path("audit/outremer-2026-27")
SOURCES=[
 {"team_id":"1990262000200","club":"JS Marigot","page":"https://ichpeyi-a.com/clubs/","img":"https://ichpeyi-a.com/wp-content/uploads/2025/07/js-marigot.webp",
  "evidence":"Foot Avenir Martinique club participant roster, labeled JS MARIGOT"},
 {"team_id":"1990262000274","club":"FC Ligne Paradis","page":"https://fcligneparadis.footeo.com/","img":"https://s3.static-footeo.com/250/uploads/fcligneparadis/logo__76a9t1qdm.jpg",
  "evidence":"Club-run site labeled logo du club FC LIGNE-PARADIS"},
 {"team_id":"1990262000155","club":"AS Montgaillard","page":"https://as-montgaillard.footeo.com/","img":"https://s2.static-footeo.com/100/uploads/as-montgaillard/logo__76a9t1vur.png",
  "evidence":"Club-run site labeled Logo du club AS Montgaillard"}
]
def pick_bg(im):
 freq=collections.Counter()
 thumb=im.copy();thumb.thumbnail((100,100))
 for r,g,b,a in thumb.getdata():
  if a<120 or max(r,g,b)-min(r,g,b)<36 or max(r,g,b)<50:continue
  freq[(r//30,g//30,b//30)]+=1
 p=freq.most_common(1)[0][0] if freq else (7,7,7)
 return tuple(int(.58*(q*30+15)+.42*255) for q in p)
results=[]
for row in SOURCES:
 tid=row["team_id"]
 outfile=DEST/(tid+".png")
 assert not outfile.exists(),f"refuse overwrite {tid}"
 resp=requests.get(row["img"],timeout=35,headers={"User-Agent":"MMD31ClubBadgeRecovery/1.0"})
 resp.raise_for_status()
 raw=resp.content
 assert 1000<len(raw)<6_000_000,(tid,len(raw))
 src=Image.open(io.BytesIO(raw));src.verify()
 img=Image.open(io.BytesIO(raw)).convert("RGBA")
 assert img.width>=55 and img.height>=55,(tid,img.size)
 bbox=img.getchannel("A").getbbox()
 assert bbox is not None,tid
 img=img.crop(bbox)
 bg=Image.new("RGBA",(120,96),pick_bg(img)+(255,))
 img.thumbnail((102,84),Image.Resampling.LANCZOS)
 bg.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
 output=bg.convert("RGB")
 blob=io.BytesIO();output.save(blob,format="PNG",optimize=True)
 assert len(blob.getvalue())>=950,tid
 outfile.write_bytes(blob.getvalue())
 asset=Image.open(outfile)
 assert asset.size==(120,96) and asset.format=="PNG"
 record=dict(row,source_sha256=hashlib.sha256(raw).hexdigest(),png_sha256=hashlib.sha256(blob.getvalue()).hexdigest(),bytes=len(blob.getvalue()))
 results.append(record)
 print("PUBLISHED",tid,row["club"],len(blob.getvalue()),flush=True)
assert len({r["png_sha256"] for r in results})==len(results)
(AUD/"lot11_three_club_sources.json").write_text(json.dumps({"count":len(results),"assets":results},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
