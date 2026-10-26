import io,subprocess
from PIL import Image
from pathlib import Path
items=[
 ('1897600004005','mmd31-cge36-four-european-d1-20261024','docs/cge36-four-leagues-2026/clubs/PL/1897600004005.png',(8,35,75)),
 ('1906200000008','mmd31-cge-v15-four-d1-20261024-test','docs/cge-v15-four-d1-20261024/1906200000008.png',(244,237,250))]
outdir=Path("docs/cge-v8-contrast-fixes");outdir.mkdir(parents=True,exist_ok=True)
for id,branch,path,new_bg in items:
 image=Image.open(io.BytesIO(subprocess.check_output(["git","show",f"origin/{branch}:{path}"]))).convert("RGB")
 assert image.size==(120,96)
 old=image.getpixel((0,0))
 assert all(image.getpixel(q)==old for q in [(119,0),(0,95),(119,95)])
 result=Image.new("RGB",(120,96),new_bg)
 for y in range(96):
  for x in range(120):
   c=image.getpixel((x,y))
   dist=sum((c[i]-old[i])**2 for i in range(3))**.5
   a=min(1,max(0,(dist-2)/12))
   result.putpixel((x,y),tuple(round(c[i]*a+new_bg[i]*(1-a)) for i in range(3)))
 result.save(outdir/f"{id}.png","PNG",optimize=True)
 print("CONTRAST_FIXED",id,old,new_bg,flush=True)
