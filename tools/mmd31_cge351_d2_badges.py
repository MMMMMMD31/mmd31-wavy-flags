#!/usr/bin/env python3
"""Generate sourced official-style 120x96 club crest cards for CGE 3.5.1 D2.
SVG files from https://github.com/JoseArroyave/football-logos
No crests are invented. HJK Klubi 04 and SJK Akatemia use their parent club crest.
"""
import io, json, os, hashlib, time
from pathlib import Path
from urllib.parse import quote
import requests, cairosvg
from PIL import Image
ENTRIES = [["DK",1910262602001,"AaB","AaB.svg","#F3EAEB"],["DK",1910262602002,"AB Gladsaxe","AB.svg","#E5F2E8"],["DK",1910262602003,"Aarhus Fremad","Aarhus_Fremad.svg","#FFF1C5"],["DK",1910262602004,"Esbjerg fB","Esbjerg.svg","#E7EFF9"],["DK",1910262602005,"FC Fredericia","FC_Fredericia.svg","#FFF0EB"],["DK",1910262602006,"HB Køge","Køge.svg","#E7F1F8"],["DK",1910262602007,"Hillerød Fodbold","Hillerød_Fodbold.svg","#E5F1FF"],["DK",1910262602008,"Hobro IK","Hobro_IK.svg","#FFF4C8"],["DK",1910262602009,"Hvidovre IF","Hvidovre_IF.svg","#F9E9EB"],["DK",1910262602010,"Kolding IF","Kolding_IF.svg","#E5ECF9"],["DK",1910262602011,"Vejle Boldklub","VB.svg","#F6E9EA"],["DK",1910262602012,"Vendsyssel FF","Vendsyssel.svg","#ECEEF0"],["SE",1911262602001,"IK Oddevold","IK_Oddevold.svg","#E6F0F8"],["SE",1911262602002,"Ljungskile SK","Ljungskile_SK.svg","#E8F2E6"],["SE",1911262602003,"IK Brage","Brage.svg","#E4F0E5"],["SE",1911262602004,"Sandvikens IF","Sandvikens_IF.svg","#FAEBE9"],["SE",1911262602005,"Falkenbergs FF","Falkenberg.svg","#FFF4D0"],["SE",1911262602006,"Varbergs BoIS","Varbergs_BoIS_FC.svg","#E9F1E7"],["SE",1911262602007,"Östersunds FK","Östersund.svg","#F5ECEE"],["SE",1911262602008,"GIF Sundsvall","GIF_Sundsvall.svg","#EBEFF9"],["SE",1911262602009,"Helsingborgs IF","Helsingborg.svg","#F7EAEB"],["SE",1911262602010,"Landskrona BoIS","Landskrona_BoIS.svg","#EFF0F0"],["SE",1911262602011,"IFK Värnamo","Värnamo.svg","#E5F1F9"],["SE",1911262602012,"Östers IF","Östers_IF.svg","#F5E9EC"],["SE",1911262602013,"Nordic United FC","Nordic_United_FC.svg","#F3E7F2"],["SE",1911262602014,"Norrby IF","Norrby_IF.svg","#E7EDF7"],["SE",1911262602015,"Örebro SK","Örebro.svg","#F0F0F0"],["SE",1911262602016,"IFK Norrköping","Norrköping.svg","#E4EEF8"],["FI",1912262602001,"EIF","Ekenäs_IF.svg","#E9F3E6"],["FI",1912262602002,"FC Haka","FC_Haka_Valkeakoski.svg","#F1F1F1"],["FI",1912262602003,"JIPPO","JIPPO.svg","#F7EAEA"],["FI",1912262602004,"JäPS","JäPS.svg","#E7F0FB"],["FI",1912262602005,"HJK Klubi 04","HJK_Helsinki.svg","#E8EFFA"],["FI",1912262602006,"FC KTP","Kotkan_Työväen_Palloilijat.svg","#E7F1E8"],["FI",1912262602007,"KäPa","KäPa.svg","#F0EAF5"],["FI",1912262602008,"Mikkelin Palloilijat","MP.svg","#E6EFF8"],["FI",1912262602009,"PK-35","PK-35.svg","#F6E6E7"],["FI",1912262602010,"SJK Akatemia","SJK_Seinäjoki.svg","#F5EEDB"]]
TARGET = Path("docs/cge351-d2-2026-27/v1/clubs")
TARGET.mkdir(parents=True, exist_ok=True)
session=requests.Session()
session.headers.update({"User-Agent":"MMD31/1.0 (noncommercial football simulator project)"})
manifest=[]
for country, team_id, name, file_name, bg in ENTRIES:
    directory={"DK":"denmark","SE":"sweden","FI":"finland"}[country]
    raw_url="https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/"+directory+"/"+quote(file_name)
    resp=None
    for attempt in range(4):
        try:
            resp=session.get(raw_url, timeout=22)
            resp.raise_for_status()
            break
        except requests.RequestException:
            if attempt==3: raise
            time.sleep(attempt+1)
    data=resp.content
    assert b"<svg" in data[:500], (name,raw_url,resp.headers.get("Content-Type"))
    png=cairosvg.svg2png(bytestring=data, output_width=480)
    crest=Image.open(io.BytesIO(png)).convert("RGBA")
    bbox=crest.getbbox()
    if not bbox: raise ValueError("Empty crest for "+name)
    crest=crest.crop(bbox)
    crest.thumbnail((102,82), Image.Resampling.LANCZOS)
    output=Image.new("RGBA",(120,96),bg)
    output.alpha_composite(crest,((120-crest.width)//2,(96-crest.height)//2))
    path=TARGET/(str(team_id)+".png")
    output.convert("RGB").save(path,"PNG",optimize=True)
    stored=path.read_bytes()
    test=Image.open(io.BytesIO(stored))
    assert test.size==(120,96) and test.format=="PNG"
    manifest.append({"country":country,"clubId":team_id,"club":name,
       "sourceUrl":raw_url,"sourceKind":"third_party_collection_of_real_club_crests",
       "sourceSvgSha256":hashlib.sha256(data).hexdigest(),"pngSha256":hashlib.sha256(stored).hexdigest(),
       "backgroundColor":bg,"width":120,"height":96,"filename":str(path),
       "reserveParentCrest":name in ["HJK Klubi 04","SJK Akatemia"],
       "validation":"SOURCE_FETCHED_PNG_120X96_CHECKED; identity not compared with live club official website"})
    print(str(team_id), name, len(stored), flush=True)
assert len(manifest)==38
doc={"task":"CGE 3.5.1 D2 38 authentic crests", "sourceCollection":"https://github.com/JoseArroyave/football-logos",
     "count":len(manifest),"clubCrests":manifest,
     "caveat":"Collection sources should be reconfirmed against the clubs current identity; imagery is copyrighted by its owners."}
(TARGET.parent/"manifest.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("GENERATED 38/38",flush=True)
