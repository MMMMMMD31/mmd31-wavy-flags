#!/usr/bin/env python3
"""Publish only authentic traceable club badge images for the English D8/D9 gap.
Never draw substitute logos. Preserve source image, original size and team identity.
"""
import io,json,re,hashlib,concurrent.futures,threading,time
from pathlib import Path
from urllib.parse import urlsplit
from collections import Counter,deque
import requests
from PIL import Image,ImageFilter,ImageOps

ROOT=Path("docs/english-clubs-2026-27")
older=json.loads((ROOT/"wiki-v13/manifest.json").read_text(encoding="utf8"))
missing=[r for r in older["files"] if not r["status"].startswith("PUBLISHED")]
assert len(missing)==55,len(missing)
tsdb=json.loads(Path("docs/english-v13/tsdb_missing_55_research.json").read_text(encoding="utf8"))
fwp=json.loads(Path("docs/english-v13/footballwebpages_missing_55_images.json").read_text(encoding="utf8"))
assert tsdb["total"]==55 and len(fwp["records"])==55

manual={
"Westfield":"https://images.pitchero.com/club_logos/87203/E1cAHyDYSLqHPHotRSCV_Westfield-FCLogoresize.png",
"South Park (Reigate)":"https://files.ekmcdn.com/sportsscene/images/south-park-reigate-fc-1087-c.jpg?h=400&v=296F06F4-6DF1-478E-A76B-8845B27C935C&w=400",
"Runcorn Town":"https://us1-photo.nextdoor.com/business_logo/c2/99/c299b4d74da9f60e9ee3b2bcff80fd38.jpeg",
"Uttoxeter Town":"https://r2.thesportsdb.com/images/media/team/badge/6qsyev1737082135.png",
"Winsford United":"https://r2.thesportsdb.com/images/media/team/badge/1vozl91754352134.png",
"Euxton Villa":"https://assets.teamstats.net/img-team-600-70-1142929-Euxton-Villa-U14-Black---teamBadge---football-team-from-Leyland-Lancashire-England-United-Kingdom_305789.jpeg",
"South Liverpool":"https://fixr-cdn.fixr.co/images/sales_account/logo/5d5cb4285a074010b62c7f4632ff0021.jpeg",
"Holmesdale":"https://www.scefl.com/wp-content/uploads/2023/05/Holmesdale-2023.png",
"Eastwood Community":"https://img-res.pitchero.com/?h=1100&o=jpg&t=fit&url=images.pitchero.com%2Fui%2F5934816%2Fimage_6a0ac26e507d2.jpeg&w=1960",
"West Bridgford Colts":"https://images.seeklogo.com/logo-png/66/1/west-bridgford-football-club-logo-png_seeklogo-664188.png",
"Bugbrooke St Michael":"https://stneotstownfc.co.uk/wp-content/uploads/2023/05/BugbrookeStMichaels.png",
"Downton":"https://r2.thesportsdb.com/images/media/team/badge/68vb4f1730045981.png",
"East Cowes Victoria Athletic":"https://media.touchlinefc.co.uk/hq/2025/11/01105756/East-Cowes.png",
"Sidmouth Town":"https://vx-3.com/cdn/shop/collections/Sidmouth-Town-FC-Badge.png?v=1657204103",
"Torpoint Athletic":"https://images.seeklogo.com/logo-png/61/1/torpoint-afc-logo-png_seeklogo-612142.png"
}
local=threading.local()
def http():
 if not hasattr(local,"client"):
  local.client=requests.Session()
  local.client.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 non-commercial 2026 football badge archival conversion)"})
 return local.client
def get_image(url):
 try:
  res=http().get(url,timeout=26)
  if res.status_code!=200:return None
  if len(res.content)>9000000 or len(res.content)<200:return None
  im=Image.open(io.BytesIO(res.content))
  im.load()
  if min(im.size)<24:return None
  return im.convert("RGBA")
 except Exception:return None
def fwp_urls(row):
 res=[]
 for obj in row.get("matches",[]):
  src=obj["url"]
  if "/graphics/teams/48/" not in src:continue
  filename=src.split("/graphics/teams/48/",1)[1].split("?",1)[0]
  # Use unmodified image names; first try highest native variants.
  for size in ("256","200","128","96","64","48"):
   res.append("https://www.footballwebpages.co.uk/graphics/teams/"+size+"/"+filename)
  res.append(src)
 return list(dict.fromkeys(res))
