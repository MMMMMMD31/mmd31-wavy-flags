#!/usr/bin/env python3
"""Fetch only identified authentic crests; never synthesize a logo."""
import io,json,hashlib,re,unicodedata,time
from pathlib import Path
from urllib.parse import quote
import requests,cairosvg
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
CLUBS={"EE":[["Tartu JK Welco","Welco"],["Viimsi JK","Viimsi"],["Tallinna FC Flora U21","Flora_Tallinn.svg"],["Tallinna FCI Levadia U21","Levadia.svg"],["FC Elva","Elva"],["JK Tallinna Kalev","Kalev.svg"],["FC Nõmme United U21","FC_Nõmme_United.svg"],["FC Tallinn","Tallinn"],["Nõmme Kalju FC U21","Nõmme_Kalju.svg"],["Maardu Linnameeskond","Maardu"]],"LV":[["FK Metta","Metta.svg"],["Valmiera FC","Valmiera.svg"],["Leevon PPK","Leevon PPK"],["Riga Mariners","Riga Mariners"],["JDFS Alberts","JDFS Alberts"],["Mārupes SC","Marupes SC"],["Riga FC II","Riga.svg"],["SK Super Nova II","SK_Super_Nova.svg"],["Skanstes SK","Skanstes SK"],["FK Smiltene/BJSS","Smiltene BJSS"],["FK Tukums 2000 II","Tukums_2000.svg"],["FC RFS II","RFS.svg"],["JFK Ventspils","JFK Ventspils"],["Rēzeknes FA/BJSS","Rezeknes_BJSS.svg"]],"LT":[["FK Minija Kretinga","Minija"],["FK Babrungas Plungė","Babrungas"],["FK Be1","Be1"],["FC Neptūnas Klaipėda","Neptunas"],["FK Žalgiris Vilnius B","Žalgiris_Vilnius.svg"],["Vilniaus BFA","Vilniaus BFA"],["FK Tauras Tauragė","Tauras.svg"],["DFK Dainava Alytus","Dainava.svg"],["FK Atmosfera Mažeikiai","Atmosfera"],["FK Jonava","Jonava.svg"],["FK Garliava","Garliava"],["FK TransINVEST B","TransINVEST.svg"],["FK Kauno Žalgiris B","Kauno_Žalgiris.svg"],["FC Hegelmann B","Hegelmann.svg"],["FK Ekranas Panevėžys","Ekranas.svg"],["FA Šiauliai B","Šiauliai.svg"]],"PL":[["Pogoń Grodzisk Mazowiecki","Pogoń_Grodzisk_Mazowiecki.svg"],["Polonia Warszawa","Polonia_Warszawa.svg"],["Bruk-Bet Termalica Nieciecza","Bruk-Bet_Termalica_Nieciecza.svg"],["Lechia Gdańsk","Lechia_Gdańsk.svg"],["Miedź Legnica","Miedź_Legnica.svg"],["Warta Poznań","Warta_Poznań.svg"],["ŁKS Łódź","ŁKS_Łódź.svg"],["Ruch Chorzów","Ruch_Chorzów.svg"],["Stal Rzeszów","Stal_Rzeszów.svg"],["Polonia Bytom","Polonia_Bytom.svg"],["Pogoń Siedlce","Pogoń_Siedlce.svg"],["Chrobry Głogów","Chrobry_Głogów.svg"],["Odra Opole","Odra_Opole.svg"],["Stal Mielec","Stal_Mielec.svg"],["Arka Gdynia","Arka_Gdynia.svg"],["Puszcza Niepołomice","Puszcza_Niepołomice.svg"],["Unia Skierniewice","Unia_Skierniewice.svg"],["Podbeskidzie Bielsko-Biała","Podbeskidzie_Bielsko-Biała.svg"]]}
COUNTRY={'EE':'estonia','LV':'latvia','LT':'lithuania','PL':'poland'}
ROOT=Path('docs/cge36-d2-2026')
S=requests.Session();S.headers.update({'User-Agent':'MMD31/1.0 (educational club logo verification)'})
def norm(s):
 s=unicodedata.normalize('NFKD',s.casefold())
 return re.sub('[^a-z0-9]','', ''.join(c for c in s if not unicodedata.combining(c)))
