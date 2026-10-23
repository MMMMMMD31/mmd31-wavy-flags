#!/usr/bin/env python3
"""Complete the one missing verified Club Brugge KV flag without re-fetching GitHub API (rate limited)."""
import io,hashlib,json
from pathlib import Path
import requests,cairosvg
from PIL import Image,ImageFilter
ROOT=Path("docs/belgium-luxembourg-clubs-2026-27/v1")
status_path=ROOT/"status.json"
a=json.loads(status_path.read_text(encoding="utf8"))
assert a["ok"]==132 and a["missing"]==1
row=next(x for x in a["assets"] if x["id"]==1900262701001)
assert row["name"]=="Club Brugge KV" and row["status"]=="missing"
source="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/belgium/Club_Brugge.svg"
r=requests.get(source,timeout=40,headers={"User-Agent":"MMD31ClubBadgeGenerator/1.0"})
r.raise_for_status()
assert b"<svg" in r.content[:3000]
crest=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=r.content,output_width=520))).convert("RGBA")
bbox=crest.getchannel("A").getbbox()
assert bbox
crest=crest.crop(bbox)
crest.thumbnail((97,82),Image.Resampling.LANCZOS)
bg=Image.new("RGBA",(120,96),(112,160,213,255))
x,y=(120-crest.width)//2,(96-crest.height)//2
alpha=crest.getchannel("A")
shadow=Image.new("RGBA",crest.size,(0,0,0,0))
shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(.8)).point(lambda x:int(x*.28)))
bg.alpha_composite(shadow,(x+1,y+1))
bg.alpha_composite(crest,(x,y))
p=ROOT/"1900262701001.png"
bg.convert("RGB").save(p,optimize=True)
assert Image.open(p).size==(120,96)
row.update(status="ok",source_url=source,source_type="github:J.A.football-logos",url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-belux-crests-test-2026/{p.as_posix()}",background=[112,160,213],bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
row.pop("problem",None)
a.update(ok=133,missing=0)
assert len(a["assets"])==133 and len({x["id"] for x in a["assets"]})==133
status_path.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding="utf8")
print("SUCCESS: 133/133 real club crests with 120x96 color backgrounds")
