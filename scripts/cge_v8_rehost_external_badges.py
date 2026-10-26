import io,json,hashlib,csv,statistics
from pathlib import Path
from PIL import Image,ImageStat,ImageChops
import requests
root=Path("docs/cge-v8-contrast-fixes")
items=json.loads((root/"external_16_sources.json").read_text(encoding="utf8"))
s=requests.Session()
s.headers.update({"User-Agent":"Mozilla/5.0 (CGE V8 football badges)", "Accept":"image/avif,image/webp,image/apng,image/*,*/*"})
results=[]
for id,name,url in items:
 try:
  r=s.get(url,timeout=30)
  r.raise_for_status()
  if not (10 < len(r.content) < 7_000_000):raise ValueError("invalid source size")
  im=Image.open(io.BytesIO(r.content)).convert("RGBA")
  iw,ih=im.size
  if min(im.size)<60:raise ValueError("logo below 60px")
  src=im.copy()
  alphaext=im.getchannel("A").getextrema()
  if alphaext[0]<255:
   # Trim transparent padding, preserving authentic logo geometry.
   bbox=im.getchannel("A").getbbox()
   if bbox:im=im.crop(bbox)
  # Contrast from source image: for solid background, replace only the uniform
  # background color. Otherwise keep the exact original pixels.
  corners=[im.getpixel(q)[:3] for q in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]]
  flat=all(max(abs(c[i]-corners[0][i]) for i in range(3))<9 for c in corners)
  # Compute foreground average brightness; choose contrasting mild background.
  bg0=corners[0]
  pix=im.convert("RGB");w,h=pix.size
  samples=[pix.getpixel((x,y)) for y in range(0,h,max(1,h//48)) for x in range(0,w,max(1,w//48))]
  colors=[c for c in samples if sum(abs(c[i]-bg0[i]) for i in range(3))>35]
  brightness=sum(sum(c)/3 for c in colors)/len(colors) if colors else 110
  bg=(7,41,77) if brightness>=152 else (227,237,247)
  if alphaext[0]<255:
   # Transparent authentic source, no background removal necessary.
   im.thumbnail((106,84),Image.Resampling.LANCZOS)
   dst=Image.new("RGBA",(120,96),bg+(255,))
   dst.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  elif flat:
   # Source already flattened; remap only flat outside background pixels.
   im.thumbnail((106,84),Image.Resampling.LANCZOS)
   dst=Image.new("RGBA",(120,96),bg+(255,))
   px=im.load()
   for yy in range(im.height):
    for xx in range(im.width):
     cr=px[xx,yy][:3]
     dd=sum((cr[k]-bg0[k])**2 for k in range(3))**.5
     a=max(0,min(1,(dd-4)/20))
     dst.putpixel(((120-im.width)//2+xx,(96-im.height)//2+yy),tuple(round(cr[i]*a+bg[i]*(1-a)) for i in range(3))+(255,))
  else:
   im.thumbnail((106,84),Image.Resampling.LANCZOS)
   dst=Image.new("RGBA",(120,96),bg+(255,))
   dst.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
  filepath=root/f"{id}.png"
  dst.convert("RGB").save(filepath,"PNG",optimize=True)
  results.append([id,name,"published",url,f"{iw}x{ih}",hashlib.sha256(r.content).hexdigest(),"flat" if flat else "nonflat"])
  print("SUCCESS",id,name,iw,ih,flush=True)
 except Exception as e:
  results.append([id,name,"source_error",url,"","",str(e)[:150]])
  print("SOURCE_ERROR",id,name,repr(e)[:180],flush=True)
with (root/"external_16_audit.csv").open("w",encoding="utf8",newline="") as f:
 w=csv.writer(f)
 w.writerow(["teamId","clubName","status","sourceURL","originalSize","sourceSha256","imageBackgroundTypeOrError"])
 w.writerows(results)
print("RESULT",sum(r[2]=="published" for r in results),"/",len(results))
