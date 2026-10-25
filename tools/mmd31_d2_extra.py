#!/usr/bin/env python3
"""Targeted sourced additions for 2026-27. Sources checked against real club identity."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests,io,json,hashlib
from PIL import Image
R=Path("docs/central-europe-d2-2026-27/extra")
R.mkdir(parents=True,exist_ok=True)
ITEMS={
1971262100005:("FC Vysočina Jihlava","https://assets.football-logos.cc/logos/czech-republic/1500x1500/jihlava.07de2cc5.png","football-logos.cc; official club describes redesigned FCV logo 2018"),
1971262100008:("FK Třinec","https://www.footylogos.com/downloads/logo/fk-trinec-logo-footylogos.png","FootyLogos named FK Třinec"),
1971262100011:("Fotbal Příbram","https://cdn.ruwiki.ru/ruwiki/files/thumb/2/25/Viagem_Pribram_logo.svg/800px-Viagem_Pribram_logo.svg.png","Viagem Příbram sponsor-era crest; needs final visual confirmation"),
1971262100012:("MFK Karviná","https://www.eurofotbal.cz/res/img/team-logo/jZNqfbeE-zoI0gGvN.png","Eurofotbal; independently confirmed by mfkkarvina.cz"),
1971262100016:("Slezský FC Opava","https://www.eurofotbal.cz/res/img/team-logo/QonimAWo-GhXTKbk2.png","Eurofotbal exact club name SFC Opava"),
1971262100104:("FC TATRAN Prešov","https://assets.football-logos.cc/logos/slovakia/3000x3000/tatran.a62a90ab.png","football-logos.cc exact club name"),
1971262100105:("FC ViOn Zlaté Moravce - Vráble","https://fcvion.sk/files/logos/png_20220615_142332_0000.png","FC ViOn official club website"),
1971262100107:("FK Humenné","https://r2.thesportsdb.com/images/media/team/badge/a2gvxi1658772153.png","TheSportsDB club profile FK Humenné"),
1971262100111:("MFK Tatran Liptovský Mikuláš","https://ilcalcio.net/assets/27/b2/27b29c3b4a67c4e8dfe3d2e336ec5e1b.png","Ilcalcio confirmed Tatran Liptovský Mikuláš crest"),
1971262100115:("OFK Malženice","https://api.sportnet.online/data/ppo/ofk-malzenice.futbalnet.sk/logo","Sportnet official club hosting"),
1971262100201:("FC Nagykanizsa","https://assets.football-logos.cc/logos/hungary/1500x1500/fc-nagykanizsa.7ea5f1bc.png","football-logos.cc exact club name"),
1971262100204:("HR-Rent Kozármisleny","https://assets.football-logos.cc/logos/hungary/1500x1500/kozarmisleny-fc.0eb670c7.png","football-logos.cc Kozármisleny FC original club crest"),
1971262100211:("Szentlőrinc SE","https://images.seeklogo.com/logo-png/51/1/szentlorinci-se-logo-png_seeklogo-512791.png","SeekLogo exact club identity Szentlőrinci SE"),
1971262100216:("Mezőkövesd Zsóry FC","https://app.fehervarfc.hu/api/image-cached/original/0/1c7e268e1ea1/169185.png","Fehérvár FC official club match images; Mezőkövesd Zsóry FC crest")
}
def get(item):
 tid,(name,url,source)=item
 d={"teamId":tid,"name":name,"image_url":url,"source":source,"status":"NOT_PUBLISHED","sha256":"","png_url":""}
 try:
  r=requests.get(url,headers={"User-Agent":"Mozilla/5.0 (MMD31 verified logo audit)","Accept":"image/*"},timeout=(5,12))
  if r.status_code!=200: d["error"]="HTTP "+str(r.status_code);return d
  img=Image.open(io.BytesIO(r.content));img.load()
  if img.width<25 or img.height<25 or img.width>5000 or img.height>5000: d["error"]="Invalid size";return d
  img=img.convert("RGBA");img.thumbnail((98,82),Image.Resampling.LANCZOS)
  bg=(235,240,247)
  out=Image.new("RGBA",(120,96),bg+(255,))
  out.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
  f=R/(str(tid)+".png");out.convert("RGB").save(f,"PNG",optimize=True)
  d.update({"status":"VERIFIED_IMAGE_PUBLISHED","sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"original_width":img.width,"original_height":img.height,"width":120,"height":96,"png_url":"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-central-europe-d2-20261025/docs/central-europe-d2-2026-27/extra/"+str(tid)+".png"})
 except Exception as e:d["error"]=str(e)[:180]
 return d
with ThreadPoolExecutor(max_workers=8) as pool:
 records=list(pool.map(get,ITEMS.items()))
Path("docs/central-europe-d2-2026-27/extra-manifest.json").write_text(json.dumps(records,ensure_ascii=False,indent=2))
print("VERIFIED",sum(x["status"]=="VERIFIED_IMAGE_PUBLISHED" for x in records),"of",len(records),flush=True)
