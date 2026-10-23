#!/usr/bin/env python3
"""Publish dated official Northern Irish league snapshots + authentic crests for CGE V13."""
import requests,bs4,re,json,io,hashlib,unicodedata,concurrent.futures
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw
from urllib.parse import urljoin
root=Path("docs/nir-clubs-2026-27/v13-extension");root.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; MMD31 dataset audit)"})
def get(url):
    r=s.get(url,timeout=24);r.raise_for_status();return r
def key(x):return re.sub(r"[^a-z0-9]","",unicodedata.normalize("NFKD",x).encode("ascii","ignore").decode().lower().replace("&","and"))
groups=[]
nafl=get("https://www.thenafl.co.uk/data/tables.json").json()
nafl_clubs=get("https://www.thenafl.co.uk/data/clubs-dev.json").json()
by_club={}
for c in nafl_clubs:
    if c.get("name"):by_club[key(c["name"])]=c
for group,section in nafl.items():
    if group=="NCL U21 Development Division":continue
    members=[]
    for a in section.get("table",[]):
        if not a.get("team"):continue
        name=a["team"]
        club=by_club.get(key(name),{})
        badge=a.get("badge") or club.get("badge")
        if not badge:badge=""
        members.append({"name":name,"badge":("https://www.thenafl.co.uk/images/badges/"+badge if badge else ""),
                        "p":a.get("pld"),"w":a.get("w"),"d":a.get("d"),"l":a.get("l"),
                        "gf":a.get("gf"),"ga":a.get("ga"),"pts":a.get("pts"),
                        "rank":a.get("pos")})
    groups.append({"code":"NAFL_"+group.replace(" ","_"),"name":"Northern Amateur Football League "+group,
                   "source":"https://www.thenafl.co.uk/data/tables.json","members":members})
urls={
    "MUFL_INTERMEDIATE_A":"intermediatea/",
    "MUFL_INTERMEDIATE_B":"intermediateb/",
    "MUFL_DIV1":"division1/",
    "MUFL_DIV2":"division2/",
    "MUFL_DIV3":"division3/",
    "MUFL_RES_CH":"reservechampionship/",
    "MUFL_RES1":"reserve1/",
    "MUFL_RES2":"reserve2/",
    "MUFL_RES3":"reserve3/"
}
for code,url in urls.items():
    source="https://midulsterfootballleague.co.uk/"+url
    g={"code":code,"name":("Mid Ulster "+code.split("MUFL_")[-1]),"source":source,"members":[],"errors":[]}
    try:
        html=get(source).text
        soup=bs4.BeautifulSoup(html,"html.parser")
        tables=soup.select("table")
        for table in tables:
            if "team" not in table.get_text(" ",strip=True).lower()[:600] or "pts" not in table.get_text(" ",strip=True).lower()[:1000]:continue
            if len(table.select("tbody tr"))<4:continue
            for tr in table.select("tbody tr"):
                cells=tr.find_all(["th","td"],recursive=False)
                raw=[c.get_text(" ",strip=True) for c in cells]
                if len(raw)<7:continue
                name=raw[1] if raw[0].strip().isdigit() else raw[0]
                if not name or name.lower().startswith("team"):continue
                ints=[int(x.replace("+","")) if re.fullmatch(r"[+-]?\d+",x.strip()) else None for x in raw]
                # SportsPress columns often: rank,team,P,W,D,L,GF,GA,GD,Pts
                p,w,d,l,gf,ga,pts=(ints[2],ints[3],ints[4],ints[5],ints[6],ints[7],ints[9]) if len(ints)>=10 else (None,)*7
                im=tr.select_one("img")
                badge=urljoin(source,im.get("data-src") or im.get("src")) if im else ""
                g["members"].append({"name":name,"badge":badge,"p":p,"w":w,"d":d,"l":l,"gf":gf,"ga":ga,"pts":pts,"rank":ints[0]})
            if g["members"]:break
        if not g["members"]:g["errors"].append("No standings table matched")
    except Exception as e:g["errors"].append(str(e)[:180])
    groups.append(g)
# Stable ID plan for new teams; don't create duplicate when club already in V4.
original_keys={
"Comber Rec":"Comber Recreation","Derriaghy CC":"Derriaghy Cricket Club",
"Dunmurry YM":"Dunmurry Young Men","Larne Tech OB":"Larne Technical Old Boys",
"18th Newtownabbey OB":"18th Newtownabbey Old Boys",
"1st Bangor":"1st Bangor Old Boys","Kilmore Rec":"Kilmore Recreation",
"Dunmurry Rec":"Dunmurry Recreation","Rosario YC":"Rosario Youth",
}
for g in groups:
    for m in g["members"]:m["mapped_name"]=original_keys.get(m["name"],m["name"])
