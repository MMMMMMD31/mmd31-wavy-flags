#!/usr/bin/env python3
"""Generate authentic-source club crests only: never draw imaginary emblems."""
import requests,io,re,json,hashlib,time,sys
from pathlib import Path
from urllib.parse import quote,urljoin
from PIL import Image
import cairosvg
from bs4 import BeautifulSoup
S=requests.Session();S.headers.update({"User-Agent":"MMD31-football-club-logo-research/1.0 (contact via github MMMMMMD31)"})
ROOT=Path("docs/cge-four-first-divisions-2026-27");ROOT.mkdir(parents=True,exist_ok=True)
OUT=Path("data/cge-four-first-divisions-2026-27-crests.json");OUT.parent.mkdir(exist_ok=True)
C={
"GRC":[
("Panathinaikos","Panathinaikos F.C."),("Olympiacos","Olympiacos F.C."),("PAOK","PAOK FC"),("AEK_Athens","AEK Athens F.C."),("Aris_Thessaloniki","Aris Thessaloniki F.C."),("Kalamata","Kalamata F.C."),("OFI","OFI Crete F.C."),("Iraklis_Thessaloniki","Iraklis F.C. (Thessaloniki)"),("Panetolikos","Panetolikos F.C."),("A.E._Kifisia","A.E. Kifisia F.C."),("Asteras_Tripolis","Asteras Tripolis F.C."),("Atromitos","Atromitos F.C."),("Levadiakos","Levadiakos F.C."),("Volos_NFC","Volos N.F.C.")],
"CYP":[
("AEL_Limassol","AEL Limassol"),("AEK_Larnaca","AEK Larnaca FC"),("Omonoia_Nicosia","AC Omonia"),("Apollon_Limassol","Apollon Limassol"),("Pafos","Pafos FC"),("Aris_Limassol","Aris Limassol FC"),("APOEL","APOEL FC"),("Omonia_29M","PAC Omonia 29M"),("Omonia_Aradippou","Omonia Aradippou"),("Olympiakos_Nicosia","Olympiakos Nicosia"),("Nea_Salamis","Nea Salamis Famagusta FC"),("Krasava_Ypsonas","Krasava ENY Ypsonas FC"),("Anorthosis_Famagusta","Anorthosis Famagusta FC"),("Karmiotissa","Karmiotissa FC")],
"MLT":[
(None,"Valletta F.C."),(None,"Marsaxlokk F.C."),(None,"Floriana F.C."),(None,"Mosta F.C."),("Hamrun_Spartans","Ħamrun Spartans F.C."),(None,"Sliema Wanderers F.C."),(None,"Balzan F.C."),(None,"Birkirkara F.C."),(None,"Hibernians F.C."),(None,"Żabbar St. Patrick F.C."),(None,"Gżira United F.C."),(None,"Birżebbuġa St. Peter's F.C.")],
"ISR":[
("Maccabi_Haifa","Maccabi Haifa F.C."),("Maccabi_Tel-Aviv","Maccabi Tel Aviv F.C."),("Hapoel_Tel_Aviv","Hapoel Tel Aviv F.C."),("Hapoel_Be'er_Sheva","Hapoel Be'er Sheva F.C."),("Beitar_Jerusalem","Beitar Jerusalem F.C."),("Maccabi_Netanya","Maccabi Netanya F.C."),("Hapoel_Haifa","Hapoel Haifa F.C."),("Bnei_Sakhnin","Bnei Sakhnin F.C."),("Hapoel_Jerusalem","Hapoel Jerusalem F.C."),("Maccabi_Petah_Tikva","Maccabi Petah Tikva F.C."),("Hapoel_Ramat_Gan_Givatayim","Hapoel Ramat Gan Givatayim F.C."),("Hapoel_Petah_Tikva","Hapoel Petah Tikva F.C."),("Hapoel_Kiryat_Shmona","Hapoel Ironi Kiryat Shmona F.C."),("Ironi_Tiberias","Ironi Tiberias F.C.")]}
ORG={"GRC":"Hellenic Football Federation","CYP":"Cyprus Football Association","MLT":"Malta Football Association","ISR":"Israel Football Association"}
IDS={"GRC":1884510000001,"CYP":1884510000101,"MLT":1884510000201,"ISR":1884510000301}
def get(u):
 try:
  r=S.get(u,timeout=25)
  if r.status_code==200 and len(r.content)>350:return r.content,r.url
 except Exception as e: print("ERR",u,str(e)[:95],flush=True)
 return None,None
