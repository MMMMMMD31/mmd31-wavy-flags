from pathlib import Path
from PIL import Image
from io import BytesIO
import requests,hashlib,json
url="https://becollective-uk.imgix.net/groups/5e721f18f06e690011cf2db0/avatars/8c32e612-ab6e-4f21-b8e3-2ae1fa076d98.png"
r=requests.get(url,timeout=30,headers={"User-Agent":"Mozilla/5.0"})
r.raise_for_status()
image=Image.open(BytesIO(r.content))
image.load()
assert image.width>=128 and image.height>=128
path=Path("docs/nir-clubs-2026-27/competition/irish_football_association.png")
path.parent.mkdir(parents=True,exist_ok=True)
image.convert("RGBA").save(path,optimize=True)
assert Image.open(path).format=="PNG"
meta={"governing_body":"Irish Football Association (IFA)","source":url,"width":image.width,"height":image.height,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"status":"official logo reproduced from the Irish FA volunteer organisation listing; IFA is umbrella, NIFL and NAFL remain distinct operators"}
path.with_suffix(".json").write_text(json.dumps(meta,indent=2))
print(meta)
