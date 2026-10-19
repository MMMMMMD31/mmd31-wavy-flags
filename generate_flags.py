import csv,io,json,math,base64,zlib,time
from pathlib import Path
from urllib.parse import urlparse
import requests,cairosvg
from PIL import Image,ImageOps,ImageDraw
root=Path(__file__).resolve().parent
rows=list(csv.DictReader(io.StringIO(zlib.decompress(base64.b64decode((root/"flags_manifest.zlib.b64").read_text().strip())).decode("utf-8"))))
site=root/"docs"; flags=site/"flags"; flags.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers.update({"User-Agent":"MMD31 WavyFlags/1.0 (regional football flags)", "Accept":"image/svg+xml,image/png,image/jpeg,image/*"})
report=[]
for n,r in enumerate(rows,1):
 try:
  url=r["source_flag_url"].split("?")[0]
  if not url.startswith("https://"):raise ValueError("Source not HTTPS")
  response=s.get(url,timeout=25);response.raise_for_status()
  if len(response.content)>8_000_000:raise ValueError("oversized source")
  if url.lower().endswith(".svg") or b"<svg" in response.content[:4000]:
   source=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=response.content,output_width=480)))
  else:source=Image.open(io.BytesIO(response.content))
  source=ImageOps.fit(source.convert("RGBA"),(128,84),method=Image.Resampling.LANCZOS)
  out=Image.new("RGBA",(176,160));p=out.load();sp=source.load()
  for x in range(128):
   f=x/127;curve=6.5*math.sin(f*math.pi*2.1)-2.8*f;light=0.84+.15*math.cos(f*4.3*math.pi-.2)
   for y in range(84):
    dx=26+x+int(2*math.sin((y/83)*math.pi*1.7)*f);dy=24+y+round(curve)
    rr,g,b,a=sp[x,y];p[dx,dy]=(int(rr*light),int(g*light),int(b*light),a)
  d=ImageDraw.Draw(out,"RGBA")
  d.rounded_rectangle((17,15,23,150),radius=3,fill=(115,127,139,255))
  d.ellipse((15,11,25,21),fill=(190,192,198,255))
  out.alpha_composite(source.crop((0,0,2,84)).resize((3,84)),(23,24))
  out.save(flags/(r["id"]+".png"),optimize=True)
  report.append({"id":r["id"],"name":r["name"],"status":"ok"})
 except Exception as e:report.append({"id":r["id"],"name":r["name"],"status":"error","reason":str(e)[:140]})
 print(n,len(rows),r["name"],report[-1]["status"],flush=True)
 time.sleep(.12)
(site/"status.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
from html import escape
cards="".join('<div><img src="flags/'+r["id"]+'.png"><p>'+escape(r["name"])+'</p></div>' for r in report if r["status"]=="ok")
(site/"index.html").write_text('<!doctype html><meta charset="utf-8"><title>MMD31 Wavy Flags</title><style>body{font-family:system-ui;background:#eef2f6;padding:24px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px} .grid>div{background:#fff;border-radius:10px;padding:10px;text-align:center}img{width:130px;height:115px;object-fit:contain}</style><h1>MMD31 — Wavy Flags</h1><p>'+str(sum(x["status"]=="ok" for x in report))+'/'+str(len(report))+' PNG générés.</p><div class="grid">'+cards+'</div>',encoding="utf-8")
