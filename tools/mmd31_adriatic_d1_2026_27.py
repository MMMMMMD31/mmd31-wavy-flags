#!/usr/bin/env python3
"""MMD31 genuine crest compositor; never synthesizes club logos."""
import io,json,hashlib,re,urllib.parse,os,requests
from pathlib import Path
from PIL import Image
import cairosvg
from bs4 import BeautifulSoup
BASE=Path("docs/adriatic-d1-2026-27/v1");BASE.mkdir(parents=True,exist_ok=True)
COUNTRIES=[
("slovenia",[
("NK Celje","Celje.svg","#77B8CF","nk-celje"),
("FC Koper","Koper.svg","#93C6ED","fc-koper"),
("NK Bravo","Bravo.svg","#E5C14A","nk-bravo"),
("NK Olimpija Ljubljana","Olimpija.svg","#8DCAA2","nk-olimpija-ljubljana"),
("NK Maribor","Maribor.svg","#C9ABD9","nk-maribor"),
("NK Radomlje","Radomlje.svg","#E4CE5E","nk-radomlje"),
("NK Aluminij Kidričevo","Aluminij.svg","#E59B9B","nk-aluminij"),
("NŠ Mura","Mura.svg","#D3D3D3","ns-mura"),
("NK Brinje Grosuplje","NK_Brinje_Grosuplje.svg","#E6D49B","nk-brinje-grosuplje"),
("NK Nafta 1903","Nafta_1903.svg","#AACEEE","nk-nafta-1903")]),
("croatia",[
("GNK Dinamo Zagreb","GNK_Dinamo_Zagreb.svg","#9DC1EC","gnk-dinamo-zagreb"),
("HNK Gorica","HNK_Gorica.svg","#D4A3A3","hnk-gorica"),
("HNK Hajduk Split","Hajduk_Split.svg","#C1D5E6","hnk-hajduk-split"),
("NK Istra 1961","Istra_1961.svg","#C5E2AF","nk-istra-1961"),
("NK Lokomotiva Zagreb","Lokomotiva_Zagreb.svg","#ABD8E8","lokomotiva-zagreb"),
("NK Osijek","Osijek.svg","#B0CCEE","nk-osijek"),
("HNK Rijeka","Rijeka.svg","#C7D9EF","hnk-rijeka"),
("NK Rudeš","Rudeš.svg","#ACCCEE","rudes"),
("NK Slaven Belupo","Slaven_Belupo.svg","#C4C4E8","slaven-belupo-koprivnica"),
("NK Varaždin","Varaždin.svg","#BDD8FA","nk-varazdin")]),
("montenegro",[
("FK Budućnost Podgorica",None,"#AACDE8","buducnost-podgorica"),
("FK Sutjeska Nikšić",None,"#AED3EF","sutjeska"),
("FK Dečić Tuzi",None,"#B8C7E6","decic"),
("OFK Petrovac",None,"#CFC0EA","petrovac"),
("FK Bokelj Kotor",None,"#BBD3EB","bokelj"),
("FK Mornar Bar",None,"#B0D6D2","mornar"),
("FK Arsenal Tivat",None,"#A6C8E6","arsenal-tivat"),
("FK Jezero Plav",None,"#B2C5EE","jezero"),
("FK Otrant-Olympic",None,"#BFD1E7","otrant-olympic"),
("OFK Mladost Donja Gorica",None,"#E3C3C3","mladost-donja-gorica")]),
("albania",[
("KF Egnatia","Egnatia.svg","#A9D3B5","kf-egnatia"),
("AF Elbasani","AF_Elbasani.svg","#B7D4FA","af-elbasani"),
("KF Vllaznia","Vllaznia.svg","#ACBDD9","kf-vllaznia"),
("FC Dinamo City","Dinamo_City.svg","#B1C3E6","fc-dinamo-city"),
("FK Partizani","Partizani.svg","#DEA6A6","fk-partizani"),
("KF Tirana","Tirana.svg","#A3CAED","kf-tirana"),
("FK Vora","Vora.svg","#B4C7EB","vora-fk"),
("KF Teuta","Teuta.svg","#A2C7E2","kf-teuta"),
("KF Skënderbeu","Skënderbeu.svg","#E1B7B7","skenderbeu"),
("KF Laçi","Laç.svg","#D0D0D0","kf-laci")])]
SESSION=requests.Session();SESSION.headers["User-Agent"]="MMD31-Football-Research/1.0"
def get(url):
 try:
  r=SESSION.get(url,timeout=16);r.raise_for_status()
  return r.content,r.headers.get("content-type","")
 except Exception: return None,None
