#!/usr/bin/env python3
"""MMD31 official-shaped 120x96 flags and transparent waving victory images; references documented."""
import io,json,math,os,time
from collections import Counter
from pathlib import Path
from urllib.parse import quote
import requests,cairosvg
from PIL import Image,ImageDraw
NL="Ajax.svg|PSV_Eindhoven.svg|Feyenoord.svg|AZ_Alkmaar.svg|Twente.svg|FC_Utrecht.svg|N.E.C._Nijmegen.svg|sc_Heerenveen.svg|FC_Groningen.svg|Go_Ahead_Eagles.svg|Fortuna_Sittard.svg|Sparta_Rotterdam.svg|Excelsior_Rotterdam.svg|PEC_Zwolle.svg|Telstar.svg|ADO_Den_Haag.svg|SC_Cambuur.svg|Willem_II.svg|Heracles_Almelo.svg|NAC_Breda.svg|Volendam.svg|FC_Dordrecht.svg|MVV_Maastricht.svg|Roda_JC_Kerkrade.svg|De_Graafschap.svg|FC_Eindhoven.svg|FC_Emmen.svg|TOP_Oss.svg|RKC_Waalwijk.svg|Ajax.svg|PSV_Eindhoven.svg|FC_Utrecht.svg|AZ_Alkmaar.svg|Helmond_Sport.svg|Almere_City_FC.svg|FC_Den_Bosch.svg|VVV-Venlo.svg|Vitesse.svg|Quick_Boys.svg|Kozakken_Boys.svg|De_Treffers.svg|HHC_Hardenberg.svg|IJsselmeervogels.svg|SV_Spakenburg.svg|AFC_Amsterdam.svg|Sparta_Rotterdam.svg|RKAV_Volendam.svg|VV_Katwijk.svg|BVV_Barendrecht.svg|Rijnsburgse_Boys.svg|HSV_Hoek.svg|Koninklijke_HFC.svg|VV_Kloetinge.svg|Almere_City_FC.svg|GVVV.svg|ROHDA_Raalte.svg".split('|')
AD=["andorra/FC_Santa_Coloma.svg","andorra/Inter_Escaldes.svg","andorra/Ordino.svg","https://assets.football-logos.cc/logos/andorra/700x700/atletic-escaldes.5893f757.png","andorra/Rànger's.svg","https://www.footylogos.com/dls/logo/cf-esperanca-dandorra.png","https://assets.football-logos.cc/logos/andorra/512x512/penya-encarnada.810ebff1.png","https://associacions.andorralavella.ad/sites/default/files/nou%20logo%20Club%20Esportiu%20CP.JPG","https://images.seeklogo.com/logo-png/34/1/sporting-club-descaldes-logo-png_seeklogo-346549.png","andorra/CE_Carroi.svg","https://www.footylogos.com/dls/logo/fs-la-massana.png","https://toppng.com/uploads/preview/ue-sant-julia-vector-logo-11573919707yzc3wp6ehd.png","https://www.footylogos.com/dls/logo/pirineus-united-fc.png","andorra/UE_Santa_Coloma.svg","https://images.seeklogo.com/logo-png/61/1/city-escaldes-fc-logo-png_seeklogo-611359.png","https://www.playmakerstats.com/img/logos/equipas/104724_imgbank_1687182507.png","andorra/FC_Santa_Coloma.svg"]
assert len(NL)==56 and len(AD)==17
ROOT=Path('docs/nl-andorra-clubs-2026-27/v1')
(ROOT/'standard').mkdir(parents=True,exist_ok=True)
(ROOT/'victory').mkdir(parents=True,exist_ok=True)
s=requests.Session()
s.headers.update({'User-Agent':'MMD31-club-crest-publisher/1.0 (educational database)'})
def url_of(country, name):
    if name.startswith('https://'):return name
    return 'https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/'+quote(name,safe="/")
def get_image(url):
    e=None
    for attempt in range(2):
        try:
            r=s.get(url,timeout=20)
            r.raise_for_status()
            if len(r.content)<150:raise ValueError('content too small')
            data=r.content
            if b'<svg' in data[:4000] or url.lower().endswith('.svg'):
                data=cairosvg.svg2png(bytestring=data,output_width=512)
            im=Image.open(io.BytesIO(data)).convert('RGBA')
            if im.width<25 or im.height<25:raise ValueError('image too small')
            bb=im.getchannel('A').getbbox()
            if not bb:raise ValueError('transparent image')
            return im.crop(bb)
        except Exception as exc:
            e=exc
            time.sleep(0.5)
    raise RuntimeError(str(e))
def color(im):
    reduced=im.copy();reduced.thumbnail((96,96))
    weights=Counter()
    for r,g,b,a in reduced.getdata():
        if a<110 or max(r,g,b)-min(r,g,b)<35:continue
        weights[(r//32,g//32,b//32)]+=a
    if not weights: return (89,99,124)
    rgb=[min(255,16+v*32) for v in weights.most_common(1)[0][0]]
    return tuple(int(.8*v+.2*255) for v in rgb)
def standard(im):
    bg=Image.new('RGBA',(120,96),color(im)+(255,))
    x=im.copy();x.thumbnail((101,82),Image.Resampling.LANCZOS)
    bg.alpha_composite(x,((120-x.width)//2,(96-x.height)//2))
    return bg
def waving(bg):
    # Wavy flag, no pole, transparent external corners, horizontal sinusoidal waves.
    core=bg.resize((108,75),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(120,96),(0,0,0,0))
    src=core.load();dst=out.load()
    for j in range(75):
        for i in range(108):
            x=int(i+6+3.2*math.sin(j/11+i/23))
            y=int(j+9+4.0*math.sin(i/17))
            if 0<=x<120 and 0<=y<96:
                r,g,b,a=src[i,j]
                f=.91+.09*math.sin(i/11)
                dst[x,y]=(int(r*f),int(g*f),int(b*f),a)
    return out
items=[]
for n,name in enumerate(['netherlands/'+x for x in NL]+AD,1):
    uid=1895100000000+n
    url=url_of('NL' if n<=56 else 'AD',name)
    try:
        im=get_image(url)
        st=standard(im)
        wa=waving(st)
        st.save(ROOT/'standard'/f'{uid}.png',optimize=True)
        wa.save(ROOT/'victory'/f'{uid}.png',optimize=True)
        assert Image.open(ROOT/'standard'/f'{uid}.png').size==(120,96)
        assert Image.open(ROOT/'victory'/f'{uid}.png').size==(120,96)
        items.append({'id':uid,'result':'ok','source':url,'background':color(im)})
    except Exception as exc:
        items.append({'id':uid,'result':'missing','source':url,'error':str(exc)})
    print(n,items[-1]['result'],url,flush=True)
(ROOT/'status.json').write_text(json.dumps({'total':73,'completed':sum(x['result']=='ok' for x in items),'assets':items},ensure_ascii=False,indent=2)+'\n')
print('DONE',sum(x['result']=='ok' for x in items),'of',73)
