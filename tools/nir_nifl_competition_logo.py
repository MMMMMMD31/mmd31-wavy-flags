from pathlib import Path
import hashlib,json,io,requests
from PIL import Image

url="https://www.irishfa.com/media/48995/nifl-logo.png"
r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=30)
r.raise_for_status()
assert r.content[:8]==b"\x89PNG\r\n\x1a\n","Source is not a PNG"
im=Image.open(io.BytesIO(r.content));im.load()
assert im.width>=100 and im.height>=50
out=Path("docs/nir-clubs-2026-27/competition/northern_ireland_football_league.png")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_bytes(r.content)
meta={
 "displayName":"Northern Ireland Football League (NIFL)",
 "sourcePage":"https://www.irishfa.com/ifa-domestic/leagues/nifl-premiership",
 "sourceImage":url,
 "publishedPath":str(out),
 "sourcePublisher":"Irish Football Association — NIFL Premiership page",
 "imageType":"PNG",
 "dimensions":[im.width,im.height],
 "sha256":hashlib.sha256(r.content).hexdigest(),
 "note":"NIFL is the competition's highest-division organizer; local divisions administered by other associations."
}
out.with_suffix(".json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(meta)