def get(url):
 r=S.get(url,timeout=12);r.raise_for_status()
 if len(r.content)>5000000 or len(r.content)<200:raise ValueError('Image size invalid')
 b=r.content
 if b'<svg' in b[:2000] or url.split('?')[0].lower().endswith('.svg'):
  b=cairosvg.svg2png(bytestring=b,output_width=512)
 image=Image.open(io.BytesIO(b)).convert('RGBA')
 if min(image.size)<34:raise ValueError('small image')
 box=image.getchannel('A').getbbox()
 if not box:raise ValueError('transparent')
 return image.crop(box)
def palette(im):
 copy=im.copy();copy.thumbnail((54,54))
 colors=[]
 for r,g,b,a in copy.getdata():
  if a>190 and max(r,g,b)-min(r,g,b)>40:colors.append((r,g,b))
 if not colors:return (201,213,228)
 from collections import Counter
 winner=Counter(tuple(x//40 for x in p) for p in colors).most_common(1)[0][0]
 return tuple(min(245,int(.56*(c*40+20)+.44*245)) for c in winner)
def find_logo(country,name,filename):
 if filename.endswith('.svg'):
  url='https://raw.githubusercontent.com/JoseArroyave/football-logos/main/logos/'+COUNTRY[country]+'/'+quote(filename)
  return get(url),url,'josearroyave-authentic-club-svg'
 # First, independent team-name API; only accept precise club identity
 names=[name]
 names.extend([name.replace('FK ','').replace('FC ','').replace('JK ','').replace('SC ','')])
 if name=='Tartu JK Welco':names.append('Tartu Welco')
 for n in names[:3]:
  try:
   data=S.get('https://www.thesportsdb.com/api/v1/json/3/searchteams.php',params={'t':n},timeout=10).json()
   for item in data.get('teams') or []:
    nm=item.get('strTeam') or ''
    cand=norm(nm)
    if cand!=norm(n) and cand!=norm(filename) and not (len(norm(filename))>=7 and norm(filename) in cand):
     continue
    if item.get('strSport') and 'Soccer' not in item['strSport']:continue
    badge=item.get('strBadge') or item.get('strTeamBadge')
    if badge: return get(badge),badge,'thesportsdb-name-verified'
  except Exception:pass
 # Wikimedia Commons: must have filename explicitly combining football club and exact name.
 aliases={'Welco':['Welco.png'],'Viimsi':['Viimsi JK.svg','Viimsi JK.png'],
 'Elva':['FC Elva logo.png'],'Maardu':['Maardu Linnameeskond logo.png']}
 for file in aliases.get(filename,[]):
  try:
   q=S.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','titles':'File:'+file,'prop':'imageinfo','iiprop':'url','format':'json'},timeout=10).json()
   for page in (q.get('query') or {}).get('pages',{}).values():
    for ii in page.get('imageinfo',[]):
     url=ii.get('url')
     if url:return get(url),url,'wikimedia-exact-identified-filename'
  except Exception:pass
 # Official football-association/club tables provide real crests with club-labelled image alt text.
 # Match strict team/alias name; do not accept a league logo or player photograph.
 sites={'EE':['https://jalgpall.ee/voistlused/53/esiliiga'],
        'LV':['https://leevonppk.com/','https://marupesfutbols.lv/'],
        'LT':['https://www.fkbabrungas.lt/','https://lietuvosfutbolas.lt/varzybos/vyru/i-lyga/']}
 target=norm(filename)
 allowed=[norm(name),target]
 for webpage in sites.get(country,[]):
  try:
   html=S.get(webpage,timeout=20).text
   soup=BeautifulSoup(html,'html.parser')
   for tag in soup.find_all('img'):
    alt=(tag.get('alt') or '').strip()
    val=norm(alt)
    if not alt or val not in allowed and val not in [target+'logo','logo'+target]:
     continue
    raw=tag.get('data-src') or tag.get('src') or tag.get('data-lazy-src') or ''
    if not raw or raw.startswith('data:'):continue
    url=urljoin(webpage,raw)
    try:
     img=get(url)
     if img.width/img.height>1.6 or img.height/img.width>1.6:continue
     return img,url,'official-club-or-federation-table-strict-image-alt'
    except Exception:continue
  except Exception:pass

 # Verified named assets visible in football club crest catalogues or team services.
 known={
   'Mārupes SC':'https://images.seeklogo.com/logo-png/38/1/mrupe-sc-logo-png_seeklogo-384577.png',
   'JFK Ventspils':'https://r2.thesportsdb.com/images/media/team/badge/ow928b1734112963.png',
   'Vilniaus BFA':'https://www.statarea.com/images/teams/embl/21416.png',
   'FK Garliava':'https://images.seeklogo.com/logo-png/52/1/fk-garliava-logo-png_seeklogo-520848.png',
 }
 if name in known:
  u=known[name]
  try:return get(u),u,'exact-club-identified-independent-badge'
  except Exception as e: print('Known image could not be retrieved:',name,str(e)[:130],flush=True)
 if name=='Riga Mariners':
  # Own official Riga Mariners website; only its navigation/header logo.
  for site in ['https://rigamariners.lv/','https://rigamariners.lv/par-mums/']:
   try:
    soup=BeautifulSoup(S.get(site,timeout=24).text,'html.parser')
    candidates=[]
    for img in soup.find_all('img'):
     parent=img.find_parent(['header','nav'])
     alt=img.get('alt') or ''
     classes=' '.join(img.get('class') or [])
     src=img.get('data-src') or img.get('src') or ''
     if (parent or 'custom-logo' in classes or norm(alt)==norm(name)) and src and not src.startswith('data:'):
      candidates.append((src,alt,classes))
    for src,alt,cls in candidates:
     url=urljoin(site,src)
     try:
      im=get(url)
      if 0.55<=im.width/im.height<=1.8:
       return im,url,'club-official-website-header-logo'
     except Exception: pass
   except Exception as e:print('Riga official website lookup',str(e)[:120],flush=True)

 if name=='Riga Mariners':
  # Identified Latvian first-league team 519903 (FK Beitar/Riga Mariners alias) on Sofascore.
  # Accept only real logo pixels; do not screenshot a match or invent a crest.
  for logo_url in ['https://img.sofascore.com/api/v1/team/519903/image',
                   'https://www.sofascore.com/api/v1/team/519903/image']:
   try:
    img=get(logo_url)
    if .55<=img.width/img.height<=1.85:
     return img,logo_url,'sofascore-team-519903-club-crest-identity-verified'
   except Exception as e:print('Riga Mariners crest unavailable:',str(e)[:120],flush=True)
 raise ValueError('No securely identified real club logo; do not publish placeholder')
manifest=[]
for cc,groups in CLUBS.items():
 for i,(name,filename) in enumerate(groups,1):
  uid=1897600000000+{'EE':5000,'LV':6000,'LT':7000,'PL':8000}[cc]+i
  item={'country':cc,'teamId':uid,'club':name,'expected_size':[120,96],'state':'missing'}
  try:
   img,url,source=find_logo(cc,name,filename)
   bg=palette(img)
   output=Image.new('RGBA',(120,96),bg+(255,))
   img.thumbnail((96,82),Image.Resampling.LANCZOS)
   output.alpha_composite(img,((120-img.width)//2,(96-img.height)//2))
   path=ROOT/'clubs'/cc/(str(uid)+'.png')
   path.parent.mkdir(parents=True,exist_ok=True)
   output.save(path,'PNG',optimize=True)
   assert Image.open(path).size==(120,96)
   item.update({'state':'published','source':url,'source_type':source,'path':path.as_posix(),'background_rgb':list(bg),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
  except Exception as e: item['problem']=str(e)[:230]
  manifest.append(item)
  print(cc,i,name,item['state'],flush=True)
ROOT.mkdir(exist_ok=True,parents=True)
(ROOT/'manifest.json').write_text(json.dumps({'expected':58,'published':sum(x['state']=='published' for x in manifest),'missing':sum(x['state']!='published' for x in manifest),'clubs':manifest},ensure_ascii=False,indent=2)+'\n')
print('TOTAL',sum(x['state']=='published' for x in manifest),'/',len(manifest),flush=True)
