#!/usr/bin/env python3
"""Real image-only render of Ponta Delgada and Campeonato dos Açores clubs.
No fallback logos, no arbitrary text badges. Report failures honestly.
"""
from pathlib import Path
from PIL import Image,ImageChops
from collections import Counter,deque
import hashlib,requests,json,io,time,concurrent.futures
BASE=Path('docs/portugal-gibraltar-clubs-2026-27/v1')
ROWS=json.loads(Path('tools/azores_2026_27_new_badges.json').read_text(encoding='utf8'))
def download(url):
    for i in range(3):
        try:
            r=requests.get(url,headers={'User-Agent':'Mozilla/5.0','Accept':'image/png,image/jpeg,image/webp,*/*'},timeout=(12,30))
            r.raise_for_status()
            if len(r.content)<250 or len(r.content)>7_000_000:raise ValueError('Invalid source size')
            im=Image.open(io.BytesIO(r.content)).convert('RGBA')
            im.load()
            return im,hashlib.sha256(r.content).hexdigest()
        except Exception as e:
            err=e;time.sleep(.5*(i+1))
    raise RuntimeError(str(err)[:230])
def bg_from_pixels(im):
    small=im.copy();small.thumbnail((100,100))
    cc=Counter()
    for r,g,b,a in small.getdata():
        if a<150 or max(r,g,b)-min(r,g,b)<50 or max(r,g,b)<70:continue
        cc[(r//28,g//28,b//28)]+=1
    if not cc:return (219,220,225),'neutral fallback'
    k=cc.most_common(1)[0][0]
    col=tuple(min(255,x*28+14) for x in k)
    alpha=.46 if sum(col)<300 else .24
    return tuple(round((1-alpha)*v+alpha*246) for v in col),'source logo pixels'
def crop_external_white(im):
    # Replace near-white edge-connected background ONLY (preserves enclosed white shield).
    im=im.copy();w,h=im.size
    # downsample before flood to limit huge image cost
    if max(w,h)>700:
        im.thumbnail((700,700),Image.Resampling.LANCZOS);w,h=im.size
    px=im.load();q=deque();seen=set()
    for x in range(w):
        for y in (0,h-1):
            r,g,b,a=px[x,y]
            if a>130 and min(r,g,b)>245:q.append((x,y));seen.add((x,y))
    for y in range(h):
        for x in (0,w-1):
            r,g,b,a=px[x,y]
            if a>130 and min(r,g,b)>245:q.append((x,y));seen.add((x,y))
    while q:
        x,y=q.popleft();r,g,b,a=px[x,y]
        px[x,y]=(r,g,b,0)
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            xx,yy=x+dx,y+dy
            if 0<=xx<w and 0<=yy<h and (xx,yy) not in seen:
                r,g,b,a=px[xx,yy]
                if a>130 and min(r,g,b)>245:
                    seen.add((xx,yy));q.append((xx,yy))
    bounds=im.getchannel('A').getbbox()
    return im.crop(bounds) if bounds else im
def render(row):
    try:
        im,src_sha=download(row['url'])
        im=crop_external_white(im)
        bbox=im.getchannel('A').getbbox()
        if not bbox:raise ValueError('badge is empty')
        im=im.crop(bbox)
        bg,basis=bg_from_pixels(im)
        canvas=Image.new('RGBA',(120,96),bg+(255,))
        im.thumbnail((100,84),Image.Resampling.LANCZOS)
        canvas.alpha_composite(im,((120-im.width)//2,(96-im.height)//2))
        p=BASE/(str(row['id'])+'.png');canvas.convert('RGB').save(p,format='PNG',optimize=True)
        with Image.open(p) as ck:
            if ck.format!='PNG' or ck.size!=(120,96):raise ValueError('Incorrect png dimensions')
            if len(ck.getcolors(120*96) or [])<30:raise ValueError('Placeholder-looking image')
        return {'id':row['id'],'name':row['name'],'source':row['url'],'path':p.as_posix(),'background':bg,'background_basis':basis,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'original_sha256':src_sha}
    except Exception as e:return {'id':row['id'],'name':row['name'],'source':row['url'],'error':str(e)[:290]}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    rows=sorted(pool.map(render,ROWS),key=lambda r:r['id'])
good=[r for r in rows if 'path' in r];bad=[r for r in rows if 'error' in r]
(BASE/'status-azores.json').write_text(json.dumps({'expected':len(ROWS),'created':len(good),'missing_count':len(bad),'assets':good,'missing':bad,'note':'True logos only; source identification pending per-club review'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Published',len(good),'of',len(ROWS), 'missing',len(bad),flush=True)
for x in bad:print('FAILED',x['id'],x['name'],x['error'],flush=True)
