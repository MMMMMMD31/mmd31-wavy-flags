#!/usr/bin/env python3
"""MMD31: publish exactly the 38 remaining 2026-27 Italian crests, retaining all previous badges."""
import json,requests,io,hashlib,time,concurrent.futures
from PIL import Image
from collections import Counter
from pathlib import Path
SOURCES=json.loads(r'''[{"id":1793400200100,"name":"Alessandria","url":"https://img.datasport.it/img/logos/squadre/alessandria.png","sha256":"a94821f932786fc077a779dca23d6a08a570c855a44ce2edfcb5c41f18c84079","source_size":[200,200]},{"id":1793400200103,"name":"Borgosesia","url":"https://www.borgosesiacalcio.com/wp-content/uploads/logo-borgosesiacalcio-colore_fondo-trasparente.png","sha256":"7dc9390d2d04b280f9c8936181db3eee605ac2cd7fe46a10674930088e9f16b6","source_size":[731,731]},{"id":1793400200108,"name":"Lascaris","url":"https://img.datasport.it/img/logos/squadre/lascaris.png","sha256":"19cea81737235c55ae9856d82b1f998a1d9c6f7e04e7922a50ffbdea94f2c3b5","source_size":[200,200]},{"id":1793400200112,"name":"Fezzanese","url":"https://img.datasport.it/img/logos/squadre/fezzanese.png","sha256":"291bd15a09ed3737225a6ae6e8d883dcf9b8946bf43324190b54425d684d9341","source_size":[200,200]},{"id":1793400200115,"name":"Millesimo","url":"https://img.datasport.it/img/logos/squadre/millesimo.png","sha256":"9d711d23cc68341f89fc148d2851ecd1d75073475b6cb94bd93802b526811351","source_size":[200,200]},{"id":1793400200123,"name":"Pavonese","url":"https://img.datasport.it/img/logos/squadre/pavonese-cigolese.png","sha256":"194968eff731d3def65c229ce7808a7fac36f6d1e922be826967d90b25106d04","source_size":[200,200]},{"id":1793400200127,"name":"Tritium","url":"https://img.datasport.it/img/logos/squadre/tritium-calcio-1908.png","sha256":"58c6fc2f1733807c13c05a742725e2e4c4f46e7a18d41e4ec0ef12ab409c77d8","source_size":[200,200]},{"id":1793400200133,"name":"Fiorenzuola","url":"https://img.datasport.it/img/logos/squadre/fiorenzuola.png","sha256":"1baf17bd7a68529b6078a11974d9f740a37301742f3c4f269526dd7f943cecc9","source_size":[200,200]},{"id":1793400200134,"name":"Nibbiano e Valtidone","url":"https://img.datasport.it/img/logos/squadre/nibbiano-e-valtidone.png","sha256":"92980ae4d218d1fa46ae6eeb6285d8767ac7e7f5808a4c69a72aabcae84e3bec","source_size":[200,200]},{"id":1793400200138,"name":"LME","url":"https://img.datasport.it/img/logos/squadre/lme.png","sha256":"c7a77a89ddc7b27ee3dbf210d8c0e94f2886d664242b6f8806c1b7eb785d49f8","source_size":[200,200]},{"id":1793400200141,"name":"Virtus Bolzano","url":"https://img.datasport.it/img/logos/squadre/virtus-bolzano.png","sha256":"1687eccf50b2a51ed776d0f2a10f701e1798c69cee286ef1c8da51b4e3361c52","source_size":[200,200]},{"id":1793400200151,"name":"Sandonà","url":"https://img.datasport.it/img/logos/squadre/sandona-1922.png","sha256":"1c466e5fd4391350abd1242ddefddf91795bf33ff4ae5f656b71c6d2816afbee","source_size":[200,200]},{"id":1793400200152,"name":"Schio","url":"https://img.datasport.it/img/logos/squadre/calcio-schio.png","sha256":"7877900df141dc6ff646b8a482c09fc1bdaebfa38add6e43eb892ea3846df729","source_size":[200,200]},{"id":1793400200160,"name":"Arconatese","url":"https://img.datasport.it/img/logos/squadre/arconatese.png","sha256":"4b11a65aa66d6e1ae33f2230df26e9f9134c5565d2dd96a9bb23745c5ffe1412","source_size":[200,200]},{"id":1793400200169,"name":"Solbiatese","url":"https://img.datasport.it/img/logos/squadre/solbiatese.png","sha256":"f41ddc6fafef0ef4876acbdee97924e441925c72f4c4df2a475d547e1f573b21","source_size":[200,200]},{"id":1793400200176,"name":"Grassina","url":"https://img.datasport.it/img/logos/squadre/grassina.png","sha256":"8055cb07011c221f5f5a80c099744ca16579010de99e76c3bc8ee22c3627d4c4","source_size":[200,200]},{"id":1793400200179,"name":"Rondinella Marzocco","url":"https://img.datasport.it/img/logos/squadre/rondinella-marzocco.png","sha256":"8355c00665e0c3e3938396bdbc57907ab8005e32a45bb6312d74c30c7d5a848f","source_size":[200,200]},{"id":1793400200187,"name":"Mezzolara","url":"https://img.datasport.it/img/logos/squadre/mezzolara.png","sha256":"fbba75358e51fb1909c0af312c577f93958a096d82c151e80b4b39901f750a3c","source_size":[200,200]},{"id":1793400200194,"name":"Montecchio Gallo","url":"https://img.datasport.it/img/logos/squadre/k-sport-montecchio-gallo.png","sha256":"b5b71117214d0d3db492737b15121ccd2a099a75b826aadb81ada7a3bc51b038","source_size":[200,200]},{"id":1793400200197,"name":"Città di Lanciano","url":"https://img.datasport.it/img/logos/squadre/lanciano-1920.png","sha256":"f9fee4ee9d9e3e9cb9c5ccaa776890f710a0a69ea3f1cb4f79592a5efd0c6337","source_size":[200,200]},{"id":1793400200201,"name":"Santegidiese","url":"https://img.datasport.it/img/logos/squadre/nuova-santegidiese-1948.png","sha256":"14417b0b36ca9b5a9a8cb6ee213dfe54448fd36475bdc9c329add84864625931","source_size":[200,200]},{"id":1793400200203,"name":"Angelana","url":"https://img.datasport.it/img/logos/squadre/angelana-1930.png","sha256":"d7e2af0ccfe2ccd0f314c4e7b09d217234531f36ff84ed87a6e29eb5164f1ea5","source_size":[200,200]},{"id":1793400200205,"name":"Pietralunghese","url":"https://img.datasport.it/img/logos/squadre/pol-pietralunghese.png","sha256":"8414d17959ae51ad3e8eda7ade678b42d66142895ad9389f36f1b31ce41c1e64","source_size":[200,200]},{"id":1793400200211,"name":"Ossese","url":"https://img.datasport.it/img/logos/squadre/polisportiva-ossese.png","sha256":"6b6c898a57191528e36115e34d11ab761ee6bb977eaa706113887a014685d3c1","source_size":[200,200]},{"id":1793400200213,"name":"Albalonga","url":"https://img.datasport.it/img/logos/squadre/albalonga.png","sha256":"c33f9a5ab1904b864f09034d461db8d7b582e95068af1c150bfa1c7b4ed13304","source_size":[200,200]},{"id":1793400200215,"name":"Aranova","url":"https://img.datasport.it/img/logos/squadre/aranova.png","sha256":"773a6766bcdd9d4830d2ca9d015305ef6d5663dbdf8eac2aeef2858f8088b8da","source_size":[200,200]},{"id":1793400200217,"name":"Certosa V. Campagnano","url":"https://img.a.transfermarkt.technology/wappen/head/22294.png?lm=4711","sha256":"2aa4a75de2d59df54bb6f31b84ae4ec783ab3526628183f22061cfc406e8ae52","source_size":[139,181]},{"id":1793400200218,"name":"Città di Anagni","url":"https://img.datasport.it/img/logos/squadre/citta-di-anagni.png","sha256":"32d5fd4a8ecfc1949db434b8e23b742e13a62104d1b8f83d0fbc6e04c350083a","source_size":[200,200]},{"id":1793400200225,"name":"Venafro","url":"https://img.datasport.it/img/logos/squadre/us-venafro.png","sha256":"5eab80e79ca45534555d338fd529f5702d82516906f08b94396f8d6d701e6c7a","source_size":[200,200]},{"id":1793400200226,"name":"Bisceglie","url":"https://img.datasport.it/img/logos/squadre/bisceglie.png","sha256":"857c1975ea95b0ec46e52fcd0ad081bac295794b6b21b3105cc4d2d9e39c2a29","source_size":[200,200]},{"id":1793400200227,"name":"Brindisi","url":"https://img.datasport.it/img/logos/squadre/brindisi-football-club.png","sha256":"1836431624a1ad72e528098de311dc28cc7213eb63138e809bf4f66f028895a2","source_size":[200,200]},{"id":1793400200236,"name":"Flegrea Puteolana","url":"https://img.datasport.it/img/logos/squadre/flegrea-puteolana.png","sha256":"b29a4a7ddc6cf20569eee80369de3f78a32573abbf600cdd74f36e653bb2ff89","source_size":[200,200]},{"id":1793400200241,"name":"Real Forio","url":"https://img.datasport.it/img/logos/squadre/real-forio-2014.png","sha256":"c1458f16e47f99ee8826041bc4c1bc493715edec3d36fed21a041f3d2c6cb5ff","source_size":[200,200]},{"id":1793400200242,"name":"Ebolitana","url":"https://img.datasport.it/img/logos/squadre/ebolitana.png","sha256":"944d85adf23893386761c27c31f469de35b2577f71824be2de9d7d323886db20","source_size":[200,200]},{"id":1793400200243,"name":"Gladiator","url":"https://img.datasport.it/img/logos/squadre/gladiator.png","sha256":"72b4154eed3612a05b581785a992269ebf88deedc87570635ab6adebf1b51208","source_size":[200,200]},{"id":1793400200249,"name":"Licata","url":"https://img.datasport.it/img/logos/squadre/licata-calcio.png","sha256":"c603071ccb814dda4e5c451a2bff19651a4c2fc0339649940baf595e6e9d58ce","source_size":[200,200]},{"id":1793400200251,"name":"Modica","url":"https://img.datasport.it/img/logos/squadre/new-modica-calcio.png","sha256":"884cdd447ddc94a385930193b6211b8837d9d72eb091dc4aebf5f1cf7dad56a4","source_size":[200,200]},{"id":1793400200257,"name":"Digiesse Praiatortora","url":"https://img.datasport.it/img/logos/squadre/digiesse-praiatortora.png","sha256":"5a589339f028165237e802ac7a4c6c241c5f49930288a1a8f952212bd591e8dd","source_size":[200,200]}]''')
assert len(SOURCES)==38 and len({x["id"] for x in SOURCES})==38
OUT=Path("docs/italian-clubs-2026-27/v1")
manifest_path=OUT/"status.json"
old=json.loads(manifest_path.read_text(encoding="utf-8"))
assert old["created"]==224 and old["missing_count"]==38,(old.get("created"),old.get("missing_count"))
oldmissing={x["id"]:x["name"] for x in old["missing"]}
assert {x["id"]:x["name"] for x in SOURCES}==oldmissing
def choose_bg(im):
    thumb=im.copy()
    thumb.thumbnail((90,90))
    buckets=Counter()
    for r,g,b,a in thumb.getdata():
        if a<125:continue
        mx,mn=max(r,g,b),min(r,g,b)
        if mx-mn<35 or mx<54 or mn>239:continue
        bins=(r//24,g//24,b//24)
        buckets[bins]+=a
    if not buckets:
        return (225,225,225)
    vals=buckets.most_common(1)[0][0]
    picked=tuple(min(255,x*24+12) for x in vals)
    # Softening preserves emblem hue but leaves contrast to dark outlines.
    mix=.36 if sum(picked)/3<125 else .24
    return tuple(int((1-mix)*c+mix*246) for c in picked)
def work(row):
    tid,name,url=row["id"],row["name"],row["url"]
    dest=OUT/(str(tid)+".png")
    assert not dest.exists(),str(dest)+" would overwrite an existing crest"
    last=None
    for attempt in range(3):
        try:
            res=requests.get(url,timeout=24,headers={"User-Agent":"MMD31ItalyClubs/2.0 (crest provenance checker)"})
            res.raise_for_status()
            raw=res.content
            digest=hashlib.sha256(raw).hexdigest()
            assert digest==row["sha256"],f"Source changed unexpectedly: {name} {digest}"
            img=Image.open(io.BytesIO(raw))
            assert img.format=="PNG",(name,img.format)
            img=img.convert("RGBA")
            bbox=img.getchannel("A").getbbox()
            assert bbox,(name,"empty crest")
            img=img.crop(bbox)
            bg_col=choose_bg(img)
            bg=Image.new("RGBA",(120,96),bg_col+(255,))
            img.thumbnail((102,84),Image.Resampling.LANCZOS)
            bg.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
            bg.convert("RGB").save(dest,format="PNG",optimize=True)
            check=Image.open(dest)
            assert check.size==(120,96) and check.format=="PNG"
            assert len(Counter(check.getdata()))>55,(name,"solid or placeholder")
            return {
                "id":tid,"name":name,"source":url,"source_sha256":digest,
                "source_size":row["source_size"],
                "github_path":dest.as_posix(),"background_rgb":list(bg_col),
                "matching":"2026-27 name-specific sports database or club source",
                "bytes":dest.stat().st_size,"png_sha256":hashlib.sha256(dest.read_bytes()).hexdigest()
            }
        except Exception as e:
            last=e
            time.sleep(1.25*(attempt+1))
    raise RuntimeError(f"Unable to create {name}: {last}")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    results=list(pool.map(work,SOURCES))
assert len(results)==38
assert len({x["png_sha256"] for x in results})==38
assert len({x["id"] for x in old["assets"]})==224
new=old.copy()
new["assets"]=sorted(old["assets"]+results,key=lambda x:x["id"])
assert len(new["assets"])==262
new["created"]=262
new["expected"]=262
new["missing_count"]=0
new["missing"]=[]
new["victory_flags_created"]=0
new["updated_on"]="2026-10-23"
new["additional_sources"]={"club_site":"www.borgosesiacalcio.com","sports_database":"www.datasport.it","certosa":"img.a.transfermarkt.technology"}
new["image_format"]={"width":120,"height":96,"background":"solid club-crest color","centered_crest":True}
new["rights_note"]="Club crests are third-party marks and remain property of their rights holders. Image sources and SHA256 are documented individually."
manifest_path.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SUCCESS: 38 newly generated, 262 total flags, no source mismatch, no previous badge overwritten")
