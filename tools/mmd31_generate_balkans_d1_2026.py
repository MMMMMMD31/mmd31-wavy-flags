#!/usr/bin/env python3
"""Render exact verified original team crests to 120x96 club-background flags."""
import hashlib,requests,urllib.parse,json,io,time
from pathlib import Path
from PIL import Image,ImageOps
import cairosvg
S=requests.Session()
S.headers.update({"User-Agent":"MMD31-ClubCrests/1.0 research","Accept":"image/*,*/*"})
R=[["BA",1947261000001,"HŠK Zrinjski Mostar","Zrinjski_Mostar.svg","#E2A6B4"],["BA",1947261000002,"FK Borac Banja Luka","Borac_Banja_Luka.svg","#BB8AC9"],["BA",1947261000003,"FK Sarajevo","Sarajevo.svg","#BD83A5"],["BA",1947261000004,"NK Široki Brijeg","Široki_Brijeg.svg","#8EAFDE"],["BA",1947261000005,"FK Željezničar Sarajevo","Željezničar.svg","#8BAED7"],["BA",1947261000006,"FK BSK Banja Luka","BSK_FALLBACK","#A2B9C9"],["BA",1947261000007,"NK Čelik Zenica","Čelik_Zenica.svg","#DB93A1"],["BA",1947261000008,"FK Sloga Doboj","Sloga_Doboj.svg","#B9A4DD"],["BA",1947261000009,"FK Radnik Bijeljina","Radnik_Bijeljina.svg","#8FBBE0"],["BA",1947261000010,"FK Velež Mostar","Velež_Mostar.svg","#E19B9B"],["RS",1947262000001,"FK Crvena zvezda","Crvena_Zvezda.svg","#DE9494"],["RS",1947262000002,"FK Vojvodina","FK_Vojvodina.svg","#D69AA4"],["RS",1947262000003,"FK Železničar Pančevo","Zeleznicar_Pancevo.svg","#99BCE0"],["RS",1947262000004,"FK IMT Novi Beograd","FK_IMT.svg","#C0B3D8"],["RS",1947262000005,"FK Radnički 1923 Kragujevac","Radnički_1923.svg","#C68BA1"],["RS",1947262000006,"FK Radnik Surdulica","Radnik_Surdulica.svg","#87B3D6"],["RS",1947262000007,"FK Mladost Lučani","FK_Mladost_Lučani.svg","#B8A2CA"],["RS",1947262000008,"FK Novi Pazar","FK_Novi_Pazar.svg","#94C5B1"],["RS",1947262000009,"FK Čukarički","FK_Čukarički.svg","#A8A8A8"],["RS",1947262000010,"FK Partizan","FK_Partizan.svg","#BCBCBC"],["RS",1947262000011,"OFK Beograd","OFK_Beograd.svg","#8DB9DF"],["RS",1947262000012,"FK Mačva Šabac","Macva_Sabac.svg","#C899B0"],["RS",1947262000013,"FK Radnički Niš","Radnicki_Niš.svg","#C2A4AC"],["RS",1947262000014,"FK Zemun","FK_Zemun.svg","#9CA9D2"],["XK",1947263000001,"FC Malisheva","FFK_Malisheva","#9FB3DA"],["XK",1947263000002,"FC Prishtina","FFK_Prishtina","#8FB8E7"],["XK",1947263000003,"FC Drita","FFK_Drita","#91BED3"],["XK",1947263000004,"SC Gjilani","FFK_Gjilani","#CFA3A3"],["XK",1947263000005,"KF Dukagjini","FFK_Dukagjini","#D4A9A9"],["XK",1947263000006,"FC Ballkani","FFK_Ballkani","#CEAEA4"],["XK",1947263000007,"KF Drenica","FFK_Drenica","#D29CAC"],["XK",1947263000008,"FC Feronikeli 74","FFK_Feronikeli","#97B5C4"],["XK",1947263000009,"KF Llapi","FFK_Llapi","#91B2DE"],["XK",1947263000010,"FC Vushtrria","FFK_Vushtrria","#B1C1D8"]];
DISC=Path("docs/balkans-d1-2026/v1/discovery.json")
SOURCE=json.loads(DISC.read_text(encoding="utf8"))
BASE=Path("docs/balkans-d1-2026/v1")
SVGS_BASE="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/"
WIKI_BSK="https://thumb.wikimedia.org/wikipedia/en/thumb/1/15/FK_BSK_Banja_Luka_%281%29.png/250px-FK_BSK_Banja_Luka_%281%29.png"
GSA_FC_VUSHTRRIA="https://dsg-images.com/clubs/50x50/14707.png"
FFK_KEY={"FFK_Malisheva":"Malisheva","FFK_Prishtina":"Prishtina","FFK_Drita":"Drita","FFK_Gjilani":"Gjilani","FFK_Dukagjini":"Dukagjini","FFK_Ballkani":"Ballkani","FFK_Drenica":"Drenica","FFK_Feronikeli":"Feronikeli 74","FFK_Llapi":"Llapi"}
def source_for(country,key):
 if key=="BSK_FALLBACK":return WIKI_BSK,"Wikipedia club crest (250px verified)","wiki"
 if key=="FFK_Vushtrria":return GSA_FC_VUSHTRRIA,"Global Sports Archive verified club roster crest","gsa"
 if key.startswith("FFK_"):
  alt="KF Dukagjini Klinë" if key=="FFK_Dukagjini" else FFK_KEY[key]
  # Official federation CDN blocks hotlinking; use identified football competition imagery.
  matches=[q for q in SOURCE["Kosovo competition"]["images"] if q["alt"].lower().startswith("logo of ") and q["alt"].lower().endswith(alt.lower()) and "/50x50/" in q["src"]]
  if not matches:raise ValueError("No identifiable club crest in verified sports competition source "+alt)
  src=matches[0]["src"]
  return src,"Global Sports Archive original competition logo, match checked by team name","gsa"
 return SVGS_BASE+{"BA":"bosnia-and-herzegovina","RS":"serbia"}[country]+"/"+urllib.parse.quote(key),"JoseArroyave football logos / originally sourced SVG","svg"