def fetch_wiki_image(page):
 # Wikimedia's HTML page often exposes authentic infobox logo on the first row.
 url="https://en.wikipedia.org/wiki/"+quote(page.replace(" ","_"),safe="(),'._-")
 raw,actual=get(url)
 if raw:
  soup=BeautifulSoup(raw,"html.parser")
  info=soup.select_one("table.infobox")
  if info:
   for img in info.select("img")[:7]:
    alt=(img.get("alt") or "").lower()
    src=img.get("src") or ""
    if ("logo" in alt or "crest" in alt or ".svg" in src or ".png" in src):
     src=urljoin(url,src if not src.startswith("//") else "https:"+src)
     b,_=get(src)
     if b:return b,src
 # Wikimedia API pageimages endpoint
 api="https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&pithumbsize=520&titles="+quote(page)
 raw,_=get(api)
 if raw:
  try:
   j=json.loads(raw);p=next(iter(j["query"]["pages"].values()))
   link=p.get("thumbnail",{}).get("source")
   if link:
    b,_=get(link)
    if b:return b,link
  except Exception:pass
 return None,None
def render(data):
 d=data.lstrip()
 if b"<svg" in d[:500] or d.startswith(b"<?xml"):
  png=cairosvg.svg2png(bytestring=data,output_width=450,output_height=450)
  im=Image.open(io.BytesIO(png)).convert("RGBA")
 else: im=Image.open(io.BytesIO(data)).convert("RGBA")
 if im.size[0]<24 or im.size[1]<24:raise ValueError("crest low resolution")
 im.thumbnail((94,82),Image.Resampling.LANCZOS)
 # Background selected to contrast with dominant crest color
 pal=im.getcolors(maxcolors=500000)
 candidates=[(count,color) for count,color in (pal or []) if color[3]>150 and max(color[:3])-min(color[:3])>30]
 if candidates:
  col=max(candidates,key=lambda x:x[0])[1][:3]
  bgcolor=tuple(int(.62*x+.38*255) for x in col)
 else:bgcolor=(219,225,234)
 bg=Image.new("RGBA",(120,96),bgcolor+(255,))
 bg.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return bg.convert("RGB"),bgcolor
manifest=[]
for key,teams in C.items():
 for ix,(stem,wiki) in enumerate(teams):
  ident=IDS[key]+ix
  source=None;data=None
  if stem:
   u=f"https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/{dict(GRC='greece',CYP='cyprus',MLT='malta',ISR='israel')[key]}/{quote(stem)}.svg"
   data,source=get(u)
  if data is None:data,source=fetch_wiki_image(wiki)
  item={"id":ident,"country":key,"wikipedia":wiki,"repositoryStem":stem,"source":source,"authentic_source":bool(data),"validation":"not_checked"}
  if data:
   try:
    png,bg=render(data)
    path=ROOT/f"{ident}.png";png.save(path,"PNG",optimize=True)
    assert Image.open(path).size==(120,96)
    item.update(validation="source_retrieved_120x96_visual_review_pending",background=list(bg),file=path.as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
   except Exception as e:item.update(validation="image_error",error=str(e))
  else:item.update(validation="source_missing")
  manifest.append(item)
  print(key,ix+1,len(teams),item["validation"],wiki,flush=True)
  if ix%5==4:
   OUT.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
OUT.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for key,page in ORG.items():
 data,source=fetch_wiki_image(page)
 item={"country":key,"page":page,"source":source}
 if data:
  try:
   im,bg=render(data);dest=ROOT/f"federation_{key}.png";im.save(dest,"PNG",optimize=True)
   item.update(validation="source_retrieved",file=dest.as_posix(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
  except Exception as e:item["error"]=str(e)
 (ROOT/f"federation_{key}.json").write_text(json.dumps(item,ensure_ascii=False,indent=2)+"\n")
 print("FEDERATION",key,item,flush=True)
print("SUMMARY",len([x for x in manifest if x["validation"].startswith("source_retrieved")]),"/",len(manifest),flush=True)