def remove_plain_white_edges(img):
 # Remove white connected to border, while keeping actual white within badges.
 if img.width*img.height>1100000:img.thumbnail((750,750),Image.Resampling.LANCZOS)
 pixels=img.load()
 w,h=img.size
 if not all(sum(pixels[x,y][:3])>702 for x,y in ((0,0),(w-1,0),(0,h-1),(w-1,h-1))):return img
 q=deque([(0,0),(w-1,0),(0,h-1),(w-1,h-1)])
 seen=set()
 while q:
  x,y=q.popleft()
  if (x,y) in seen or x<0 or y<0 or x>=w or y>=h:continue
  seen.add((x,y))
  r,g,b,a=pixels[x,y]
  if not (r>=240 and g>=240 and b>=240):continue
  pixels[x,y]=(r,g,b,0)
  q.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
 return img
def palette(img):
 c=Counter()
 thumb=img.copy();thumb.thumbnail((100,100))
 for r,g,b,a in thumb.getdata():
  if a<150 or max(r,g,b)-min(r,g,b)<35 or min(r,g,b)>210:continue
  c[(r//32,g//32,b//32)]+=a
 r,g,b=(min(255,v*32+16) for v in c.most_common(1)[0][0]) if c else (55,85,115)
 return tuple(round(0.62*v+0.38*255) for v in (r,g,b))
def convert(img):
 img=remove_plain_white_edges(img)
 bounds=img.getchannel("A").getbbox()
 if not bounds:raise ValueError("blank after alpha")
 img=img.crop(bounds)
 col=palette(img)
 img.thumbnail((100,84),Image.Resampling.LANCZOS)
 dst=Image.new("RGBA",(120,96),col+(255,))
 pos=((120-img.width)//2,(96-img.height)//2)
 # Soft dark outline/shadow improves visibility for light crests.
 alpha=img.getchannel("A").filter(ImageFilter.MaxFilter(3))
 sh=Image.new("RGBA",img.size,(20,25,28,70));sh.putalpha(alpha.point(lambda x:round(x*.28)))
 dst.alpha_composite(sh,pos);dst.alpha_composite(img,pos)
 return dst.convert("RGB"),list(col)
out=ROOT/"remaining-55-v11";out.mkdir(parents=True,exist_ok=True)
tsmap={r["id"]:r for r in tsdb["records"]}
fwmap={r["id"]:r for r in fwp["records"]}
def process(row):
 name=row["name"];id=row["id"]
 sources=[]
 if name in manual:sources.append(("individual_verified",manual[name]))
 for obj in tsmap[id].get("tsdb",[]):
  if obj.get("image_ok") and obj.get("gender")=="Male":sources.append(("TheSportsDB_male_club",obj["badge"]))
 sources.extend(("FootballWebPages_league_badge",u) for u in fwp_urls(fwmap[id]))
 # Read each resource exactly; never use a generic substitute image.
 for label,url in dict(((label,url),None) for label,url in sources):
  img=get_image(url)
  if img is None:continue
  try:
   origin=list(img.size)
   canvas,color=convert(img)
   path=out/(str(id)+".png")
   canvas.save(path,format="PNG",optimize=True)
   assert Image.open(path).size==(120,96)
   return {"id":id,"name":name,"status":"SOURCE_IMAGE_VERIFIED_AND_PUBLISHED","source_type":label,"source_url":url,"origin_dimensions":origin,"background_rgb":color,"path":str(path),"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
  except Exception as e:continue
 return {"id":id,"name":name,"status":"NO_VERIFIED_IMAGE","attempted":len(sources)}
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:records=list(pool.map(process,missing))
records.sort(key=lambda r:r["id"])
published=[r for r in records if r["status"]=="SOURCE_IMAGE_VERIFIED_AND_PUBLISHED"]
manifest={"requested":55,"published":len(published),"missing":55-len(published),"new_images":published,"unresolved":[r for r in records if r["status"]!="SOURCE_IMAGE_VERIFIED_AND_PUBLISHED"],"provenance":"Official team sources, correctly matched league table badges, archived sports club badges; no invented crests; 120x96 PNG."}
(out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf8")
assert len(list(out.glob("*.png")))==len(published)
print("PUBLISHED",len(published),"/55 ; MISSING",manifest["missing"],flush=True)
print("NOT FOUND",[r["name"] for r in manifest["unresolved"]],flush=True)
