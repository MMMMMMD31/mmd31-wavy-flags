from pathlib import Path
from PIL import Image, ImageOps
import hashlib,json
p=Path("docs/nir-clubs-2026-27/competition/northern_ireland_football_league.png")
assert p.is_file()
im=Image.open(p)
im.load()
assert im.width>=250 and im.height>=200
im=im.convert("RGBA")
im.thumbnail((470,470),Image.Resampling.LANCZOS)
background=Image.new("RGBA",(512,512),(255,255,255,255))
background.alpha_composite(im,((512-im.width)//2,(512-im.height)//2))
dest=p.with_name("northern_ireland_football_league_square.png")
background.convert("RGB").save(dest,optimize=True)
with Image.open(dest) as check: assert check.size==(512,512) and check.format=="PNG"
metadata={"identity":"Northern Ireland Football League (NIFL)","original":str(p),"new":str(dest),"dimensions":[512,512],"aspect":"1:1","sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"method":"original logo centered on white 512 square; no redrawing","source":"https://www.irishfa.com/media/48995/nifl-logo.png"}
dest.with_suffix(".json").write_text(json.dumps(metadata,indent=2))
print(metadata)
