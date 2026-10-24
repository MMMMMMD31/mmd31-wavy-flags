from pathlib import Path
import io,json,requests
from PIL import Image
import cairosvg
p=Path("docs/english-clubs-2026-27/competition")
p.mkdir(parents=True,exist_ok=True)
url="https://commons.wikimedia.org/wiki/Special:Redirect/file/The_FA_logo.svg"
s=requests.Session();s.headers["User-Agent"]="Mozilla/5.0 (compatible; MMD31 public FA logo conversion)"
r=s.get(url,timeout=35)
r.raise_for_status()
assert b"<svg" in r.content[:2000],(r.status_code,r.url,len(r.content),r.text[:120])
res=cairosvg.svg2png(bytestring=r.content,output_width=600)
img=Image.open(io.BytesIO(res)).convert("RGBA")
img.thumbnail((576,240),Image.Resampling.LANCZOS)
out=Image.new("RGBA",(640,270),(255,255,255,0))
out.alpha_composite(img,((640-img.width)//2,(270-img.height)//2))
save=p/"the-fa-logo.png";out.save(save,format="PNG",optimize=True)
assert Image.open(save).size==(640,270)
(p/"source.json").write_text(json.dumps({"organism":"The Football Association (The FA)","logo_source":url,"downloaded_from":r.url,"size":[640,270],"limits":"FA administers NLS; Premier League and EFL separately govern professional levels. Editor display not yet checked in game."},indent=2))
print("Validated logo",save,save.stat().st_size)
