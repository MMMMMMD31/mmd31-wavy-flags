#!/usr/bin/env python3
"""Create real-club crest PNG 120x96 and federation/logo images with provenance."""
import io,requests,json,re,time
from urllib.parse import quote,urljoin
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
import cairosvg
from PIL import Image
rows=json.loads(Path("tools/mmd31-four-d1-2026-roster.json").read_text(encoding="utf8"))
out=Path("docs/mmd31-four-first-divisions-2026");out.mkdir(parents=True,exist_ok=True)
ss=requests.Session();ss.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 2026 noncommercial football club logo research)"})
def get(url):
 for n in range(3):
  try:
   r=ss.get(url,timeout=24)
   if r.status_code in (429,500,502,503,504):time.sleep(n+1);continue
   r.raise_for_status();return r
  except Exception:
   if n==2:raise
   time.sleep(n+1)
def load_logo(url):
 r=get(url)
 if len(r.content)<200:raise ValueError("empty")
 if b"<svg" in r.content[:3000] or url.lower().split("?")[0].endswith(".svg"):
  raw=cairosvg.svg2png(bytestring=r.content,output_width=480)
 else:raw=r.content
 im=Image.open(io.BytesIO(raw)).convert("RGBA")
 bounds=im.getchannel("A").getbbox()
 if bounds:im=im.crop(bounds)
 if im.width<20 or im.height<20:raise ValueError("very small")
 return im
def create_flag(im,path):
 thumb=im.copy();thumb.thumbnail((100,90))
 colors=Counter()
 for r,g,b,a in thumb.getdata():
  if a>110 and max(r,g,b)-min(r,g,b)>25 and min(r,g,b)<220:
   colors[(r//32,g//32,b//32)]+=1
 if colors:
  rgb=tuple(min(255,k*32+16) for k in colors.most_common(1)[0][0])
 else:rgb=(65,90,125)
 bg=tuple(round(.72*c+.28*255) for c in rgb)
 im.thumbnail((102,84),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",(120,96),bg+(255,))
 canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 path.parent.mkdir(parents=True,exist_ok=True)
 canvas.convert("RGB").save(path,"PNG",optimize=True)
 assert Image.open(path).size==(120,96)
 return bg
faro_alias={
"NSÍ Runavík":["NSÍ Runavík"],
"KÍ Klaksvík":["KÍ Klaksvík"],
"HB Tórshavn":["Havnar Bóltfelag","HB Tórshavn"],
"Víkingur Gøta":["Víkingur Gøta"],
"B36 Tórshavn":["B36 Tórshavn"],
"EB/Streymur":["EB/Streymur"],
"Skála ÍF":["Skála ÍF"],
"AB Argir":["Argja Bóltfelag"],
"07 Vestur":["07 Vestur"],
"B68 Toftir":["B68 Toftir"]
}
def faroe_lookup(name):
 errs=[]
 for title in faro_alias[name]:
  for domain in ["en.wikipedia.org","fr.wikipedia.org"]:
   url="https://"+domain+"/wiki/"+quote(title.replace(" ","_"),safe="()_.")
   try:
    r=get(url)
    soup=BeautifulSoup(r.content,"html.parser")
    images=soup.select("table.infobox img")
    for im in images[:5]:
     src=im.get("src","")
     if src.startswith("//"):src="https:"+src
     if not src.startswith("https://"):continue
     fn=src.split("/")[-1].lower()
     if any(word in fn for word in ("kit","shirt","jersey","stadium","ground","home_colours","away_colours","flag_of")):continue
     if not re.search(r"\\.(png|jpe?g|webp|svg)(?:\\?|$)",src,re.I):continue
     try:
      logo=load_logo(src)
      return logo,src,url
     except Exception as ex:errs.append(str(ex)[:85])
   except Exception as ex:errs.append(str(ex)[:85])
 raise RuntimeError("No authentic image for "+name+": "+";".join(errs[:3]))
logos=[]
for i,row in enumerate(rows,1):
 country,name=row["country"],row["name"]
 if country=="faroe":
  im,src,article=faroe_lookup(name)
 else:
  path="logos/"+country+"/"+row["source_logo_name"]
  src="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/"+"/".join(quote(p,safe="") for p in path.split("/"))
  im=load_logo(src);article=None
 path=out/country/(str(row["id"])+".png")
 bg=create_flag(im,path)
 logos.append({**row,"source_url":src,"source_article":article,"github_path":path.as_posix(),"background_rgb":bg,"pixel_dimensions":[120,96],"source_label":"JoseArroyave SVG" if country!="faroe" else "Wikimedia club infobox"})
 print(f"{i}/{len(rows)}",country,name,flush=True)
assert len(logos)==54
federations={"wales":("Football Association of Wales (FAW)","logos/wales/Wales_National_Team.svg"),
"iceland":("Knattspyrnusamband Íslands (KSÍ)","logos/iceland/Iceland_National_Team.svg"),
"faroe":("Fótbóltssamband Føroya (FSF)","logos/faroe-islands/Faroe_Islands_National_Team.svg"),
"norway":("Norges Fotballforbund (NFF)","logos/norway/Norway_National_Team.svg")}
fedlogo=[]
for c,(assoc,sourcepath) in federations.items():
 url="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/"+"/".join(quote(p,safe="") for p in sourcepath.split("/"))
 im=load_logo(url)
 im.thumbnail((400,380),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",(440,420),(255,255,255,0))
 canvas.alpha_composite(im,((440-im.width)//2,(420-im.height)//2))
 target=out/c/"federation-logo.png";canvas.save(target,"PNG",optimize=True)
 fedlogo.append({"country":c,"association":assoc,"source_url":url,"github_path":target.as_posix(),"logo_size":[440,420],"source_note":"National team badge used as a federation-identifying crest; verify administrative current logo in-game."})
(out/"manifest.json").write_text(json.dumps({"clubs":logos,"federations":fedlogo,"expected":54,"published":len(logos)},ensure_ascii=False,indent=2),encoding="utf8")
print("SUCCESS",len(logos),"club crests and",len(fedlogo),"federation symbols",flush=True)