def source_image(country,name,gh_name,slug):
 urls=[]
 if gh_name:
  urls.append("https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/"+country+"/"+urllib.parse.quote(gh_name))
 urls.append(f"https://assets.footylogos.com/logos/{slug}/{slug}-logo-footylogos.svg")
 # Montenegro and any missing club: source site lists individually.
 urls.append("https://football-logos.cc/"+country+"/"+slug+"/")
 if country=="montenegro":
  urls.append(f"https://www.footylogos.com/logos/{slug}")
 for url in urls:
  dat,ctype=get(url)
  if not dat:continue
  if b"<svg" in dat[:1500]:
   try:return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=dat,output_width=400))),url
   except Exception:continue
  if dat[:8]==b"\x89PNG\r\n\x1a\n" or dat[:2]==b"\xff\xd8":
   try:return Image.open(io.BytesIO(dat)),url
   except Exception:continue
  if "html" in (ctype or "") or b"<html" in dat[:200].lower():
   try:
    soup=BeautifulSoup(dat,"html.parser")
    candidates=[]
    for tag in soup.select("img"):
     alt=tag.get("alt","").lower()
     src=tag.get("src") or tag.get("data-src")
     if src and ("logo" in alt or "crest" in alt or "badge" in alt):candidates.append(urllib.parse.urljoin(url,src))
    for tag in soup.select('meta[property="og:image"]'):
     if tag.get("content"):candidates.append(urllib.parse.urljoin(url,tag["content"]))
    seen=set()
    for imgurl in candidates:
     if imgurl in seen:continue
     seen.add(imgurl)
     binary,typ=get(imgurl)
     if binary:
      try:
       if b"<svg" in binary[:1200]:return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=binary,output_width=400))),imgurl
       im=Image.open(io.BytesIO(binary))
       if im.width>=64 and im.height>=64:return im,imgurl
      except Exception:pass
   except Exception:pass
 return None,None
def render(im,col):
 im=im.convert("RGBA")
 im.thumbnail((101,82),Image.Resampling.LANCZOS)
 dst=Image.new("RGBA",(120,96),col)
 dst.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
 return dst.convert("RGB")
records=[]
for ci,(country,teams) in enumerate(COUNTRIES):
 for ti,(name,gh,col,slug) in enumerate(teams):
  tid=1942600200000+ci*100+ti
  im,source=source_image(country,name,gh,slug)
  rec={"id":tid,"country":country,"name":name,"background":col,"source":source,"sourceCandidate":gh or slug}
  if im:
   out=BASE/(str(tid)+".png");render(im,col).save(out,optimize=True)
   rec["status"]="PNG_120x96_PUBLISHED_IN_BRANCH";rec["sha256"]=hashlib.sha256(out.read_bytes()).hexdigest();rec["width"]=120;rec["height"]=96
  else:rec["status"]="CREST_SOURCE_UNVERIFIED"
  records.append(rec)
  print(country,ti,name,rec["status"],source,flush=True)
(BASE/"manifest.json").write_text(json.dumps({"season":"2026-27","catalog":"MMD31 first division genuine crest candidates","total":len(records),"published":sum(x["status"].startswith("PNG") for x in records),"assets":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PUBLISHED",sum(x["status"].startswith("PNG") for x in records),"/",len(records),flush=True)
