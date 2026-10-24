#!/usr/bin/env python3
"""Real club crests only; authentic upstream SVGs, output 120x96 PNG with colored background.
No invented shields. All failures recorded; never publish bad logo silently."""
import io, json, hashlib, colorsys
from pathlib import Path
from urllib.parse import quote
from collections import Counter
import requests,cairosvg
from PIL import Image
DATA={"EE":{"federation":"Estonia_National_Team.svg","clubs":["Levadia.svg","Flora_Tallinn.svg","Paide.svg","Nõmme_Kalju.svg","Tammeka.svg","Harju_JK.svg","Pärnu_JK_Vaprus.svg","Kuressaare.svg","FC_Nõmme_United.svg","Narva_Trans.svg"]},"LV":{"federation":"Latvia_National_Team.svg","clubs":["RFS.svg","Riga.svg","Auda.svg","Liepāja.svg","Daugavpils.svg","SK_Super_Nova.svg","Jelgava.svg","Grobiņa.svg","Tukums_2000.svg","Ogre_United.svg"]},"LT":{"federation":"Lithuania_National_Team.svg","clubs":["Kauno_Žalgiris.svg","Žalgiris_Vilnius.svg","Sūduva.svg","TransINVEST.svg","Banga.svg","Džiugas.svg","Panevėžys.svg","Hegelmann.svg","Šiauliai.svg","Riteriai.svg"]},"PL":{"federation":"Polish_Football_Association.svg","clubs":["Górnik_Zabrze.svg","Lech_Poznań.svg","Pogoń_Szczecin.svg","Legia_Warszawa.svg","Piast_Gliwice.svg","Wisła_Kraków.svg","Zagłębie_Lubin.svg","GKS_Katowice.svg","Korona_Kielce.svg","Wisła_Płock.svg","Motor_Lublin.svg","Jagiellonia_Białystok.svg","Cracovia.svg","Widzew_Lodz.svg","Wieczysta_Kraków.svg","Radomiak_Radom.svg","Raków_Częstochowa.svg","Śląsk_Wrocław.svg"]}}
DIRS={'EE':'estonia','LV':'latvia','LT':'lithuania','PL':'poland'}
ROOT=Path('docs/cge36-four-leagues-2026')
session=requests.Session()
session.headers.update({'User-Agent':'Mozilla/5.0 (CGE36 authenticity/attribution image publisher)'})
manifest=[]
def download(key,file):
    src='https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/'+DIRS[key]+'/'+quote(file)
    resp=session.get(src,timeout=35);resp.raise_for_status()
    if not b'<svg' in resp.content[:1500]:raise ValueError('Not an authentic SVG file')
    png=cairosvg.svg2png(bytestring=resp.content,output_width=512,output_height=512)
    im=Image.open(io.BytesIO(png)).convert('RGBA')
    bounds=im.getchannel('A').getbbox()
    if not bounds:raise ValueError('Empty SVG')
    return im.crop(bounds),src
def color_for(im):
    # Emblem color, avoiding white/black, derived from genuine image pixels.
    palette=Counter()
    im=im.resize((64,64),Image.Resampling.LANCZOS)
    for r,g,b,a in im.getdata():
        if a<150:continue
        mx=max(r,g,b);mn=min(r,g,b)
        if mx-mn<42:continue
        # quantize
        palette[(r//28*28,g//28*28,b//28*28)]+=1
    rgb=palette.most_common(1)[0][0] if palette else (40,95,158)
    # pale backdrop tinted by real club color
    return tuple(int(.65*v+.35*245) for v in rgb)
for key,info in DATA.items():
    for i,name in enumerate(info['clubs']):
        uid=1897600000000 + {'EE':1000,'LV':2000,'LT':3000,'PL':4000}[key] + i+1
        record={'nation':key,'teamId':uid,'source_filename':name,'status':'missing'}
        try:
            im,src=download(key,name)
            bg=color_for(im)
            picture=Image.new('RGBA',(120,96),bg+(255,))
            im.thumbnail((96,82),Image.Resampling.LANCZOS)
            picture.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
            dest=ROOT/'clubs'/key/(str(uid)+'.png')
            dest.parent.mkdir(parents=True,exist_ok=True)
            picture.save(dest,'PNG',optimize=True)
            assert Image.open(dest).size==(120,96)
            record.update({'status':'ok','source':src,'path':dest.as_posix(),
             'background_rgb':list(bg),'size':[120,96],'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
        except Exception as e:
            record['error']=str(e)
        manifest.append(record);print(key,i+1,name,record['status'],flush=True)
    record={'nation':key,'teamId':None,'type':'federation_logo','source_filename':info['federation'],'status':'missing'}
    try:
        im,src=download(key,info['federation'])
        img=Image.new('RGBA',(512,512),(0,0,0,0))
        im.thumbnail((482,482),Image.Resampling.LANCZOS)
        img.alpha_composite(im,((512-im.width)//2,(512-im.height)//2))
        dest=ROOT/'federations'/(key.lower()+'.png')
        dest.parent.mkdir(parents=True,exist_ok=True)
        img.save(dest,'PNG',optimize=True)
        assert Image.open(dest).size==(512,512)
        record.update({'status':'ok','source':src,'path':dest.as_posix(),'size':[512,512],
         'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    except Exception as e:record['error']=str(e)
    manifest.append(record)
(ROOT/'manifest.json').write_text(json.dumps({'expected_clubs':48,'clubs_ok':sum(1 for r in manifest if r['status']=='ok' and r.get('teamId') is not None),
  'federations_ok':sum(r['status']=='ok' and r.get('type')=='federation_logo' for r in manifest),
  'items':manifest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if any(r['status']!='ok' for r in manifest):
    raise SystemExit('Incomplete assets; inspect manifest (not published as complete)')
