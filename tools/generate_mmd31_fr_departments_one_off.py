#!/usr/bin/env python3
"""Temporary MMD31 selection flags for all 101 French departments.
All are ORIGINAL UNOFFICIAL FICTIONAL PENNANTS (not governmental emblems).
No network access and no copyrighted upstream imagery required.
"""
import math
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REGIONS = [
'01 03 07 15 26 38 42 43 63 69 73 74',
'21 25 39 58 70 71 89 90',
'22 29 35 56',
'18 28 36 37 41 45',
'2A 2B',
'08 10 51 52 54 55 57 67 68 88',
'02 59 60 62 80',
'75 77 78 91 92 93 94 95',
'14 27 50 61 76',
'16 17 19 23 24 33 40 47 64 79 86 87',
'09 11 12 30 31 32 34 46 48 65 66 81 82',
'44 49 53 72 85',
'04 05 06 13 83 84',
'971', '972', '973', '974', '976'
]
PALETTES = [
('#091e35','#edb74c','#f1f6fc'),('#143b57','#e8a23b','#f7f0e0'),
('#183d32','#e2c078','#f6faf9'),('#472c49','#cda85a','#fff5e6'),
('#253453','#e0874d','#faf7ec'),('#392b32','#f1c15a','#fffafa'),
('#14364b','#f77c54','#e9f6fa'),('#283b65','#dbc178','#eef5fc'),
('#2b3c4d','#c0d0de','#f6f9fc'),('#163c54','#dbaf70','#f5ead7'),
('#292c54','#f0be53','#f5f1fc'),('#295047','#dbc18a','#e8f3ed'),
('#2b3546','#f2b764','#fff8e9'),('#16334a','#d6ab41','#f5f8fd'),
('#1d5065','#d3c46c','#fbf7dc'),('#28445b','#ca9d60','#ffffff'),
('#215356','#edbf66','#f5ebd0'),('#29524b','#e4ab51','#f9fff4')
]
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(size):
    try: return ImageFont.truetype(FONT,size)
    except OSError: return ImageFont.load_default()
def rgb(t): return tuple(int(t[i:i+2],16) for i in (1,3,5))
def flag(code,palette):
    bg,accent,white=map(rgb,palette)
    im=Image.new('RGBA',(300,192),(*bg,255))
    d=ImageDraw.Draw(im)
    d.polygon([(0,0),(89,0),(201,192),(100,192)],fill=(*accent,255))
    d.polygon([(0,0),(57,0),(168,192),(111,192)],fill=(*white,255))
    d.rectangle((9,9,290,183),outline=(*accent,255),width=3)
    d.rounded_rectangle((171,44,278,112),radius=12,fill=(*white,255))
    d.text((224,77),code,fill=(*bg,255),font=font(37 if len(code)<=2 else 29),anchor='mm')
    d.text((224,138),'DEP.',fill=(*accent,255),font=font(22),anchor='mm')
    d.ellipse((28,133,56,161),fill=(*accent,255),outline=(*white,255),width=3)
    return im
def wave(im):
    src=im.resize((102,72),Image.Resampling.LANCZOS)
    dest=Image.new('RGBA',(120,96),(0,0,0,0))
    px=src.load();out=dest.load()
    for x in range(102):
        dy=int(6*math.sin((x/102)*math.pi*2-.2))
        for y in range(72):
            yy=y+12+dy+int(2*math.sin(y/15+x/37))
            if 0<=yy<96:
                c=px[x,y];shade=0.86+0.14*math.sin(x/12+0.3)
                out[x+9,yy]=(int(c[0]*shade),int(c[1]*shade),int(c[2]*shade),255)
    return dest
def main():
    root=Path('docs/departements-fr-test')
    for sub in ['flags','victory']: (root/sub).mkdir(parents=True,exist_ok=True)
    codes=[]
    for i,group in enumerate(REGIONS):
        for code in group.split():
            assert code not in codes,code
            codes.append(code)
            im=flag(code,PALETTES[i])
            im.save(root/'flags'/f'fr-{code}.png')
            wave(im).save(root/'victory'/f'fr-{code}.png')
    assert len(codes)==101
    (root/'ABOUT.md').write_text(
        '# MMD31 French departments — ONE-OFF TEST\n\n'
        '101 normal PNG selection pennants (300×192) and 101 Victory PNGs (120×96, transparency, waved).\n\n'
        '**These are ORIGINAL FICTIONAL MMD31 graphics, not official flags of departments.** '
        'Many departments do not have a single official flag. The department identifier is shown on each graphic. '
        'All art is generated locally without downloading from Wikimedia.\n',
        encoding='utf-8')
    (root/'manifest.json').write_text(json.dumps({'codes':codes,'count':len(codes),
        'flag_kind':'fictional experimental selection banner, NOT authentic official departmental flag',
        'normal_size':[300,192], 'victory_size':[120,96]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated',len(codes),'normal and',len(codes),'victory PNG flags')
if __name__=='__main__': main()
