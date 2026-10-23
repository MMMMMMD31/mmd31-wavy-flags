#!/usr/bin/env python3
"""Finish MMD31 NI crests from the official NAFL club catalogue, source audited."""
from pathlib import Path
import io,requests,json,hashlib
from PIL import Image,ImageOps
out=Path("docs/nir-clubs-2026-27/v13-extension");out.mkdir(parents=True,exist_ok=True)
catalogue="https://www.thenafl.co.uk/data/clubs-dev.json"
s=requests.Session();s.headers.update({"User-Agent":"MMD31 club identity validation (Mozilla/5.0)"})
teams=s.get(catalogue,timeout=25);teams.raise_for_status()
matches=[x for x in teams.json() if x.get("name")=="St Patricks Y.M. F.C." and x.get("slug")=="st-patricks-ym"]
assert len(matches)==1, f"Expected one distinct club identity, got {len(matches)}"
club=matches[0]
assert club.get("badge")=="st-patricks-ym.png",club
logo_url="https://www.thenafl.co.uk/images/badges/"+club["badge"]
r=s.get(logo_url,timeout=25);r.raise_for_status()
assert "image" in r.headers.get("content-type",""),r.headers.get("content-type")
src=Image.open(io.BytesIO(r.content));src.load()
assert src.size[0]>=40 and src.size[1]>=40,src.size
src=src.convert("RGBA")
# Remove only uniformly transparent borders if any; keep the real club crest untouched.
mask=src.getchannel("A");bounds=mask.getbbox()
assert bounds is not None,"Empty badge"
src=src.crop(bounds)
# Club's official primary colour is #008000; use its pale hue for a legible flat plate.
bg=(213,238,213)
src.thumbnail((102,82),Image.Resampling.LANCZOS)
canvas=Image.new("RGBA",(120,96),bg+(255,))
canvas.alpha_composite(src,((120-src.width)//2,(96-src.height)//2))
rgb=canvas.convert("RGB")
output=[]
for team_id in (1900231300166,1900231300255):
    path=out/(str(team_id)+".png")
    rgb.save(path,format="PNG",optimize=True)
    with Image.open(path) as check:
        assert check.format=="PNG" and check.size==(120,96)
    output.append({"id":team_id,"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"source":logo_url,"dimensions":[120,96],"identity":"St Patricks Y.M. F.C.","status":"PUBLIE","review":"official NAFL catalogue name slug badge exact"})
status={"catalogue":catalogue,"name":club.get("name"),"slug":club.get("slug"),"club_id":club.get("id"),"official_badge":club.get("badge"),"source":logo_url,"original_dimensions":list(Image.open(io.BytesIO(r.content)).size),"image_sha256":hashlib.sha256(r.content).hexdigest(),"output":output}
(out/"st_patricks_ym_badges_audit.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(status,ensure_ascii=False))
