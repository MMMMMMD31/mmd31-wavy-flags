from pathlib import Path
import io, json, hashlib, requests
from PIL import Image
import cairosvg
from urllib.parse import quote
p=Path("docs/cge35-europelight-v91/cup-invitations")
p.mkdir(parents=True,exist_ok=True)
rows=[
 {"id":1912262603001,"name":"KPV Kokkola","svg":"KPV_Kokkola.svg","background":"#E7F2E7"},
 {"id":1912262603002,"name":"OLS Oulu","svg":"OLS_Oulu.svg","background":"#EDF2FC"}
]
manifest=[]
for club in rows:
 src="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/finland/"+quote(club["svg"])
 res=requests.get(src,timeout=30); res.raise_for_status()
 if b"<svg" not in res.content[:500]:raise RuntimeError("invalid svg "+src)
 raster=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=res.content,output_width=500))).convert("RGBA")
 raster=raster.crop(raster.getbbox());raster.thumbnail((104,82),Image.Resampling.LANCZOS)
 target=Image.new("RGBA",(120,96),club["background"])
 target.alpha_composite(raster,((120-raster.width)//2,(96-raster.height)//2))
 path=p/(str(club["id"])+".png");target.convert("RGB").save(path,"PNG",optimize=True)
 b=path.read_bytes(); assert Image.open(io.BytesIO(b)).size==(120,96)
 manifest.append({**club,"source":src,"sha256":hashlib.sha256(b).hexdigest(),"png":str(path)})
(p/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print("TWO_FINNISH_CUP_INVITATIONS_OK")
