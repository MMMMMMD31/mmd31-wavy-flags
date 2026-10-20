#!/usr/bin/env python3
"""Generate only the 10 MMD31 Benelux 120x96 no-pole waving Victory flags."""
import io, json, math, hashlib, time
from pathlib import Path
from urllib.parse import quote
import requests, cairosvg
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'docs'/'emoji-flags'
OUT.mkdir(parents=True,exist_ok=True)
FILES=[
(1792700001001,"Noord-Nederland","Flag_of_Groningen_City.svg"),
(1792700001002,"Oost-Nederland","Flag_of_Zwolle.svg"),
(1792700001003,"West-Nederland","Flag_of_Amsterdam.svg"),
(1792700001004,"Zuid-Nederland","Flag_of_Eindhoven.svg"),
(1792700001005,"Flanders","Flag_of_Flanders.svg"),
(1792700001006,"Wallonia","Flag_of_Wallonia.svg"),
(1792700001007,"Brussels-Capital","Flag_of_the_Brussels-Capital_Region.svg"),
(1792700001008,"Diekirch District","Flag_of_Diekirch,_Luxembourg.svg"),
(1792700001009,"Grevenmacher District","Flag_of_Luxembourg.svg"),
(1792700001010,"Luxembourg District","Flag_of_Luxembourg_(city).svg"),
]
S=requests.Session()
S.headers.update({'User-Agent':'MMD31-FlagProject/3.0 (football game flags)','Accept':'image/svg+xml,image/png,image/*'})
def source_url(filename):
    h=hashlib.md5(filename.encode()).hexdigest()
    return 'https://upload.wikimedia.org/wikipedia/commons/'+h[0]+'/'+h[:2]+'/'+quote(filename,safe='(),-_.')
def wave(flag):
    flag=ImageOps.fit(flag.convert('RGBA'),(240,180),method=Image.Resampling.LANCZOS)
    base=Image.new('RGBA',(240,180),'white');base.alpha_composite(flag)
    src=base.convert('RGB').load()
    out=Image.new('RGBA',(120,96),(0,0,0,0));dst=out.load()
    for x in range(6,116):
        u=(x-6)/109
        offset=3.2*math.sin((u-.07)*math.pi*2.05)+1.4*math.sin((u+.2)*math.pi*3.1)
        top=10+offset-2.1*u;bottom=90+offset-2.7*u
        light=.83+.12*math.cos(4.25*math.pi*u-.24)+.05*u
        for y in range(max(0,int(top)),min(96,int(bottom)+2)):
            v=(y-top)/(bottom-top)
            if not 0<=v<=1:continue
            sx=max(0,min(239,round(u*239+1.5*math.sin(math.pi*v*1.1)*math.sin(math.pi*u*2))))
            sy=max(0,min(179,round(v*179)))
            r,g,b=src[sx,sy];shade=light+.025*math.sin(2*math.pi*v)
            if min(v,1-v)<.03:shade*=.93
            dst[x,y]=(min(255,round(r*shade)),min(255,round(g*shade)),min(255,round(b*shade)),255)
    return out
results=[]
for id,name,filename in FILES:
    dest=OUT/(str(id)+'.png')
    try:
        if not dest.is_file():
            url=source_url(filename);resp=S.get(url,timeout=30);resp.raise_for_status()
            if not resp.content or len(resp.content)>8_000_000:raise ValueError('Empty or oversized SVG')
            if b'<svg' not in resp.content[:4000]:raise ValueError('Source is not SVG')
            im=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=resp.content,output_width=480)))
            wave(im).save(dest,optimize=True)
        verify=Image.open(dest)
        assert verify.size==(120,96) and verify.mode=='RGBA'
        assert verify.getpixel((0,0))[3]==0
        results.append(dict(id=id,name=name,status='ok',source=source_url(filename)))
        print(name,'OK',flush=True)
    except Exception as err:
        results.append(dict(id=id,name=name,status='error',reason=str(err)[:170]))
        print(name,'ERROR',str(err),flush=True)
    time.sleep(0.3)
(ROOT/'docs'/'benelux-emoji-status.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
if any(x['status']!='ok' for x in results):raise SystemExit('One or more Benelux flags failed')
print('Verified ten transparent no-pole 120x96 PNGs.')
