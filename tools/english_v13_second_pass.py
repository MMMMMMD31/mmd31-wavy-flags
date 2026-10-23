import json,io,re,concurrent.futures,threading,time,random
from urllib.parse import quote,urlsplit
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
import requests
D=Path("docs/english-clubs-2026-27/wiki-v13")
M=json.loads((D/"manifest.json").read_text(encoding="utf8"))
missing=[x for x in M["files"] if x["status"]=="NO_VERIFIED_REAL_IMAGE"]
local=threading.local()
ALIASES={
 "AFC Varndeanians":["A.F.C. Varndeanians","AFC Varndeanians F.C."],
 "Darlaston Town":["Darlaston Town (1874) F.C."],
 "Horsham YMCA":["Horsham Y.M.C.A. F.C.","Horsham YMCA F.C."],
 "Eastbourne United Association":["Eastbourne United A.F.C."],
 "Tavistock Association":["Tavistock A.F.C."],
 "Bournemouth Poppies":["Bournemouth F.C."],
 "Coton Green Saturday":["Coton Green F.C."],
 "AFC Wolverhampton City":["A.F.C. Wulfrunians"],
 "Sutton United (Birmingham)":["Sutton United F.C. (Birmingham)"],
 "Cray Valley PM":["Cray Valley Paper Mills F.C."],
 "Egham Town":["Egham Town F.C."],
 "Fakenham Town":["Fakenham Town F.C."],
}
def get(url):
 if not hasattr(local,"session"):
  local.session=requests.Session()
  local.session.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 non-commercial football crest bibliographic research)"})
 for x in range(4):
  try:
   r=local.session.get(url,timeout=24)
   if r.status_code in [429,500,502,503,504] and x<3:
    time.sleep((x+1)*1.6+random.random());continue
   return r
  except requests.RequestException:
   if x==3:raise
   time.sleep(x+1)
def key(name):
 name=name.lower().replace("&","and").replace("’","'")
 name=re.sub(r"association football club|football club|a\.?f\.?c\.?|f\.?c\.?","",name)
 return re.sub("[^a-z0-9]","",name)
def run(item):
 name=item["name"];id=item["id"]
 variations=[name+" F.C.",name+" A.F.C.",name]
 if name.startswith("AFC "):variations.extend(["A.F.C. "+name[4:],name])
 variations=ALIASES.get(name,[])+variations
 for candidate in dict.fromkeys(variations):
  url="https://en.wikipedia.org/wiki/"+quote(candidate.replace(" ","_"),safe="()_.")
  try:
   h=get(url)
   if h.status_code!=200:continue
   soup=BeautifulSoup(h.content,"html.parser")
   title=(soup.title.get_text(" ",strip=True) if soup.title else "").replace(" - Wikipedia","")
   if key(title)!=key(name) and candidate not in ALIASES.get(name,[]):continue
   for ix,tag in enumerate(soup.select("table.infobox img")[:3]):
    src=tag.get("src") or ""
    if src.startswith("//"):src="https:"+src
    src=src.split("?")[0]
    if not src.startswith("https://") or "wikimedia.org" not in urlsplit(src).netloc:continue
    file=src.split("/")[-1].lower()
    if any(k in file for k in ("kit","shirt","stadium","ground","flag","aerial","homecolors","awaycolors")):continue
    if not re.search(r"\.(png|jpe?g|webp|svg)$",file,re.I):continue
    if ix>0 and not any(k in file for k in ("logo","crest","badge","emblem")):continue
    im=get(src)
    if im.status_code!=200:continue
    if file.endswith(".svg"):
     import cairosvg
     img=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=im.content,output_width=240))).convert("RGBA")
    else:img=Image.open(io.BytesIO(im.content)).convert("RGBA")
    if img.width<30 or img.height<30:continue
    img.thumbnail((98,82),Image.Resampling.LANCZOS)
    from collections import Counter
    palette=Counter()
    for r,g,b,a in img.getdata():
     if a>150 and max(r,g,b)-min(r,g,b)>28:palette[(r//32,g//32,b//32)]+=1
    rgb=tuple(min(255,x*32+16) for x in palette.most_common(1)[0][0]) if palette else (55,75,95)
    bg=tuple(round(.7*x+.3*255) for x in rgb)
    dest=Image.new("RGBA",(120,96),bg+(255,))
    dest.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
    path=D/(str(id)+".png")
    dest.convert("RGB").save(path,"PNG",optimize=True)
    return {"id":id,"name":name,"status":"PUBLISHED_REAL_WIKIPEDIA_INFOBOX_SECOND_PASS","source_logo":src,"verified_page_title":title,"wikipedia_article":url,"github_path":path.as_posix(),"bytes":path.stat().st_size,"quality_note":"Wikipedia football-club infobox first image, possible identity alias"}
  except Exception:continue
 return item
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 results=list(pool.map(run,missing))
after={r["id"]:r for r in results}
M["files"]=[after.get(r["id"],r) for r in M["files"]]
M["published"]=sum(r["status"].startswith("PUBLISHED") for r in M["files"])
M["unverified"]=len(M["files"])-M["published"]
M["second_pass_sources"]="Wikipedia football club first infobox logo; candidate named aliases requiring review"
(D/"manifest.json").write_text(json.dumps(M,ensure_ascii=False,indent=2),encoding="utf8")
print("SECOND PASS",len(missing)-M["unverified"],"added ; total",M["published"],"remaining",M["unverified"],flush=True)