# Mark extensions and create their own logo
existing=[
"Ballymena United|Bangor|Carrick Rangers|Cliftonville|Coleraine|Crusaders|Dungannon Swifts|Glentoran|Limavady United|Larne|Linfield|Portadown",
"Glenavon|Moyola Park|Strabane Athletic|Rathfriland Rangers|Newry City|Annagh United|Loughgall|Harland & Wolff Welders|Institute|Queen's University|Newington|Ards|Warrenpoint Town|Armagh City|Dundela|Ballinamallard United",
"Portstewart|St James Swifts|Dergview|Ballyclare Comrades|Ballymacash Rangers|Lisburn Distillery|Dollingstown|Rosario Youth|Oxford Sunnyside|Knockbreda|Coagh United|Banbridge Town",
"Comber Recreation|Dunmurry Young Men|Derriaghy Cricket Club|Lisburn Rangers|Ards Rangers|Dromara Village|Crumlin Star|Holywood|Islandmagee|Immaculata|Drumaness Mills|Abbey Villa|East Belfast|Mossley",
"Banbridge Rangers|Bourneview Mill|Crewe United|FC Mindwell|Fivemiletown United|Laurelvale|Lower Maze|Lurgan Town|Moneyslane|Newmills|Richhill AFC|Tandragee Rovers|Valley Rangers|Windmill Stars",
"Newtowne|Desertmartin|Heights FC|Wellington Recreation|Newbuildings United|Donegal Celtic|Ballymoney United|Belfast Celtic|Glebe Rangers",
"Willowbank|St Oliver Plunkett|Sirocco Works|Greenisland|Larne Technical Old Boys|1st Bangor Old Boys|Albert Foundry|Shankill United|Kilmore Recreation|Finaghy|Aquinas|18th Newtownabbey Old Boys|Crumlin United|Dunmurry Recreation",
"AFC Craigavon|Ambassadors|Bessbrook United|Camlough Rovers|Craigavon City|Dromore Amateurs|Dungannon Tigers|Hanover|Lurgan Celtic|Markethill Swifts|Portadown BBOB|PSNI|Seagoe|Seapatrick|St Mary’s YC|Tullyvallen",
"Dundonald|Rosemount Rec|St Matthews|Ballynahinch Olympic|Bryansburn Rangers|Killyleagh YC|Shamrock|Woodvale|Newcastle Town|Downshire YM|St Lukes|St Marys (Newtownabbey)|Colin Valley|Bangor Amateurs",
"Malachians|Tullycarnet|Castlewellan Town|Saintfield United|Shorts|Suffolk|Bloomfield|Portaferry Rovers|Grove United|Portavogie Rangers|Ballynahinch United|Orangefield OB|Ballywalter Rec",
"Cookstown Youth|Trojans YCG|Maiden City|Chimney Corner|Brantwood|Killymoon Rangers|Inspired Talents|Tobermore United"]
existing={key(n) for block in existing for n in block.split("|")}
existing.update([key("Harland & Wolff Welders"),key("Harland and Wolff Welders"),key("St Marys YC")])
exclude={"NCL Premier","Premier Division","Division 1A","Division 1B","Division 1C","Intermediate A","Intermediate B"}
new_groups=[g for g in groups if g["code"].startswith("NAFL_") and g["code"][5:].replace("_"," ") not in exclude or g["code"] in ("MUFL_DIV1","MUFL_DIV2","MUFL_DIV3","MUFL_RES_CH","MUFL_RES1","MUFL_RES2","MUFL_RES3")]
already=set(existing);jobs=[]
for g in new_groups:
    for m in g["members"]:
        k=key(m["mapped_name"])
        if k in already:continue
        already.add(k);m["created_group"]=g["code"];jobs.append(m)
for i,m in enumerate(jobs,1900231300143):m["newId"]=i
def render(job):
    out={"id":job["newId"],"name":job["mapped_name"],"group":job["created_group"],"source":job["badge"],"status":"missing"}
    try:
        if not job["badge"]:raise ValueError("No official crest")
        raw=get(job["badge"]).content
        if not 150<len(raw)<5000000:raise ValueError("Empty/oversized asset")
        im=Image.open(io.BytesIO(raw));im.load();im=im.convert("RGBA")
        if im.width<18 or im.height<18:raise ValueError("tiny crest")
        bbox=im.getchannel("A").getbbox()
        if not bbox:raise ValueError("transparent")
        im=im.crop(bbox)
        small=im.copy();small.thumbnail((85,85))
        counts=Counter()
        for r,g,b,a in small.getdata():
            if a>120 and max(r,g,b)-min(r,g,b)>36:counts[(r//32,g//32,b//32)]+=a
        color=max(counts,key=counts.get) if counts else (2,4,6)
        bg=tuple(min(255,int((v*32+16)*.68+255*.32)) for v in color)
        canvas=Image.new("RGBA",(120,96),bg+(255,))
        im.thumbnail((102,82),Image.Resampling.LANCZOS)
        canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
        path=root/(str(job["newId"])+".png");canvas.convert("RGB").save(path,optimize=True)
        with Image.open(path) as check:assert check.size==(120,96) and check.format=="PNG"
        out.update({"status":"created","sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bg":bg})
    except Exception as e:out["error"]=str(e)[:160]
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=18) as ex:images=list(ex.map(render,jobs))
final={"sourceDate":"2026-10-23","officialNAFL":"https://www.thenafl.co.uk/data/tables.json",
"newGroups":len(new_groups),"newParticipants":len(jobs),"newPNGs":sum(v["status"]=="created" for v in images),
"groups":groups,"images":images}
(root/"official_snapshot.json").write_text(json.dumps(final,ensure_ascii=False,indent=2))
print("RESULTS",len(groups),"groups",len(jobs),"new club entries",final["newPNGs"],"new PNGs")
for g in groups: print("GROUP",g["code"],len(g["members"]),g.get("errors"))
