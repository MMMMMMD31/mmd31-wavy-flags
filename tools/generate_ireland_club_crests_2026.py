#!/usr/bin/env python3
"""MMD31 Republic of Ireland authentic club-crests, 120x96 club-color PNGs."""
import io, re, json, hashlib, unicodedata
from pathlib import Path
from urllib.parse import urljoin, quote
from collections import Counter
import requests, cairosvg
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

ROOT = Path("docs/irish-clubs-2026/v1")
ROOT.mkdir(parents=True,exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent":"MMD31-football-crest-research/1.0 (source-credited; not an official website)","Accept":"text/html,image/avif,image/webp,image/*,*/*"})
REPO="JoseArroyave/football-logos"
D1=["Bohemians","Derry City","Drogheda United","Dundalk","Galway United","Shamrock Rovers","Shelbourne","Sligo Rovers","St Patrick's Athletic","Waterford"]
D2=["Athlone Town","Bray Wanderers","Cobh Ramblers","Cork City","Finn Harps","Kerry FC","Longford Town","Treaty United","UCD","Wexford FC"]
D3=["Bonagee United","Cockhill Celtic","Home Farm DCU","Lucan United","Mervue United","Letterkenny Rovers","Mayo FC","Salthill Devon","St. Francis","TU Dublin","CK United","Killarney Celtic","Newbridge Town","UCC Soccer","Villa FC"]
SVGS={
"Bohemians":"Bohemian.svg","Derry City":"Derry_City.svg","Drogheda United":"Drogheda_United.svg","Dundalk":"Dundalk_FC.svg","Galway United":"Galway_United_FC.svg",
"Shamrock Rovers":"Shamrock_Rovers.svg","Shelbourne":"Shelbourne.svg","Sligo Rovers":"Sligo_Rovers.svg","St Patrick's Athletic":"St_Patrick's_Athletic.svg","Waterford":"Waterford.svg",
"Athlone Town":"Athlone_Town.svg","Bray Wanderers":"Bray_Wanderers.svg","Cobh Ramblers":"Cobh_Ramblers.svg","Cork City":"Cork_City.svg","Finn Harps":"Finn_Harps.svg","Kerry FC":"Kerry.svg",
"Longford Town":"Longford_Town.svg","Treaty United":"Treaty_United.svg","UCD":"University_College_Dublin.svg","Wexford FC":"Wexford.svg"}
COLORS={
"Bohemians":"#C4464B","Derry City":"#CF3D45","Drogheda United":"#A8D0DE","Dundalk":"#C5C5C5","Galway United":"#8DB3D6",
"Shamrock Rovers":"#83CDA0","Shelbourne":"#D98786","Sligo Rovers":"#D27774","St Patrick's Athletic":"#E28D8B","Waterford":"#8AB2DB",
"Athlone Town":"#8A96DC","Bray Wanderers":"#86BFA2","Cobh Ramblers":"#CFA1B9","Cork City":"#DB6665","Finn Harps":"#98B6D0","Kerry FC":"#A4D7BF",
"Longford Town":"#CF8489","Treaty United":"#C4A5DF","UCD":"#9BC5E1","Wexford FC":"#C7AEDF",
"Bonagee United":"#B5BFCB","Cockhill Celtic":"#92C8A1","Home Farm DCU":"#A6BFDA","Lucan United":"#B6C5E4","Mervue United":"#8FC8C0",
"Letterkenny Rovers":"#98B7D9","Mayo FC":"#D49EAD","Salthill Devon":"#9FC1DC","St. Francis":"#C5A9C6","TU Dublin":"#7DAECB",
"CK United":"#C6B5D4","Killarney Celtic":"#8BC4A3","Newbridge Town":"#B6BFDA","UCC Soccer":"#9BAFE0","Villa FC":"#C4A4B8"}
ALIASES={
"Home Farm DCU":["home farm dcu","home farm"],"St. Francis":["st. francis","st francis"],
"Mayo FC":["mayo","mayo fc"],"TU Dublin":["tu dublin","tu dublin fc","tud","tudublin"],
"UCC Soccer":["ucc soccer","ucc afc","ucc"],"Villa FC":["villa fc","villa"],
"CK United":["ck united","ck united fc"],"Mervue United":["mervue united","mervue united fc"],
"Salthill Devon":["salthill devon","salthill devon fc"],"Bonagee United":["bonagee united","bonagee united fc"],
"Cockhill Celtic":["cockhill celtic","cockhill celtic fc"],"Lucan United":["lucan united","lucan united fc"],
"Letterkenny Rovers":["letterkenny rovers","letterkenny rovers fc"],"Newbridge Town":["newbridge town","newbridge town fc"],
"Killarney Celtic":["killarney celtic","killarney celtic fc"]}
def norm(s):
 return re.sub(r"[^a-z0-9]+"," ",unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()).strip()
def download(url):
 r=S.get(url,timeout=35);r.raise_for_status()
 if not (r.content.startswith(b"\x89PNG") or b"<svg" in r.content[:2000] or r.content.startswith((b"\xff\xd8",b"RIFF",b"GIF8"))):
  raise ValueError("not a supported image "+r.headers.get("content-type",""))
 return r.content
def discover_fai():
 page="https://www.fai.ie/national-league/clubs/"
 r=S.get(page,timeout=35);r.raise_for_status()
 soup=BeautifulSoup(r.text,"html.parser")
 imgs=[]
 for tag in soup.find_all("img"):
  alt=tag.get("alt","") or ""
  src=(tag.get("data-src") or tag.get("src") or "")
  if not src or src.startswith("data:"):continue
  if src.startswith("//"):src="https:"+src
  src=urljoin(page,src)
  imgs.append(dict(alt=alt,url=src,parent=(tag.parent.get_text(" ",strip=True)[:120] if tag.parent else "")))
 print("FAI images",len(imgs),[(v['alt'][:35],v['url'][:75]) for v in imgs[:35]],flush=True)
 return imgs
def fai_match(name,images):
 names=[norm(name)]+[norm(a) for a in ALIASES.get(name,[])]
 cand=[]
 for item in images:
  alt=norm(item['alt'])
  if any(alt==n or alt==n+" visit club page" for n in names):
   cand.append((2,item))
  elif any(n and (n in alt) for n in names) and not any(generic in alt for generic in ("fa i","national league")):
   cand.append((1,item))
 if not cand:return None
 cand.sort(key=lambda t:t[0],reverse=True)
 top=[v for score,v in cand if score==cand[0][0]]
 if len({x["url"] for x in top})!=1:raise ValueError("Ambiguous FAI image: "+name+" "+str(top[:4]))
 return top[0]
def convert(raw):
 if b"<svg" in raw[:2000]:raw=cairosvg.svg2png(bytestring=raw,output_width=600,output_height=600)
 img=Image.open(io.BytesIO(raw)).convert("RGBA")
 alpha=img.getchannel("A")
 bbox=alpha.getbbox()
 if not bbox:raise ValueError("empty transparent image")
 if bbox and img.width>2 and img.height>2:img=img.crop(bbox)
 return img
def render(img,color):
 # Create flag with authentic logo unchanged and centered, not an AI reconstruction.
 bg=Image.new("RGBA",(120,96),color)
 crest=img.copy();crest.thumbnail((98,86),Image.Resampling.LANCZOS)
 bg.alpha_composite(crest,((120-crest.width)//2,(96-crest.height)//2))
 return bg.convert("RGB")
assets=[];missing=[]
try:FAI_IMAGES=discover_fai()
except Exception as e:FAI_IMAGES=[];print("FAI discovery error",str(e),flush=True)
for i,name in enumerate(D1+D2+D3,1):
 tid=1883261000000+i
 candidates=[]
 if name in SVGS:
  candidates.append(("Verified crest repository",f"https://raw.githubusercontent.com/{REPO}/main/logos/republic-of-ireland/"+quote(SVGS[name])))
 else:
  m=fai_match(name,FAI_IMAGES)
  if m:candidates.append(("FAI National League official site",m["url"]))
 # for reliable D3 source also retry FAI National League club pages when directory is incomplete.
 error=None
 for provenance,url in candidates:
  try:
   raw=download(url);img=convert(raw)
   if img.width<25 or img.height<25:raise ValueError("crest image too small")
   result=render(img,COLORS[name]);fn=ROOT/(str(tid)+".png")
   result.save(fn,format="PNG",optimize=True)
   with Image.open(fn) as check:assert check.size==(120,96) and check.format=="PNG"
   assets.append(dict(id=tid,name=name,tier=1 if i<=10 else 2 if i<=20 else 3,flag_url=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-ireland-2026-crest-test/{fn.as_posix()}",source_url=url,source_origin=provenance,source_sha256=hashlib.sha256(raw).hexdigest(),background=COLORS[name],png_bytes=fn.stat().st_size))
   print("OK",name,url,flush=True);break
  except Exception as e:
   error=str(e);print("CANDIDATE FAILED",name,url,error[:250],flush=True)
 else:missing.append(dict(id=tid,name=name,attempted=candidates,error=error or "No trustworthy original crest source matched"))
status=dict(description="Authentic club crests centered on 120x96 solid club-color flags (no victory flags)",expected=35,published=len(assets),missing=len(missing),assets=assets,unresolved=missing)
(ROOT/"status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("CRESTS PUBLISHED",len(assets),"of",35,"MISSING:",[x["name"] for x in missing],flush=True)
assert len(assets)>=20,"National D1/D2 crest source failed unexpectedly"
