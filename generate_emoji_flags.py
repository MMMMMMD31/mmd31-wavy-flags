import csv, io, json, math, base64, zlib, time
from pathlib import Path
import requests, cairosvg
from PIL import Image, ImageOps

root=Path(__file__).resolve().parent
rows=list(csv.DictReader(io.StringIO(zlib.decompress(base64.b64decode((root/'flags_manifest.zlib.b64').read_text().strip())).decode('utf-8'))))
site=root/'docs'; old_dir=site/'flags'; new_dir=site/'emoji-flags'; new_dir.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({'User-Agent':'MMD31 Regional Flags/2.0 (+https://github.com/manoemenanteau-ship-it/mmd31-wavy-flags)','Accept':'image/svg+xml,image/png,image/jpeg,image/*'})

def recover_old(img):
    src=img.convert('RGBA');flat=Image.new('RGBA',(128,84))
    for x in range(128):
        f=x/127;curve=6.5*math.sin(f*math.pi*2.1)-2.8*f
        light=.84+.15*math.cos(f*4.3*math.pi-.2)
        for y in range(84):
            xx=26+x+int(2*math.sin(y/83*math.pi*1.7)*f);yy=24+y+round(curve)
            if 0<=xx<src.width and 0<=yy<src.height:
                r,g,b,a=src.getpixel((xx,yy))
                if a:flat.putpixel((x,y),(min(255,round(r/max(.3,light))),min(255,round(g/max(.3,light))),min(255,round(b/max(.3,light))),a))
    return flat

def render(flag):
    flag=ImageOps.fit(flag.convert('RGBA'),(240,180),method=Image.Resampling.LANCZOS)
    base=Image.new('RGBA',(240,180),(255,255,255,255));base.alpha_composite(flag)
    pix=base.convert('RGB').load()
    out=Image.new('RGBA',(120,96),(0,0,0,0));dst=out.load()
    for x in range(6,116):
        u=(x-6)/109
        wave=3.2*math.sin((u-.07)*math.pi*2.05)+1.4*math.sin((u+.2)*math.pi*3.1)
        top=10+wave-2.1*u;bot=90+wave-2.7*u
        shade0=.83+.12*math.cos(4.25*math.pi*u-.24)+.05*u
        for y in range(max(0,int(top)),min(96,int(bot)+2)):
            v=(y-top)/(bot-top)
            if not 0<=v<=1:continue
            sx=max(0,min(239,round(u*239+1.5*math.sin(math.pi*v*1.1)*math.sin(math.pi*u*2))))
            sy=max(0,min(179,round(v*179)))
            r,g,b=pix[sx,sy];shade=shade0+.025*math.sin(2*math.pi*v)
            if min(v,1-v)<.03:shade*=.93
            dst[x,y]=(min(255,round(r*shade)),min(255,round(g*shade)),min(255,round(b*shade)),255)
    return out

def fetch_original(url):
    url=url.split('?')[0]
    if not url.startswith('https://'):raise ValueError('HTTPS source required')
    res=s.get(url,timeout=24);res.raise_for_status()
    if len(res.content)>7_000_000:raise ValueError('oversized image')
    if url.lower().endswith('.svg') or b'<svg' in res.content[:4000]:
        return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=res.content,output_width=480)))
    return Image.open(io.BytesIO(res.content))

status=[]
for n,r in enumerate(rows,1):
    old=old_dir/(r['id']+'.png');target=new_dir/(r['id']+'.png')
    try:
        if target.exists():
            status.append({'id':r['id'],'name':r['name'],'status':'ok','cached':True})
            continue
        if old.exists():
            source=recover_old(Image.open(old));method='old-cache'
        else:
            source=fetch_original(r['source_flag_url']);method='original'
        render(source).save(target,optimize=True)
        assert Image.open(target).size==(120,96)
        status.append({'id':r['id'],'name':r['name'],'status':'ok','method':method})
    except Exception as e:
        status.append({'id':r['id'],'name':r['name'],'status':'error','reason':str(e)[:140]})
    print(n,'/',len(rows),r['name'],status[-1]['status'],flush=True)
    if not old.exists():time.sleep(.35)

(site/'emoji-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
from html import escape
cards=''.join('<figure><img src="emoji-flags/'+r['id']+'.png"><figcaption>'+escape(r['name'])+'</figcaption></figure>' for r in status if r['status']=='ok')
(site/'emoji-gallery.html').write_text('<!doctype html><meta charset="utf-8"><title>MMD31 Emoji Wavy Flags</title><style>body{font-family:system-ui;background:#23252a;color:white;padding:24px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}figure{margin:0;padding:12px;background:#393a3f;border-radius:8px;text-align:center}img{width:120px;height:96px;object-fit:contain}figcaption{font-size:13px}</style><h1>MMD31 Victory Emoji Wavy Flags</h1><p>'+str(sum(x['status']=='ok' for x in status))+'/'+str(len(status))+' PNG 120x96 transparents</p><div class="grid">'+cards+'</div>',encoding='utf-8')
