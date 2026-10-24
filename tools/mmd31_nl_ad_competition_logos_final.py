#!/usr/bin/env python3
"""Create two square 512x512 PNG competition logos from recognizable official artwork."""
import io, json, hashlib
from pathlib import Path
from PIL import Image
import requests
ROOT=Path('docs/nl-andorra-competition-logos/v2')
ROOT.mkdir(parents=True,exist_ok=True)
session=requests.Session()
session.headers.update({'User-Agent':'Mozilla/5.0 (compatible; MMD31 educational football assets)'})
sources={
  'eredivisie':[
    'https://upload.wikimedia.org/wikipedia/commons/8/81/VriendenLoterij_Eredivisie_Logo.png',
    'https://assets.football-logos.cc/logos/netherlands/1500x1500/eredivisie--no-text.c22e770a.png'
  ],
  'andorra-faf':[
    'https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-nl-andorra-20261023/docs/nl-andorra-competition-logos/v1/faf.png',
  ]
}
manifest={}
for key, options in sources.items():
    errors=[]
    for u in options:
        try:
            response=session.get(u,timeout=40);response.raise_for_status()
            image=Image.open(io.BytesIO(response.content))
            image.load()
            image=image.convert('RGBA')
            if min(image.size)<100:raise ValueError('source too small')
            bounds=image.getchannel('A').getbbox()
            if bounds is None:raise ValueError('transparent logo without subject')
            cropped=image.crop(bounds)
            cropped.thumbnail((466,466),Image.Resampling.LANCZOS)
            output=Image.new('RGBA',(512,512),(0,0,0,0))
            output.alpha_composite(cropped,((512-cropped.width)//2,(512-cropped.height)//2))
            outpath=ROOT/(key+'.png')
            output.save(outpath,'PNG',optimize=True)
            with Image.open(outpath) as saved:
                assert saved.format=='PNG' and saved.size==(512,512)
            data=outpath.read_bytes()
            manifest[key]={'status':'published','source':u,'output':str(outpath),
              'format':'PNG','pixel_size':[512,512], 'sha256':hashlib.sha256(data).hexdigest(),
              'transparent_square':True,'source_kind':'official competition logo' if key=='eredivisie' else 'federation emblem'}
            print(key,'OK',len(data),'bytes',flush=True)
            break
        except Exception as error:
            errors.append(str(error)[:200])
    else:
        raise RuntimeError(f'{key}: no verified logo source; {errors}')
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
