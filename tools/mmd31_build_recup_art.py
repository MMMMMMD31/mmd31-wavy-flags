#!/usr/bin/env python3
"""Build ReCup logo and trophy using existing MMD31-owned artwork in the repository.
No Wikimedia dependency; intended sizes: logo 1024x768, trophy 768x960.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path("docs")
SRC=ROOT/"wecr-logos"/"western_europe_logo.png"
OUT=ROOT/"wecr-recup"
OUT.mkdir(parents=True, exist_ok=True)

def font(size, serif=False):
    paths=[
      "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if serif else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
      "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf"
    ]
    for p in paths:
      if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def centered(d,text,cx,y,ft,fill,stroke=0,stroke_fill=None):
    d.text((cx,y),text,font=ft,anchor="mt",fill=fill,
      stroke_width=stroke,stroke_fill=stroke_fill)

src=Image.open(SRC).convert("RGB")
src=src.resize((1024,768),Image.Resampling.LANCZOS)
logo=src.convert("RGBA")
overlay=Image.new("RGBA",(1024,768),(0,0,0,0))
od=ImageDraw.Draw(overlay)
# Remove only the legacy wording; do not obscure the principal golden trophy or edge flags.
for y in range(473,700):
    for x in range(219,806):
        edge=min(x-219,805-x,y-473,699-y)
        a=int(245*min(1,max(0,edge/26)))
        od.point((x,y),fill=(3,15,32,a))
logo=Image.alpha_composite(logo,overlay).convert("RGB")
d=ImageDraw.Draw(logo)
gold=(237,196,107); ivory=(255,246,227)
centered(d,"WESTERN EUROPE",512,512,font(53,True),ivory,2,(29,32,38))
centered(d,"ReCup",512,586,font(100,True),gold,2,(29,27,23))
d.line([(339,699),(685,699)],fill=gold,width=3)
logo.save(OUT/"Western_Europe_ReCup_Logo_1024x768.png", optimize=True)

# Trophy art: isolate the main trophy / European map from the preexisting poster.
W,H=768,960
trophy=Image.new("RGB",(W,H))
p=trophy.load()
for y in range(H):
    for x in range(W):
        rx=(x-W/2)/W;ry=(y-360)/H
        glow=max(0,1-2.9*math.sqrt(rx*rx+ry*ry))
        p[x,y]=(int(3+18*glow),int(12+29*glow),int(27+40*glow))
dr=ImageDraw.Draw(trophy)
for radius in (320,304,285):
    dr.ellipse((W/2-radius,70,W/2+radius,70+radius*2),outline=(124,91,40),width=2)
# Main trophy-centered material from the Western Europe artwork.
crop=src.crop((266,27,760,482))
crop=crop.resize((636,586),Image.Resampling.LANCZOS)
mask=Image.new("L",crop.size,0)
md=ImageDraw.Draw(mask)
md.rounded_rectangle((8,3,628,583),radius=54,fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(23))
trophy.paste(crop,(66,81),mask)
dr=ImageDraw.Draw(trophy)
# Metallic plinth, highlights and engraving.
dr.rounded_rectangle((70,688,698,917),radius=23,fill=(9,17,29),outline=(190,135,59),width=7)
dr.rounded_rectangle((104,722,664,879),radius=11,fill=(10,24,42),outline=(225,181,88),width=3)
dr.line([(94,894),(676,894)],fill=(248,215,129),width=4)
centered(dr,"WESTERN EUROPE",W//2,746,font(39,True),(245,231,194),1,(2,9,17))
centered(dr,"ReCup",W//2,806,font(70,True),(251,203,104),1,(2,9,17))
dr.text((W//2,916),"MMD31 REGIONAL FOOTBALL",font=font(17),
        anchor="mm",fill=(197,174,127))
trophy.save(OUT/"Western_Europe_ReCup_Trophy_768x960.png", optimize=True)
print("Generated",[(p.name,Image.open(p).size) for p in OUT.glob("*.png")])
