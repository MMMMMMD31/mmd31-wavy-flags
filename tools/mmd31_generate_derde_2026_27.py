#!/usr/bin/env python3
"""Create authentic-looking game flags only when a source explicitly labels the same real club."""
import io,math,json,time,hashlib,re,unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin
import requests,cairosvg
from bs4 import BeautifulSoup
from PIL import Image
ALIASES=[["ACV","ADO '20","Dovo","DVS 33 Ermelo","Eemdijk","Excelsior '31","Harkemase Boys","Hercules","Hollandia","Hoogeveen","Purmersteijn","SC Genemuiden","VV Scherpenzeel","Sparta Nijkerk","Sportlust '46","Staphorst","SVZW","TEC"],["Achilles Veen","Blauw Geel","Dongen","EVV","Excelsior Maassluis","FC Lisse","Gemert","GOES","Groene Ster","Noordwijk","Roosendaal","Rijnvogels","Poortugaal","TOGB","UDI '19","UNA","Vvsb","Zwaluwen"]]
assert [len(a) for a in ALIASES]==[18,18]
ROOT=Path('docs/nl-derde-divisie-2026-27/v1')
(ROOT/'standard').mkdir(parents=True,exist_ok=True)
(ROOT/'victory').mkdir(parents=True,exist_ok=True)
BASE='https://derde-divisie.nl/stand/derde-divisie-'
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; MMD31ClubAssets/2.0; educational football archive)'})
def norm(s):
    s=unicodedata.normalize('NFKD',s.lower())
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+','',s)
def getpage(letter):
    u=BASE+letter+'/'
    r=S.get(u,timeout=30);r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    entries={}
    for tag in soup.find_all('img'):
        alt=tag.get('alt','').strip()
        if not alt:continue
        k=norm(alt)
        urls=[]
        for attr in ('data-src','src','data-original','data-lazy-src','data-srcset','srcset'):
            v=tag.get(attr)
            if v: urls.append(v.split(',')[0].strip().split(' ')[0])
        urls=[urljoin(u,v) for v in urls if 'data:image' not in v and not v.startswith('blob:')]
        if urls:entries.setdefault(k,[]).extend(urls)
    return entries
def download(u):
    r=S.get(u,timeout=22,headers={'Referer':'https://derde-divisie.nl/'})
    r.raise_for_status()
    d=r.content
    if len(d)<200:raise ValueError('too-small image')
    if b'<svg' in d[:5000] or u.lower().split('?')[0].endswith('.svg'):
        d=cairosvg.svg2png(bytestring=d,output_width=512)
    im=Image.open(io.BytesIO(d)).convert('RGBA')
    if im.width<28 or im.height<28:raise ValueError('tiny image')
    bb=im.getchannel('A').getbbox()
    if not bb:raise ValueError('transparent image')
    return im.crop(bb),hashlib.sha256(d).hexdigest()
def dominant(im):
    small=im.copy();small.thumbnail((90,90))
    c=Counter()
    for r,g,b,a in small.getdata():
        if a<100 or max(r,g,b)-min(r,g,b)<35:continue
        c[(r//32,g//32,b//32)]+=a
    if c:
        rgb=[min(255,v*32+16) for v in c.most_common(1)[0][0]]
    else: rgb=[61,93,145]
    return tuple(int(.78*v+.22*255) for v in rgb)
def build(im):
    bg=Image.new('RGBA',(120,96),dominant(im)+(255,))
    x=im.copy();x.thumbnail((99,82),Image.Resampling.LANCZOS)
    bg.alpha_composite(x,((120-x.width)//2,(96-x.height)//2))
    return bg
def wave(bg):
    small=bg.resize((108,75),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(120,96),(0,0,0,0))
    src=small.load();dst=out.load()
    for j in range(75):
        for i in range(108):
            x=int(i+6+3.2*math.sin(j/11+i/23))
            y=int(j+9+4.0*math.sin(i/17))
            if 0<=x<120 and 0<=y<96:
                r,g,b,a=src[i,j]
                f=.91+.09*math.sin(i/11)
                dst[x,y]=(int(r*f),int(g*f),int(b*f),a)
    return out
pages={}
for letter in ('a','b'):
    try:pages[letter]=getpage(letter)
    except Exception as e:
        print('PAGE FETCH FAILED',letter,str(e),flush=True)
        pages[letter]={}
status=[]
seen={}
for gp,aliases in enumerate(ALIASES):
    for n,alt in enumerate(aliases):
        index=gp*18+n
        uid=1895100000074+index
        letter='ab'[gp]
        aliases_to_try=[alt]
        if alt=='EVV':aliases_to_try+=['EVV Echt']
        if alt=='Roosendaal':aliases_to_try+=['RBC']
        if alt=='VV Scherpenzeel':aliases_to_try+=['Scherpenzeel']
        fallbacks={
          'ACV':['https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/netherlands/ACV_Assen.svg'],
          'Excelsior Maassluis':['https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/netherlands/Excelsior_Maassluis.svg']
        }
        urls=[]
        for key in aliases_to_try:urls+=pages[letter].get(norm(key),[])
        urls+=fallbacks.get(alt,[])
        urls=list(dict.fromkeys(urls))
        item={'id':uid,'name':alt,'group':letter.upper(),'status':'missing','source':None}
        errors=[]
        for u in urls[:12]:
            try:
                im,h=download(u)
                if h in seen and seen[h]!=uid:
                    raise ValueError('identical-image-collision with '+str(seen[h]))
                img=build(im)
                if img.size!=(120,96):raise ValueError('bad output size')
                img.save(ROOT/'standard'/f'{uid}.png',optimize=True)
                wave(img).save(ROOT/'victory'/f'{uid}.png',optimize=True)
                seen[h]=uid
                item.update({'status':'ok','source':u,'background':dominant(im)})
                break
            except Exception as e:
                errors.append(str(e)[:150])
        if item['status']!='ok':item['errors']=errors[:3]
        status.append(item)
        print(uid,alt,item['status'],flush=True)
ROOT.joinpath('status.json').write_text(json.dumps({'count':len(status),'verified':sum(a['status']=='ok' for a in status),'assets':status},ensure_ascii=False,indent=2)+'\n')
print('Completed',sum(a['status']=='ok' for a in status),'of 36',flush=True)