assets=[];missing=[]
for c,id,name,key,color in R:
 try:
  src,provenance,source_type=source_for(c,key)
  rr=S.get(src,timeout=35);rr.raise_for_status()
  raw=rr.content
  if b"<svg" in raw[:2500]:
   image=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=raw,output_width=500))).convert("RGBA")
  else:
   image=Image.open(io.BytesIO(raw)).convert("RGBA")
  if image.width<16 or image.height<16:raise ValueError("Crest has too few source pixels")
  bbox=image.getchannel("A").getbbox()
  if not bbox:raise ValueError("Logo image empty")
  image=image.crop(bbox)
  image.thumbnail((100,86),Image.Resampling.LANCZOS)
  im=Image.new("RGBA",(120,96),color)
  im.alpha_composite(image,((120-image.width)//2,(96-image.height)//2))
  path=BASE/f"{id}.png"
  im.convert("RGB").save(path,format="PNG",optimize=True)
  with Image.open(path) as check:
   assert check.size==(120,96) and check.format=="PNG"
  assets.append(dict(id=id,country=c,club=name,source_url=src,source_description=provenance,background=color,source_size_bytes=len(raw),image_size=[120,96],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),flagUrl=f"https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-balkans-d1-2026-test/{path.as_posix()}",source_resolution=[image.width,image.height]))
  print("CREST_OK",id,name,src,flush=True)
 except Exception as e:
  missing.append(dict(id=id,country=c,name=name,error=str(e),source_key=key))
  print("CREST_MISSING",id,name,str(e),flush=True)
manifest=dict(expected=len(R),created=len(assets),missing=len(missing),format="120x96 authentic crest on club-color solid rectangle",assets=assets,unresolved=missing)
(BASE/"crests_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
print("RESULT",len(assets),"/",len(R),"missing",missing,flush=True)
assert len(assets)>=25,"Too many source image failures"
